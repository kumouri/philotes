"""User-facing wording that the spec constrains, kept in one place so tests can pin it.

``AVOIDS_HONOURED`` is required by §12 Phase 1 and §7.6 (ruled 2026-10-06, §14 #15): wherever a
player can set an avoid, the product says plainly that avoids are honoured, so a person who watches
who they get matched with may partly work out that someone avoided them. It must never claim avoids
are undetectable. It appears on every post-seed card, in ``/help``, in the reply to setting an
avoid or block, and in docs/user-guide.md.
"""

from __future__ import annotations

AVOIDS_HONOURED = (
    "**Avoids are honoured.** If you avoid or block someone, the matcher keeps you apart. That "
    "means someone who pays close attention to who they get matched with may be able to partly "
    "work out that a person avoided them. Avoids are private, but they are not undetectable. If "
    "you need certainty, use **block**, or **report** if someone broke the rules."
)

JOIN = (
    "Philotes forms Archipelago multiworld seeds from whoever signs up each week, and remembers "
    "who you liked playing with so you can end up together again. To join, confirm that you are "
    "18 or older: `/join adult:true`.\n\n"
    "What we keep: your Discord user ID, your sign-ups, the style and interests you set, the "
    "marks you set on people you played with, who you've been in seeds with, any reports, "
    "and submitted player YAMLs and generated Archipelago files when automation is enabled. "
    "Nobody can see your marks, including the people they're about. `/mydata` shows all of it "
    "and `/leave` deletes it."
)

HELP = (
    "**Philotes** (closed alpha)\n"
    "`/join` — opt in (18+).\n"
    "`/style` — voice/text, chatty/heads-down, sweaty/chill. Optional.\n"
    "`/interests` — a few tags, used as tiebreakers. Optional.\n"
    "`/signup` — sign up for this week's seeds: goal lengths you're up for and seed sizes.\n"
    "`/withdraw` — take your sign-up back.\n"
    "`/status` — your sign-up, and your seeds.\n"
    "`/yaml seed:<number> file:<attachment>` — submit a player YAML when automation is enabled.\n"
    "`/recent` — people you've played with lately, to mark **more**, **avoid**, **block** or "
    "**report**.\n"
    "`/forget` — clear a mark you set (frees a block slot).\n"
    "`/report` — report someone you played with to this community's moderators.\n"
    "`/mydata` — everything we hold about you. `/leave` — delete it all.\n\n"
    "Seeds form once a week, when the sign-up window closes. You only hear from the bot when "
    "your seed forms and when it ends by DM. YAML reminders and room details stay in the seed "
    "channel.\n\n" + AVOIDS_HONOURED
)

CARD_HEADER = (
    "Your seed **#{seed}** ({goal}) has ended. Here's who you played with. For each person you "
    "can choose **more** (match us again), **neutral** (the default — ignoring this is fine), "
    "**avoid** (rather not; fades over a few weeks), **block** (never; you have {cap} slots), or "
    "**report** (goes to this community's moderators and also blocks them). Nobody is told what "
    "you chose. You can change it with `/recent` for {days} days.\n\n" + AVOIDS_HONOURED
)

SEED_FORMED_DM = (
    "Your seed **#{seed}** has formed: {goal} goal, {n} players. Your private channel is {where}."
)

SEED_CHANNEL_WELCOME = (
    "Welcome to seed **#{seed}** ({goal} goal, about {days} days): {mentions}.\n"
    "Share your Archipelago YAMLs here and pick one person to generate and host the seed. When "
    "the seed ends, the bot will DM each of you a short card about who you played with."
)

SIGNED_UP = (
    "You're signed up for this week: {goals}, seed size {pref} (or {acc} if that's what it "
    "takes). Seeds form when the window closes ({closes}). You'll get a DM only when your seed "
    "forms. If none forms for you this week, your sign-up carries over to next week."
)
