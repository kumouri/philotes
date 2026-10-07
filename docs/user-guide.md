# Philotes: a guide for players

Philotes is a Discord bot that forms Archipelago multiworld seeds from whoever signs up each week.
After a seed, you can tell it who you liked playing with, and it tries to put you together again
the next time you both sign up. You never browse or pick people. You only react to people you
have already played with.

It is in a closed alpha, in one community, for adults (18+) only.

## Joining and signing up

- `/join adult:true` opts you in. You need a Discord account that is at least 30 days old.
- `/signup goals:short,medium size:4-6 accept:3-8` signs you up for this week. **Goals** are the
  seed lengths you're up for, your first choice first: short (about a week), medium (two weeks)
  and long (four weeks). **Size** is how many players you'd like. **Accept** is the range you'll
  take if that's what it takes to place you.
- `/style` (voice or text, chatty or heads-down, sweaty or chill) and `/interests` are optional.
  They help the matcher put compatible people together.
- `/withdraw` takes your sign-up back. `/status` shows your sign-up and your seeds.

Seeds form once a week, when the sign-up window closes. If yours forms, you get a DM and a private
channel with the other players. Share your YAMLs there and pick someone to generate and host the
seed. If no seed forms for you that week, your sign-up carries over to the next one automatically
and keeps its place in the queue.

The bot never tells you who else is signed up, how many people are, or who is online.

## After a seed: more, avoid, block, report

When your seed ends, the bot DMs you a card with each person you played with. For each person you
can choose:

- **more**: match us again. The matcher tries to put you in the same seed next time you both sign
  up.
- **neutral**: the default. Ignoring the card is fine.
- **avoid**: you'd rather not. The matcher keeps you apart. This fades over a few weeks.
- **block**: never. The matcher will never put you together. You have 10 blocks; `/forget`
  frees one.
- **report**: for when someone broke the rules. It goes to this community's moderators and also
  blocks them, outside the 10-block limit.

You can change your choice with `/recent` for 14 days after the seed ends. Nobody is ever told
what you chose, including the person it's about. You'll never be told that someone marked you
**more** too.

**Avoids are honoured.** If you avoid or block someone, the matcher keeps you apart. That means
someone who pays close attention to who they get matched with may be able to partly work out
that a person avoided them. Avoids are private, but they are not undetectable. If you need
certainty, use **block**, or **report** if someone broke the rules.

## Your data

Philotes keeps your Discord user ID, your sign-ups, the style and interests you set, the marks you
set, who you've been in seeds with, and any reports. It never reads your messages, voice, presence
or real name.

- `/mydata` shows everything it holds about you.
- `/leave confirm:true` deletes all of it, including every mark anyone set about you. Reports go
  to the moderators and stay with them.
- Avoids are deleted once they have faded. Records of who played with whom are deleted after a
  year.

## Notifications

The bot only messages you for two things: when your seed forms, and the card when it ends. There
are no reminders or nudges.
