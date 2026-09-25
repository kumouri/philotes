# Spec: group matchmaking for multiplayer games (working name)

| | |
|---|---|
| **Status** | **Specced, unbuilt.** No code, users or hosting yet. |
| **Spec version** | v0.1, 2026-09-24 (first draft) |
| **Owner / decider** | Ceryce |
| **Canonical source** | This file. Other formats are rendered from it. |
| **Product name** | Undecided. `multiplayer-matchmaking` is only the working folder name ([§14](#14-open-questions)). |

How to read this spec: **Rulings** (§4) are Ceryce's decisions and hold unless she changes them.
Anything marked **Proposed** is a design idea from the conversation that started this project. Most
of those came from Margo. They are recommendations and nothing more. Each one has a **lean**, and
the decision stays with Ceryce. Where a problem is still unsolved, the spec says so.

---

## 1. The ask

> "Start speccing it rofl might as well build it and put it out there, if no one uses it, no one
> uses it, if people do, awesome, no matter what, it's a contribution of ours to the world."

This is an open project that we build, publish and let the world use or ignore. The spec makes no
growth assumptions, and the success test is modest:

- A small community uses it, and some people end up with a regular group they would not otherwise
  have found.
- Some of those groups move to their own Discord server or group chat. **That counts as success**
  (Ruling 5).

## 2. Problem

Adult friendship mostly comes from repeated, low-stakes time with the same people. Hall (2018)
estimated about **50 hours** together to go from acquaintance to casual friend, about **90** to
friend, and **200+** to close friend. "Playing video games" is explicitly in the kind of time he
counted ([KU News](https://news.ku.edu/news/article/2018/03/06/study-reveals-number-hours-it-takes-make-friend);
[paper](https://journals.sagepub.com/doi/10.1177/0265407518761225)).

Multiplayer games already produce hours like that. The tools for finding people to play with throw
the repetition away:

- **Automated matchmaking** (quick play, duty finders) puts you with strangers and forgets them
  afterwards. You get hours of play, but every hour is with someone new.
- **LFG posts and boards** match you once for one session. Turning that into a regular group takes
  deliberate social effort from someone: friend requests, DMs, scheduling. Many people, including
  the shy, the busy and neurodivergent players, never make that move.
- **Friend-finder apps** start from profiles and personality quizzes. They are a dating-app shape
  applied to friendship, and they make you pick people before you have played with them.

What actually works is the thing Discord communities stumble into by accident. A small group that
already plays together needs one or two more people. A stranger fills the gap, gets on with them,
keeps showing up and becomes part of the group. Ceryce put it this way (Ruling 2): *"You don't make
friends from LFG, you make friends from groups looking for one or two people, and then you happen
to hit it off with that group and join it."*

**This product automates that accident.** The matcher fills groups from whoever is queued now. It
remembers who you liked playing with and quietly puts you together again the next time you are both
online, without anyone having to schedule it.

## 3. Non-goals

These are out of scope by design. They are not simply deferred.

- **No friends list or social graph UI.** At most there is a short, expiring "recently played
  with" list (Ruling 6).
- **No profile browsing, swiping, searching for people, or "people you may like".** You never pick
  people. You only react to people you have already played with.
- **Not a dating app,** and not a "dating app for friends" (Ruling 1).
- **No pre-scheduled or fixed groups.** Groups are emergent clusters, not memberships (Rulings 2
  and 4). A group that becomes stable and moves off-platform has graduated. It has not churned.
- **No competitive or skill-rating matchmaker.** Skill appears only as a soft self-described style
  field such as "sweaty / chill". We don't compute or show MMR.
- **No chat, voice or messaging of our own.** Discord and in-game tools already handle that. We
  form the group and hand off.
- **No engagement maximising.** The matcher's objective is good sessions and relationships forming,
  not time-in-app. EOMM-style engagement-optimised matchmaking
  ([Chen et al., 2017](https://arxiv.org/pdf/1702.06820)) is the reference point we avoid.

## 4. Rulings

These are Ceryce's decisions, quoted verbatim. The rest of the spec has to agree with them.

**R1. Any game, group-shaped, preference-weighted.**
> "it wouldn't be so much a dating app for friends as it would be a matchmaking service for
> multiplayer in ANY game. You pick the games you're down for playing and how many people you want,
> and then it matches groups up. Even better if you've got info on other interests or like
> communications style or whatever else and we can match you with preference."

The engine is game-agnostic. The inputs are games, desired group size and optional
interest/communication preferences.

**R2. Friendships come from rematching, not from LFG.**
> "You don't make friends from LFG, you make friends from groups looking for one or two people, and
> then you happen to hit it off with that group and join it. The real feature would be 'I like
> playing with this person, match me with them more often', then you don't have to both be playing
> at that time next Thursday, the next time you're both playing it can try matching you back
> together."

The core feature is the **"match me with them more often"** signal, applied opportunistically when
both people happen to be queued. It needs no scheduling.

**R3. Density is the hard problem.**
> "the hard problem is density … nothing we made would have enough density out the gate"

This is accepted as the primary risk. It shapes the launch strategy (§9) and Phase 0 (§12).

**R4. Avoidance after matchmaking replaces leaving a group.**
> "It also completely avoids the 'A likes B, B dislikes A, how does B get out of the group cleanly,
> especially if they like C, D, and E?' If it was pre-scheduled groups they'd be stuck, this way
> they just say they dislike A after matchmaking and matchmaker does its best to avoid matching them
> together."

Because there is no group membership, there is nothing to leave. Relationships are pairwise edges,
and a negative edge quietly steers the matcher without breaking up the cluster.

**R5. Known problems are accepted as real, and a group moving off-platform is success.**
Ceryce named three problems as real: **silent rejection becoming noticeable**, **rich-get-richer**
(well-liked players cluster, and frequently-avoided players end up matched only with each other),
and **weaponized avoidance**.
> "I assume frozen groups would just move off-platform"

A group that moves to its own Discord is the product working. It is not a retention failure.

**R6. No friends lists.**
> "I wasn't planning on ever having anything like friends lists or anything like that, at MOST it
> would be like 'recently played with'."

**R7. Anchors.**
> "Ooo anchors is a good one."

Anchors are players who opt in to being matched with newcomers and strangers. They are in scope as
a mechanism (§7.4), with details still open.

**R8. Weaponized avoidance is limited by arithmetic, and the arithmetic is local.**
> "if ENOUGH users of a community avoided a player … it would be impossible to make a lobby their
> requested size … without including one of the players who put the member on avoid."
>
> "that would require a huge proportion of a community avoid one player"

Counterpoint recorded in the same conversation (Margo): the denominator that matters is **who is
queued for that game right now**, not the whole community. With 8 queued and a lobby of 5, four
online avoiders lock one player out. So this bites off-peak and in niche games. §8 does the
arithmetic, and the Phase 0 simulator (§12) measures it.

## 5. Prior art

Researched 2026-09-24. Each tool below is judged against **R1**: any game, group-shaped, filled
automatically from who is available, preference-weighted. It is also judged against **R2**: a
"match me with them more often" signal applied opportunistically, with no scheduling.

| Prior art | What it does | Where it falls short of R1–R2 |
|---|---|---|
| **GameTree** ([site](https://gametree.me/), [App Store](https://apps.apple.com/us/app/gametree/id1181404496), [Scout Discord bot](https://gametree.me/discord-lfg-bot/)) | Friend-finder built on profiles, owned games, platform and personality/values quizzes (Myers-Briggs-style). Its Discord bot advertises personality matching to "build lasting squads" and "permanent gaming rosters" ([TheGamer](https://www.thegamer.com/gametree-gamer-friend-finding-app-facts-information/)). | This is the "dating app for friends" shape that R1 rejects: you pick people from profiles before playing with them. "Permanent rosters" are the frozen groups R4 avoids. We found no rematch-when-both-online mechanism. Its personality signal is a quiz, whereas ours comes from actual play. |
| **GamerLink, PLINK, Z League LFG** ([GamerLink](https://gamerlinkapp.com/), [roundup](https://www.zleague.gg/theportal/top-5-looking-for-group-lfg-apps/)) | LFG apps across 250–300+ games. PLINK uses a Tinder-like swipe UI with voice. Z League matches on submitted preferences. | They cover many games, so they meet the "any game" part of R1. But they are one-shot: you post or swipe, play once and start over. Nothing weights a repeat pairing (R2), and swipe UIs are the profile-browsing we list as a non-goal. |
| **Discord LFG bots**: LFG Hub, Teamplay, LFG Bot, OSS `looking-for-group` ([LFG Hub](https://lfghub.gg/), [Teamplay](https://teamplay.gg/discord-lfg-bot), [LFG Bot](https://lfg-bot.com/), [GitHub](https://github.com/NickDelfino/looking-for-group), [top.gg tag](https://top.gg/tag/lfg)) | A player posts a group ("need 2 for X"), others click to join, and the bot creates a temporary voice channel, sends pings and supports scheduling. LFG Hub runs a cross-server "LFG Network" to pool players. | These are the right venue: they sit where the communities are and hand off to voice cleanly. But humans still form every group, one post at a time. None of them remembers who you enjoyed playing with or quietly reunites you, and none has pairwise avoidance. Scheduling features push toward the pre-scheduled groups R4 rules out. Density is per server unless networked. |
| **Overwatch 2 "Avoid as Teammate"** ([Dexerto](https://www.dexerto.com/overwatch/new-overwatch-2-avoid-slot-system-explained-2867330/), [esports.gg](https://esports.gg/news/overwatch/overwatch-2-finally-lets-you-avoid-15-teammates/), [wiki](https://overwatch.fandom.com/wiki/Avoid_as_Teammate)) | 15 avoid slots: 3 pinned permanently, 12 that expire after 7 days, with the oldest evicted when full. Avoid means *deprioritised*, not guaranteed. Avoided players can still be matched in small pools such as top ranks, low-population regions and off-hours. | This is the strongest evidence for the proposed **hard/soft split with decay** (§7.2). A large shipped game landed on almost the same design and was open about small pools breaking it. However, it only covers avoidance. There is no positive "more of this person" signal, it works in one game, and it is tuned for fair competitive teams rather than relationships. |
| **Dota 2 avoid list** ([Eloking](https://eloking.com/blog/how-to-use-dota-2-avoid-list), [win.gg](https://win.gg/news/dota-2-avoid-player-feature-improved-as-long-as-fans-pay-up/)) | Paid (Dota Plus). 25 slots, more can be bought with shards, and old entries are evicted silently. Avoid is a preference, not a hard block. | The stated reason for the cap is directly relevant to **R8**: without it, small-pool players could "avoid all other mid players at [their] MMR" to game the matcher. So weaponized avoidance in thin pools is a known, shipped problem. Like Overwatch, Dota has no positive signal and is single-game. |
| **Destiny 2 Fireteam Finder; FFXIV Party Finder vs Duty Finder** ([Bungie Help](https://help.bungie.net/hc/en-us/articles/25787853699220-Fireteam-Finder-Guide), [FFXIV wiki](https://ffxiv.consolegameswiki.com/wiki/Duty_Finder)) | Official in-game LFG. Destiny supports listings with tags (including communication tags), play-now or scheduled. FFXIV splits an automated queue (Duty Finder: fast, random, cross-server) from manual listings (Party Finder). | FFXIV's split shows the gap clearly. Players describe Party Finder as the place for "playing with people you can actually friend afterwards" and Duty Finder as quick and anonymous. **This project tries to merge the two:** automated like Duty Finder, with memory like Party Finder. Both are single-game. |
| **Steam "Recently Played With"** ([Steam community](https://steamcommunity.com/discussions/forum/7/2828702373008810755/)) | A passive list of recent co-players in supported games, from which you can send friend requests. | This is the ceiling R6 allows us, and all it does is surface names. Getting to play together again still needs a friend request plus explicit coordination, which is the social effort R2 is meant to remove. |
| **Microsoft patent US 7,677,970**, "System and method for social matching of game players on-line" (filed 2004-12-08, granted 2010-03-16) ([Google Patents](https://patents.google.com/patent/US7677970B2/en)) | Post-game feedback records "whether or not you would want to play with this game player in future games". Positive feedback raises a player in an "Affiliates" priority list (Friends > positive-feedback players > recent players). Negative feedback adds them to an Avoid list. | This is the **closest conceptual prior art to R2**, so we should not claim the core idea is new. The version we aim for is cross-game, has no friends tier (R6), is open source, and treats avoidance as a soft, decaying, avoider-local signal. **Patent status:** US utility patents generally run 20 years from filing, so this has *probably* lapsed. That is not legal advice, and it should be checked before launch ([§14](#14-open-questions)). |

**Summary.** Every piece exists somewhere. There are cross-game LFG tools, avoid lists with
hard/soft tiers and decay, and a 2004 design for "play with again" feedback. What we could not find
shipped anywhere is the combination. Based on this search, no product today forms groups
automatically from who is available across any game, uses a "match me with them more often" signal
to reunite people opportunistically, and deliberately avoids friends lists, profiles and fixed
groups. The idea itself is not what's new. Our contribution would be the combination and the open
implementation.
