"""The slash-command surface, declared once for every transport.

Each ``Command`` names a ``Bot`` method and its options. The local console parses typed lines with
it, and the Discord adapter registers the same list as application commands, so
the two cannot drift. Option names are the method's parameter names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .core import Bot, Invocation, Reply

STR, INT, BOOL, USER = "str", "int", "bool", "user"
ATTACHMENT = "attachment"


@dataclass(frozen=True)
class Option:
    name: str
    kind: str
    description: str
    required: bool = False
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Command:
    name: str  # "signup", or "mod remove" for a subcommand of /mod
    method: str
    description: str
    options: tuple[Option, ...] = ()


_STYLE = {
    "comms": ("voice", "text", "either"),
    "talk": ("chatty", "heads-down", "either"),
    "intensity": ("sweaty", "chill", "either"),
}

COMMANDS: tuple[Command, ...] = (
    Command("help", "help", "What Philotes does and how to use it"),
    Command(
        "join",
        "join",
        "Opt in to Philotes (18+)",
        (Option("adult", BOOL, "I confirm I am 18 or older", required=True),),
    ),
    Command(
        "style",
        "style",
        "How you like to play (optional)",
        tuple(Option(a, STR, f"{a}: {' / '.join(c)}", choices=c) for a, c in _STYLE.items()),
    ),
    Command(
        "interests",
        "interests",
        "Up to 5 interest tags, comma-separated (optional; blank clears)",
        (Option("tags", STR, "e.g. zelda, metroidvania, speedrun"),),
    ),
    Command(
        "signup",
        "signup",
        "Sign up for this week's Archipelago seeds",
        (
            Option("goals", STR, "Goal lengths, first choice first: short,medium,long", True),
            Option("size", STR, "Preferred seed size, e.g. 4-6"),
            Option("accept", STR, "Sizes you'd accept if needed, e.g. 3-8"),
        ),
    ),
    Command("withdraw", "withdraw", "Take back this week's sign-up"),
    Command("status", "status", "Your sign-up and your seeds"),
    Command(
        "yaml",
        "submit_yaml",
        "Submit or replace your Archipelago player YAML",
        (
            Option("seed", INT, "Seed number", True),
            Option("file", ATTACHMENT, "Your .yaml or .yml file (max 64 KiB by default)", True),
        ),
    ),
    Command("recent", "recent", "People you've played with lately, to mark"),
    Command(
        "forget",
        "forget",
        "Clear a mark you set on someone",
        (Option("user", USER, "Who", required=True),),
    ),
    Command(
        "report",
        "report",
        "Report someone you played with to the moderators",
        (
            Option("user", USER, "Who", required=True),
            Option("reason", STR, "What happened", required=True),
        ),
    ),
    Command("mydata", "mydata", "Everything Philotes holds about you"),
    Command(
        "leave",
        "leave",
        "Delete everything Philotes holds about you",
        (Option("confirm", BOOL, "Yes, delete it all"),),
    ),
    Command(
        "mod remove",
        "mod_remove",
        "Take a player out of matching",
        (Option("user", USER, "Who", required=True), Option("reason", STR, "Why")),
    ),
    Command(
        "mod restore",
        "mod_restore",
        "Let a removed player sign up again",
        (Option("user", USER, "Who", required=True),),
    ),
    Command("mod reports", "mod_reports", "List open reports"),
    Command(
        "mod resolve",
        "mod_resolve",
        "Mark a report handled",
        (
            Option("report", INT, "Report number", required=True),
            Option("note", STR, "Note"),
            Option(
                "outcome", STR, "Review outcome", choices=("open", "resolved", "abusive", "false")
            ),
        ),
    ),
    Command(
        "mod history",
        "mod_history",
        "Retained reports filed and received",
        (Option("user", USER, "Who", True), Option("page", INT, "Page (10 reports)")),
    ),
    Command(
        "mod audit",
        "mod_audit",
        "Moderator action log",
        (Option("page", INT, "Page (10 actions)"),),
    ),
    Command("mod close-window", "mod_close_window", "Close this week's window and form seeds now"),
)

BY_NAME = {c.name: c for c in COMMANDS}


class UsageError(ValueError):
    pass


def convert(opt: Option, raw: str) -> object:
    if opt.kind == ATTACHMENT:
        raise UsageError(
            "Submit /yaml with a Discord file attachment; console does not read files."
        )
    if opt.kind == STR:
        if opt.choices and raw not in opt.choices:
            raise UsageError(f"{opt.name} must be one of: {', '.join(opt.choices)}")
        return raw
    if opt.kind == BOOL:
        if raw.lower() not in {"true", "false", "yes", "no", "1", "0"}:
            raise UsageError(f"{opt.name} must be true or false")
        return raw.lower() in {"true", "yes", "1"}
    m = re.fullmatch(r"<@!?(\d+)>|(\d+)", raw.strip())
    if m is None:
        raise UsageError(f"{opt.name} must be a {'user' if opt.kind == USER else 'number'}")
    return int(m.group(1) or m.group(2))


def dispatch(bot: Bot, inv: Invocation, name: str, args: dict[str, str]) -> Reply:
    """Run command ``name`` with raw string ``args``. Raises ``UsageError`` on bad input."""
    cmd = BY_NAME.get(name)
    if cmd is None:
        raise UsageError(f"unknown command /{name}")
    known = {o.name: o for o in cmd.options}
    unknown = set(args) - set(known)
    if unknown:
        raise UsageError(f"/{name} has no option {', '.join(sorted(unknown))}")
    kw = {}
    for o in cmd.options:
        if o.name in args:
            kw[o.name] = convert(o, args[o.name])
        elif o.required:
            raise UsageError(f"/{name} needs {o.name}")
    return getattr(bot, cmd.method)(inv, **kw)
