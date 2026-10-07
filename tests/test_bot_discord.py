import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from philotes_bot.cli import main
from philotes_bot.commands import COMMANDS
from philotes_bot.discord_adapter import Adapter, CardButton, DiscordClient, message_kwargs
from philotes_bot.transport import Message
from tests.test_bot_core import join_and_sign, to_close, world


@pytest.fixture(scope="session")
def loop():
    # Windows initializes an internal loopback wakeup pipe before the network guard.
    event_loop = asyncio.new_event_loop()
    yield event_loop
    event_loop.close()


def interaction(user=1, guild=77, roles=()):
    return SimpleNamespace(
        user=SimpleNamespace(id=user, roles=[SimpleNamespace(id=r) for r in roles]),
        guild_id=guild,
        response=SimpleNamespace(defer=AsyncMock(), send_modal=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )


def test_commands_buttons_and_modal(loop):
    async def scenario():
        w = world()

        async def call(method, *args):
            return method(w.bot, *args) if callable(method) else getattr(w.bot, method)(*args)

        adapter = Adapter(w.bot.cfg, call)
        i = interaction()
        await adapter.command(i, "join", {"adult": True})
        assert w.store.player(1)
        assert i.followup.send.call_args.kwargs["ephemeral"]
        join_and_sign(w, range(1, 5))
        to_close(w)
        assert all(len(w.t.dms_to(u)) == 1 for u in range(1, 5))
        sid = w.store.seeds()[0].id
        for action in ("more", "avoid", "block", "neutral"):
            await adapter.button(interaction(guild=None), f"ph:{action}:{sid}:2")
        assert w.store.edge(1, 2) is None
        i = interaction(guild=None)
        await adapter.button(i, f"ph:report:{sid}:2")
        modal = i.response.send_modal.call_args.args[0]
        modal.reason._value = "Repeated harassment"
        await modal.on_submit(interaction(guild=None))
        assert len(w.store.reports()) == 1 and len(w.t.mod_posts) == 1
        assert w.store.edge(1, 2).via_report
        w.store.close()

    loop.run_until_complete(scenario())


def test_moderator_role_refusal_and_acceptance(loop):
    async def scenario():
        w = world()
        cfg = replace(w.bot.cfg, community=replace(w.bot.cfg.community, mod_role_id=99))

        async def call(method, *args):
            return method(w.bot, *args)

        adapter = Adapter(cfg, call)
        for guild, roles, allowed in [
            (77, (), False),
            (78, (99,), False),
            (None, (99,), False),
            (77, (99,), True),
        ]:
            i = interaction(guild=guild, roles=roles)
            await adapter.command(i, "mod reports", {})
            content = i.followup.send.call_args.kwargs["content"]
            assert (content == "No open reports.") == allowed
        w.store.close()

    loop.run_until_complete(scenario())


def test_registration_and_restart_buttons(loop):
    async def scenario():
        w = world()
        client = DiscordClient(w.bot.cfg)
        guild = discord.Object(id=77)
        registered = client.tree.get_commands(guild=guild)
        names = {f"mod {c.name}" for c in next(c for c in registered if c.name == "mod").commands}
        names |= {c.name for c in registered if c.name != "mod"}
        assert names == {c.name for c in COMMANDS}
        calls = []

        async def call(method, *args):
            calls.append(args[1])
            return method(w.bot, *args)

        client.adapter.call = call
        await client.tree.get_command("join", guild=guild).callback(interaction(), adult=True)
        await client.tree.get_command("help", guild=guild).callback(interaction())
        assert calls == ["join", "help"]  # each callback retains its own declaration
        assert w.store.player(1)
        for c in registered:
            for leaf in c.commands if isinstance(c, discord.app_commands.Group) else [c]:
                spec = next(s for s in COMMANDS if s.name == leaf.qualified_name)
                assert [(p.name, p.required) for p in leaf.parameters] == [
                    (o.name, o.required) for o in spec.options
                ]
        assert (
            not client.intents.members
            and not client.intents.presences
            and not client.intents.message_content
        )
        button = await CardButton.from_custom_id(
            None, discord.ui.Button(custom_id="ph:more:1:2", label="more"), None
        )
        assert button.item.custom_id == "ph:more:1:2"
        kwargs = message_kwargs(Message("x" * 3000))
        assert "file" in kwargs and kwargs["allowed_mentions"].to_dict() == {"parse": []}
        await client.close()
        w.store.close()

    loop.run_until_complete(scenario())


def test_missing_token_never_constructs_client(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DISCORD_TOKEN", "ignored-process-token")
    monkeypatch.chdir(tmp_path)
    assert main(["run"]) == 1
    assert "DISCORD_TOKEN is absent" in capsys.readouterr().out


def test_transport_private_channels_and_delivery(loop):
    from unittest.mock import MagicMock

    from philotes_bot.discord_adapter import DiscordTransport

    async def scenario():
        w = world()
        # Hashable stand-ins for discord.py's role/member overwrite keys.
        everyone, bot_member, member1, member2 = range(4)
        guild = SimpleNamespace(
            id=77,
            default_role=everyone,
            me=bot_member,
            fetch_member=AsyncMock(side_effect=[member1, member2]),
            create_text_channel=AsyncMock(),
        )
        channel = SimpleNamespace(id=123, guild=guild, send=AsyncMock(), delete=AsyncMock())
        guild.create_text_channel.return_value = channel
        category = MagicMock(spec=discord.CategoryChannel)
        category.guild = guild
        user = SimpleNamespace(send=AsyncMock())
        client = SimpleNamespace(
            get_guild=lambda _: guild,
            fetch_channel=AsyncMock(return_value=category),
            fetch_user=AsyncMock(return_value=user),
        )
        transport = DiscordTransport(client, w.bot.cfg, loop)
        cid = await loop.run_in_executor(
            None, transport.create_seed_channel, "seed-1-short", [1, 2], Message("welcome")
        )
        assert cid == 123
        overwrites = guild.create_text_channel.call_args.kwargs["overwrites"]
        assert overwrites[everyone].view_channel is False
        assert set(overwrites) == {everyone, bot_member, member1, member2}
        assert all(overwrites[m].view_channel for m in [bot_member, member1, member2])
        assert guild.create_text_channel.call_args.kwargs["category"] is category
        assert await loop.run_in_executor(None, transport.send_dm, 1, Message("hand-off"))
        assert user.send.call_count == 1
        client.fetch_channel.return_value = channel
        assert await loop.run_in_executor(None, transport.post_mod, Message("report"))
        await loop.run_in_executor(None, transport.delete_channel, 123)
        channel.delete.assert_awaited_once()
        client.fetch_user.side_effect = discord.Forbidden(
            SimpleNamespace(status=403, reason="closed"), "closed"
        )
        assert not await loop.run_in_executor(None, transport.send_dm, 1, Message("closed"))
        w.store.close()

    loop.run_until_complete(scenario())
