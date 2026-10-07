"""What the bot needs from a chat platform, and an in-memory implementation of it.

The core (``core.py``) never imports a Discord library. It calls a ``Transport`` to DM a player,
create a private seed channel for its members, remove that channel, post seed updates/files,
and post into the moderators' channel. Slash-command replies are return values, not
transport calls.

``InMemoryTransport`` records every call and is what the tests and the local console use. It never
touches the network. The Discord gateway transport is in discord_adapter.py (docs/phase1-bot.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Button:
    custom_id: str
    label: str


@dataclass(frozen=True)
class Message:
    text: str
    buttons: tuple[Button, ...] = ()
    files: tuple[Path, ...] = ()


class Transport(Protocol):
    def send_dm(self, user_id: int, message: Message) -> bool:
        """DM a user. False if it could not be delivered (e.g. they have DMs from servers off)."""
        ...

    def create_seed_channel(self, name: str, member_ids: list[int], welcome: Message) -> int | None:
        """Create a private channel only ``member_ids`` (and the bot) can see; post ``welcome``."""
        ...

    def delete_channel(self, channel_id: int) -> None: ...

    def post_seed(self, channel_id: int, message: Message) -> bool: ...

    def post_mod(self, message: Message) -> bool:
        """Post to the host community's private moderators' channel (§10)."""
        ...


@dataclass
class SentDM:
    user_id: int
    message: Message


@dataclass
class Channel:
    channel_id: int
    name: str
    members: list[int]
    messages: list[Message]
    deleted: bool = False


@dataclass
class InMemoryTransport:
    """Records everything; delivers nothing. ``dm_closed`` simulates users with DMs turned off."""

    dms: list[SentDM] = field(default_factory=list)
    channels: dict[int, Channel] = field(default_factory=dict)
    mod_posts: list[Message] = field(default_factory=list)
    dm_closed: set[int] = field(default_factory=set)
    _next_channel: int = 9000

    def send_dm(self, user_id: int, message: Message) -> bool:
        if user_id in self.dm_closed:
            return False
        self.dms.append(SentDM(user_id, message))
        return True

    def create_seed_channel(self, name: str, member_ids: list[int], welcome: Message) -> int | None:
        self._next_channel += 1
        cid = self._next_channel
        self.channels[cid] = Channel(cid, name, sorted(member_ids), [welcome])
        return cid

    def delete_channel(self, channel_id: int) -> None:
        if channel_id in self.channels:
            self.channels[channel_id].deleted = True

    def post_mod(self, message: Message) -> bool:
        self.mod_posts.append(message)
        return True

    def post_seed(self, channel_id: int, message: Message) -> bool:
        channel = self.channels.get(channel_id)
        if channel is None or channel.deleted:
            return False
        channel.messages.append(message)
        return True

    def dms_to(self, user_id: int) -> list[Message]:
        return [d.message for d in self.dms if d.user_id == user_id]
