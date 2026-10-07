"""Discord translation only; the synchronous core owns all product decisions."""

import asyncio
import inspect
import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import discord
from discord import app_commands

from .commands import ATTACHMENT, BOOL, COMMANDS, INT, STR, USER, UsageError, dispatch
from .config import BotConfig
from .core import Bot, Invocation, Reply, parse_card_id
from .store import Store
from .transport import Message

log = logging.getLogger(__name__)


def message_kwargs(message):
    kwargs = {"allowed_mentions": discord.AllowedMentions.none()}
    if len(message.text) <= 2000:
        kwargs["content"] = message.text
    else:
        kwargs["file"] = discord.File(io.BytesIO(message.text.encode()), filename="philotes.txt")
    if message.buttons:
        view = discord.ui.View(timeout=None)
        for button in message.buttons:
            view.add_item(CardButton(button.custom_id, button.label))
        kwargs["view"] = view
    if message.files:
        kwargs["files"] = [discord.File(str(path)) for path in message.files]
        if "file" in kwargs:
            kwargs["files"].append(kwargs.pop("file"))
    return kwargs


class CardButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"ph:(more|neutral|avoid|block|report):\d+:\d+",
):
    def __init__(self, custom_id, label):
        super().__init__(discord.ui.Button(custom_id=custom_id, label=label))

    @classmethod
    async def from_custom_id(cls, interaction, item, match):
        return cls(item.custom_id, item.label)

    async def callback(self, interaction):
        await interaction.client.adapter.button(interaction, self.item.custom_id)


class ReportModal(discord.ui.Modal, title="Report to community moderators"):
    reason = discord.ui.TextInput(
        label="What happened?", style=discord.TextStyle.paragraph, max_length=1500
    )

    def __init__(self, adapter, custom_id):
        super().__init__()
        self.adapter = adapter
        self.card_id = custom_id

    async def on_submit(self, interaction):
        await self.adapter.card(interaction, self.card_id, str(self.reason))


class Adapter:
    def __init__(self, cfg, call):
        self.cfg = cfg
        self.call = call

    def invocation(self, interaction):
        roles = getattr(interaction.user, "roles", ())
        is_mod = interaction.guild_id == self.cfg.community.guild_id and any(
            r.id == self.cfg.community.mod_role_id for r in roles
        )
        return Invocation(interaction.user.id, interaction.guild_id, is_mod)

    async def reply(self, interaction, reply):
        for message in (Message(reply.text), *reply.follow_ups):
            await interaction.followup.send(ephemeral=True, **message_kwargs(message))

    async def command(self, interaction, name, args):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if name == "yaml":
            await self.yaml(interaction, args)
            return
        raw = {k: str(v.id if hasattr(v, "id") else v) for k, v in args.items() if v is not None}
        try:
            reply = await self.call(dispatch, self.invocation(interaction), name, raw)
        except UsageError as exc:
            reply = Reply(str(exc), ok=False)
        await self.reply(interaction, reply)

    async def yaml(self, interaction, args):
        inv, seed, attachment = self.invocation(interaction), args["seed"], args["file"]
        allowed = await self.call("yaml_permission", inv, seed)
        if not allowed.ok:
            await self.reply(interaction, allowed)
            return
        if (
            attachment.size > self.cfg.archipelago.max_yaml_bytes
            or not attachment.filename.lower().endswith((".yaml", ".yml"))
        ):
            reply = Reply("Use a .yaml or .yml file within the configured size cap.", ok=False)
        else:
            try:
                content = await attachment.read()
                reply = await self.call("submit_yaml", inv, seed, content)
            except discord.HTTPException:
                reply = Reply("Unable to read the Discord attachment. Please try again.", ok=False)
        await self.reply(interaction, reply)

    async def button(self, interaction, custom_id):
        parsed = parse_card_id(custom_id)
        if parsed and parsed[0] == "report":
            await interaction.response.send_modal(ReportModal(self, custom_id))
        else:
            await self.card(interaction, custom_id)

    async def card(self, interaction, custom_id, reason=None):
        await interaction.response.defer(ephemeral=True, thinking=True)
        reply = await self.call("card", self.invocation(interaction), custom_id, reason)
        await self.reply(interaction, reply)


def register_commands(tree, adapter, guild):
    group = app_commands.Group(name="mod", description="Community moderation")
    for command in COMMANDS:

        async def callback(interaction, _command=command, **kwargs):
            await adapter.command(interaction, _command.name, kwargs)

        types = {STR: str, BOOL: bool, INT: int, USER: discord.User, ATTACHMENT: discord.Attachment}
        params = [
            inspect.Parameter(
                "interaction",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=discord.Interaction,
            )
        ]
        for opt in command.options:
            params.append(
                inspect.Parameter(
                    opt.name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=types[opt.kind],
                    default=inspect.Parameter.empty if opt.required else None,
                )
            )
        callback.__signature__ = inspect.Signature(params)
        callback = app_commands.describe(**{o.name: o.description for o in command.options})(
            callback
        )
        choices = {
            o.name: [app_commands.Choice(name=c, value=c) for c in o.choices]
            for o in command.options
            if o.choices
        }
        callback = app_commands.choices(**choices)(callback)
        registered = app_commands.Command(
            name=command.name.split()[-1], description=command.description, callback=callback
        )
        if command.name.startswith("mod "):
            group.add_command(registered)
        else:
            tree.add_command(registered, guild=guild)
    tree.add_command(group, guild=guild)


class DiscordTransport:
    """Called only on the core worker; wait for actual Discord delivery results."""

    def __init__(self, client, cfg, loop):
        self.client, self.cfg, self.loop = client, cfg, loop

    def wait(self, coro, fallback):
        try:
            return asyncio.run_coroutine_threadsafe(coro, self.loop).result()
        except discord.HTTPException:
            log.warning("Discord delivery failed; check host permissions or closed DMs")
            return fallback

    def send_dm(self, user_id, message):
        async def send():
            user = await self.client.fetch_user(user_id)
            await user.send(**message_kwargs(message))
            return True

        return self.wait(send(), False)

    def create_seed_channel(self, name, member_ids, welcome):
        async def create():
            guild = self.client.get_guild(self.cfg.community.guild_id)
            category = await self.client.fetch_channel(self.cfg.community.seed_category_id)
            if not isinstance(category, discord.CategoryChannel) or category.guild.id != guild.id:
                raise ValueError("seed_category_id must name a category in the configured guild")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            for uid in member_ids:
                member = await guild.fetch_member(uid)
                overwrites[member] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )
            channel = await guild.create_text_channel(
                name, category=category, overwrites=overwrites
            )
            await channel.send(**message_kwargs(welcome))
            return channel.id

        return self.wait(create(), None)

    def delete_channel(self, channel_id):
        async def delete():
            channel = await self.client.fetch_channel(channel_id)
            if channel.guild.id != self.cfg.community.guild_id:
                raise ValueError("Refusing to delete a channel outside the configured guild")
            await channel.delete()

        self.wait(delete(), None)

    def post_mod(self, message):
        async def post():
            channel = await self.client.fetch_channel(self.cfg.community.mod_channel_id)
            if channel.guild.id != self.cfg.community.guild_id:
                raise ValueError("mod_channel_id must belong to the configured guild")
            await channel.send(**message_kwargs(message))
            return True

        return self.wait(post(), False)

    def post_seed(self, channel_id, message):
        async def post():
            channel = await self.client.fetch_channel(channel_id)
            if channel.guild.id != self.cfg.community.guild_id:
                raise ValueError("Seed channel must belong to the configured guild")
            await channel.send(**message_kwargs(message))
            return True

        return self.wait(post(), False)


class DiscordClient(discord.Client):
    def __init__(self, cfg):
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.cfg = cfg
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="philotes-core")
        self.tree = app_commands.CommandTree(self)
        self.adapter = Adapter(cfg, self.call)
        self.timer = None
        self.bot = None
        register_commands(self.tree, self.adapter, discord.Object(id=cfg.community.guild_id))
        self.add_dynamic_items(CardButton)

    async def call(self, method, *args):
        def invoke():
            if callable(method):
                return method(self.bot, *args)
            return getattr(self.bot, method)(*args)

        return await asyncio.get_running_loop().run_in_executor(self.worker, invoke)

    async def setup_hook(self):
        loop = asyncio.get_running_loop()

        def initialize():
            self.bot = Bot(
                self.cfg, Store(self.cfg.db_path), DiscordTransport(self, self.cfg, loop), time.time
            )

        await loop.run_in_executor(self.worker, initialize)
        await self.tree.sync(guild=discord.Object(id=self.cfg.community.guild_id))
        self.timer = asyncio.create_task(self.ticks())

    async def ticks(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.call("tick")
            except Exception:
                log.exception("Core timer failed; host intervention may be needed")
            await asyncio.sleep(60)

    async def close(self):
        if self.timer:
            self.timer.cancel()
            await asyncio.gather(self.timer, return_exceptions=True)
        if self.bot:
            await asyncio.get_running_loop().run_in_executor(self.worker, self.bot.close)
        self.worker.shutdown(wait=True)
        await super().close()


def run(cfg: BotConfig):
    if not cfg.discord_token:
        print(
            "DISCORD_TOKEN is absent. Put it in the untracked .env; see docs/SETUP.md. "
            "No connection attempted."
        )
        return 1
    if any(
        not getattr(cfg.community, key)
        for key in ("guild_id", "mod_role_id", "mod_channel_id", "seed_category_id")
    ):
        print("Configure all community IDs in philotes-bot.toml first; see docs/SETUP.md.")
        return 1
    DiscordClient(cfg).run(cfg.discord_token)
    return 0
