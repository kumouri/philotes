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

In Ceryce's words: *"We should build a dating service for friends, except they already exist and people
like me still aren't on them 😆 the most effective one so far wasn't even designed to be one, Discord."*

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

## 6. Core model

**Proposed** (Margo). Lean: adopt. It follows directly from R2, R4 and R6.

The model is **a weighted graph of people, not groups.**

- **Player**: an account. It holds the games the player is up for, the group sizes they accept per
  game, a coarse region/time zone, platform(s), optional *communication style* and *interests*, and
  an optional **anchor** flag. Nothing about a player is browsable by anyone else.
- **Edge (a → b)**: a *directed* relationship that only `a` sets, only about someone `a` has
  actually played with (from "recently played with", R6). Each edge has one of three kinds:
  - `more`: "I like playing with this person, match me with them more often" (R2).
  - `avoid-soft`: "rather not". This weight decays over time (§7.2).
  - `avoid-hard`: "never". Each player has a small capped number of these (§7.2).
  - No edge means neutral, which is the default for everyone.
- **Co-play record (a, b)**: how many sessions they have played together and when they last did.
  The system writes this, not the users. It powers "recently played with" and the diminishing
  returns in §7.3.
- **Queue entry**: *"I'm up for {games} with {size range} people for the next {window}."* This is an
  **availability window**, for example "for the next 2 hours, ping me", and not only a live
  lobby wait. Windows are what make R2's *"the next time you're both playing"* work at low density
  (§9).
- **Session**: a matcher output. It's a set of players, a game, a size, and a hand-off (a temporary
  Discord voice/text channel, or in-game handles shown only to the lobby). It is *not* a persistent
  object people belong to.
- **Group**: *there is no group object.* A "group" is simply a cluster of `more` edges whose members
  keep being co-matched. When a cluster makes its own Discord and stops queuing, that is R5's
  graduation.

**Communication-style fields** (Proposed, Margo) are a small fixed set of self-described axes, and
they are strong match signals:

| Axis | Values |
|---|---|
| Comms | voice · text · either |
| Talk | chatty · heads-down · either |
| Intensity | sweaty · chill · either |
| Optional | language(s), age band (18+ only at launch, §10), content/banter tolerance (open question) |

**Interests** (R1, "other interests") are optional free tags, matched by overlap. They get a weak
weight. Lean: interests act as tiebreakers, and comm-style carries the real weight, because a
mismatch there, such as voice-chatty against text-heads-down, ruins a session and an interest
mismatch doesn't.

## 7. Matching algorithm

### 7.1 Shape of the problem

Every **tick** (lean: 20–30 s, run per game), the matcher takes the players currently in an open
window for that game and splits some of them into lobbies. This is constrained graph clustering,
close to *clique partitioning with size bounds*. It is NP-hard in general, but pools are small: tens
to low hundreds of people per game per region. Lean approach:

1. **Hard-filter** the candidate pairs (§7.2).
2. **Seed** lobbies in priority order: longest-waiting players first, and anyone with pending
   `more` edges to others who are queued.
3. **Grow greedily** by marginal score.
4. **Improve by local search** (swap and move) for a bounded time. For small pools (< ~40) an exact
   ILP/CP-SAT solve is affordable and gives a quality baseline to measure the heuristic against in
   Phase 0.

A player can be left unmatched in any tick. They just stay in their window, and their wait-time
priority goes up.

### 7.2 Hard vs soft constraints

**Hard. These are never violated.**

- Same game, and a lobby size inside *every* member's accepted range.
- Platform / cross-play compatibility, and a region or latency bound where the game needs one.
- **Hard blocks.** If `a` has `avoid-hard` on `b`, then `a` and `b` are never in the same lobby.
  (Proposed, Margo.) Lean: **5 per player**, which lines up with Overwatch's 3 pinned and Dota's
  paywalled 25. They don't decay. Because of the cap, a player can't use hard blocks to exclude a
  meaningful share of a pool (see §8).
- Age band separation (§10).
- Mandatory filters the player sets on themselves, such as "voice required".

**Soft. These are weighted and can be broken when the pool is thin.**

- `avoid-soft` edges: a large negative weight that **decays** (lean: half-life around 30 days,
  refreshed if re-applied). Overwatch's 7-day expiry is the shipped precedent.
- `more` edges: positive weight (§7.3).
- Comm-style and intensity compatibility: medium weight. Interest overlap: low weight.
- Newcomer / low-connectivity boost and anchor placement (§7.4).
- Wait-time priority: this grows with time in window and is what eventually pays for breaking soft
  constraints.
- Small random noise (§7.6).

**An avoid only affects the avoider's own matches** (Proposed, Margo). `a` avoiding `b` becomes a
constraint on lobbies containing `a`. It is never a property of `b`: it doesn't show up as `b`'s
reputation or lower `b`'s priority anywhere else. Lean: adopt. This is the rule that stops the
rich-get-richer and weaponisation problems from turning into a hidden global score.

### 7.3 How "match me with them more often" is weighted

A lobby's score is the sum of pairwise terms plus per-player terms. For a directed `more` edge
`a → b`:

- **Base weight `M`**, applied when both are in the lobby. If the edge is mutual (`b → a` also
  exists), the pair gets a bonus. Mutuality is used internally and is **never revealed** (§7.6).
- **Asymmetry rule.** If `a` has `more` on `b` and `b` has *any* avoid on `a`, the avoid wins
  outright. A `more` can never override the other person's avoid. This is R4 applied to the edge
  case it names.
- **Diminishing returns in co-play count**, for example `M / (1 + k·log(1 + n_ab))`. This way a pair
  that has already played 40 times doesn't swamp every lobby, and new people keep getting slots.
- **Recency.** Pairs who haven't co-played recently get a small "reunion" bump. R2 is about finding
  each other again, so the weight should rise the longer it has been.
- **"Core + one or two" composition bonus** (derived from R2). The best lobby, as Ceryce described
  it, is a core that already likes each other plus one or two fresh people. The objective adds a
  bonus for lobbies with a `more`-connected core of ≥ 2 **and** at least one open seat filled by
  someone with no history with that core (a newcomer or stranger). This is how new people get into
  groups. Without it, the matcher would converge on the same closed clusters.

Implicit signals, such as the same people re-queuing together or long sessions, are **not used in
v1** (lean). Explicit signals are easier to explain, easier to delete and easier to audit. This is
an open question for later.

### 7.4 Rich-get-richer mitigations

The risk (R5): a pure affinity objective pulls well-liked players together, and players with many
avoids end up matched only with each other.

- **Newcomer / low-connectivity boost** (Proposed, Margo). Players with few `more` edges, or who
  are new, get a priority bonus to fill the "one or two" seats in cores. Lean: adopt, and decay it
  over the first ~20 sessions.
- **Anchors** (R7). Anchors are players who opt in to "put me with newcomers and strangers". The
  matcher prefers placing newcomers into lobbies with an anchor. Anchors get nothing visible for it.
  No badges, because a badge turns into a status game (lean). Open details: whether anchors also
  host lobbies of players with high avoid counts, and whether that is fair to ask of anyone
  (§14).
- **Assortativity guard.** Phase 0 measures how often players whose inbound-avoid count is in the
  top decile are matched *only* with each other. If that happens, the matcher adds a mixing term,
  and that term is always overridden by the avoider-local constraints. **Honest caveat:** this pulls
  against R4. If many people genuinely avoid someone, respecting all of those avoids *does*
  concentrate that person among non-avoiders. The spec does not claim to solve this. Phase 0 is
  there to measure how bad it gets.

### 7.5 Relaxation when the pool is thin

Proposed (Margo). The matcher widens the pool **before** it fails anyone. Each step is presented to
the user as ordinary queue wait, never as "no one wants to play with you":

1. **Strict.** All soft preferences weighted normally.
2. **Widen time zone / region**, within whatever latency bound the game has.
3. **Widen group size** inside the range the player accepted, for example 5 → 4.
4. **Neighbouring games.** Lean: only games the player has *already listed*, never inferred ones.
   An alternative the matcher could offer: "nobody's up for X, 3 people are up for Y which you also
   listed".
5. **Larger community.** Only once more than one community exists (§9, Phase 2), and only for
   players who opted in.
6. **Break soft avoids**, lowest-weight and most-decayed first. Hard blocks are never broken.
7. **Keep waiting.** The window stays open and the player is pinged if a lobby forms.

**Which player gets left over is a fairness decision.** When the pool doesn't divide evenly into
lobbies, somebody waits. Wait-time priority makes sure it isn't the same person every time. That
matters most for a heavily soft-avoided player, whose growing priority eventually *forces* a soft
avoid to break rather than letting them wait forever.

### 7.6 Silent rejection

The risk (R5): `b` works out that `a` avoided them.

- **Never show who is online or queued** (Proposed, Margo). There's no presence, no "3 people you
  like are playing", and no queue roster. You only learn who you're matched with when the lobby
  forms.
- **Noise in matching** (Proposed, Margo). A small random term means a missing reunion looks the
  same as bad timing. Lean: adopt, and tune it in Phase 0 against a *detection test*. That test
  asks whether a statistically motivated `b` could tell "a avoided me" apart from "a and I were
  unlucky" at realistic pool sizes.
- **Edges are never revealed.** That covers `more`, `avoid` and mutual `more` alike. There is no
  "they liked you too!", because that is the dating-app mechanic R1 rejects (lean; §14).
- **Honest limit.** In a tiny pool, such as a niche game where the same six people are always
  online, no amount of noise hides a consistent absence. R5 accepts this. The spec does not claim
  otherwise.

## 8. Weaponized avoidance: the lockout arithmetic

This section works through R8. Take one game's compatible pool at one moment:

- `N` = players in an open window who could be in a lobby with target `P` (P included).
- `L` = lobby size.
- `A` = players in that pool whose avoid on `P` the matcher is currently honouring.

`P` can only be placed if at least `L − 1` non-avoiders are available: `N − 1 − A ≥ L − 1`, or
**`A ≤ N − L`**. Lockout therefore needs **`A ≥ N − L + 1`** simultaneous, *queued* avoiders.

Expressed as the share of the *other queued players* who must be avoiding `P`:

| `N` queued | `L` = 5 | `L` = 4 | `L` = 3 |
|---:|---:|---:|---:|
| 6 | 2 of 5 (40%) | 3 of 5 (60%) | 4 of 5 (80%) |
| 8 | **4 of 7 (57%)** | 5 of 7 (71%) | 6 of 7 (86%) |
| 10 | 6 of 9 (67%) | 7 of 9 (78%) | 8 of 9 (89%) |
| 20 | 16 of 19 (84%) | 17 of 19 (89%) | 18 of 19 (95%) |
| 50 | 46 of 49 (94%) | 47 of 49 (96%) | 48 of 49 (98%) |

What follows from the table:

1. **Ceryce's point holds at scale.** With a healthy pool, lockout needs almost everyone queued to
   be avoiding one person.
2. **Margo's counterpoint holds off-peak.** When `N` is close to `L`, a handful of online avoiders
   is enough. The 8-queued / lobby-of-5 example needs only 4. Niche games and 3 a.m. live near the
   top rows of the table.
3. **Smaller lobbies and flexible size ranges resist lockout.** Letting players accept "3–5"
   instead of exactly 5 is one of the strongest anti-lockout levers available. This is a reason to
   encourage size *ranges* in the UI.
4. **Soft avoids cannot lock anyone out indefinitely.** The relaxation ladder (§7.5) breaks soft
   avoids once wait-time priority is high enough, so a mass *soft* avoid delays `P` and nothing
   more. Only **hard** blocks can lock someone out. Hard blocks are capped (lean: 5 per player), so
   a lockout needs `N − L + 1` distinct people to each spend a scarce slot on `P` and be queued at
   the same moment.

**Who pays for an avoid?** Lean (derived from the "an avoid only affects the avoider's matches"
principle): when the matcher must choose between making the avoider wait and making the avoided
player wait, and wait priorities are equal, **the avoider waits**. An avoid is a request, and the
avoider pays for it in their own queue time. When a soft avoid has to break, the matcher breaks the
most-decayed, lowest-weight one first.

**Mass avoidance as a signal** (Proposed, Margo). If many people avoid someone, that goes to
**human review only when it comes with actual reports**. It is never an automatic verdict, never a
hidden score, and never a matching penalty applied to `P` globally. Lean: adopt. Lean addition:
detect **coordinated hard-blocking**, where several accounts that often queue together hard-block
the same target within a short window. Send that to review too, because in that case the likely
bad actor is the group, not the target.

**Unsolved, stated plainly:** a determined clique in a niche game with a thin pool can still lock
someone out at specific hours using hard blocks. We can detect it and review it. We can't make it
arithmetically impossible without weakening hard blocks, and hard blocks exist for real safety
reasons. Phase 0 measures how often this happens at realistic sizes.

## 9. Density and launch strategy

R3 is the primary risk. The core feature (R2) needs *two specific people* to be in windows at the
same time, which is harder than filling any lobby.

### 9.1 Back-of-envelope concurrency

These are assumptions to be replaced by Phase 0 output. Let `M` be opted-in players for one game in
one region, `h` the hours per week each has an open window, and `f` the peak-to-average factor
(evenings, weekends).

Peak concurrency ≈ `f · M · h / 168`. For lobbies of 5 with real *choice* (lean target: ≥ 3L = 15
concurrent at peak):

| Window habit | `h` | `f` | `M` needed |
|---|---:|---:|---:|
| Live queue only ("I'm on now") | 2 | 2.5 | ~500 |
| Availability windows ("ping me in the next few hours", a few times a week) | 6 | 2.5 | ~170 |
| Generous windows | 10 | 2.5 | ~100 |

**Availability windows cut the required community size by roughly 3×**, which is why the model
uses windows (§6) rather than only a live lobby wait. A window is still not a scheduled group:
nobody commits to anyone, and it only says when *you* are free. Rematch rates for specific pairs
are what R2 depends on, and they are harder to estimate on paper. Phase 0 measures them directly.

### 9.2 Start narrow

The engine is game-agnostic (R1). **The launch should not be.** Lean: one existing community, 1–3
games, one region. Prefer **co-op PvE games with 4-player lobbies** and no skill balancing, where
sessions are sociable and voice is common: the "4-player co-op" genre. Small lobbies need less
density and resist lockout (§8), and skill doesn't have to be matched.

**Candidate launch niche: async Archipelago multiworlds** (added 2026-09-24; Ceryce: *"definitely add it
as a candidate launch niche. I wasn't even thinking async archipelago, but that's genius."*).
[Archipelago](https://archipelago.gg/faq/en/) is a cross-game randomizer that builds one shared
multiworld from each player's own game, described by a YAML file, and supports **async** play, where
players connect at their own pace. As of 2026-09-24 a quick search found no automatic matcher or
seed-maker: groups form by hand in the Archipelago Discord or interest threads, and one person
collects YAMLs and generates the seed. Why it fits:

- **Async removes the concurrency requirement** that drives §9.1. Players only need to join the
  same seed, not be online at the same minute, so the density needed collapses from "queued now" to
  "interested this week".
- **The matcher can also be the maker.** It groups compatible requests (desired player count, pace,
  goal length, sync vs async), collects the YAMLs, generates the seed and hands out the room. That
  removes the organiser work that currently gates who gets to play.
- **Rematch maps onto "the next seed".** "Match me with these people again" (R2) becomes "put us in
  the same next multiworld", which is the same thing as the group-looking-for-one-or-two shape of R2.
- **Caveats to check:** Archipelago's own licence and generation API, server hosting costs for
  long-running async rooms, per-game setup friction, and whether §8's lockout arithmetic behaves
  differently when the "pool" is a weekly sign-up window instead of a live queue.

### 9.3 MVP shape: Discord-bot-first, evaluated

| Option | Density | Build cost | Hand-off | Risk |
|---|---|---|---|---|
| **A. Discord bot inside one existing community** (lean) | Borrows the community's existing density and trust. Cold start is "a server's members opt in", not "strangers find an app". | Low: slash commands, DMs, temp channels. No accounts, no voice infra. | Trivial: the bot creates a private temp voice and text channel for the lobby. | Discord dependency and policy. Bot DMs can be disabled by users. Density is capped at one server. |
| B. Standalone web or mobile app | Worst cold start: an empty room. | High: accounts, notifications, a hand-off path, T&S tooling. | Hard: needs in-game handle exchange. | Everything in R3. |
| C. Cross-server Discord network (like LFG Hub's network) | Best long-term density. | Medium (on top of A). | Same as A, across servers. | Moderation across communities with different norms. |
| D. Contribute to an existing OSS LFG bot | Inherits its installs. | Unknown; depends on fit. | Inherited. | The R2 model would be bolted onto a post-and-join design that it rejects. |

**Lean: A, then C in Phase 2.** Discord-first does sidestep the cold start *for the first
community*, because the density problem is shrunk to fit one server rather than solved. The MVP
needs only interactions (slash commands, buttons, DMs) and channel management. It doesn't read
message content, so it needs no privileged Message Content intent.

**MVP flow (sketch).**

1. `/up game:<x> size:3-5 for:2h`, plus a one-time `/style` for comm-style.
2. The bot DMs the player when a lobby forms, then creates a private temp voice and text channel
   with those members only.
3. After the channel has been empty for a while, the bot DMs each member a "recently played with"
   card listing each person with the options **more · neutral · avoid · block · report**. Neutral
   is the default, and ignoring the card is fine.
4. "Recently played with" lasts 14 days (lean), so a player can set an edge later but not months
   later.

## 10. Trust & safety

The product puts strangers into voice channels with each other. That is its function, and it's
also the main risk.

- **18+ only at launch** (lean). Matching adults and minors as strangers in voice is the riskiest
  thing this could do. In the MVP, age is self-attested and backed by the host community's own
  rules. **Self-attestation is weak.** We accept that for a closed alpha and don't pretend it's
  verification. Age bands are a hard constraint if minors are ever admitted, which is Ceryce's call
  (§14).
- **Avoid ≠ report.** An avoid is a *preference*: private, unreviewed, affecting only the avoider.
  A report is an *allegation*: it goes to humans. Lean: filing a report also applies a hard block
  *outside* the 5-slot cap. Abusive reporting is itself something moderators can act on.
- **Human review, not automated verdicts.** Moderators act on reports. Mass avoidance only matters
  alongside reports (§8). There's no hidden reputation score, no shadow-banning, and no automated
  penalty to matching priority.
- **Who moderates.** In the Phase 1 MVP, the **host community's moderators** do, through a private
  mod channel that the bot posts reports into. They can remove a player from the matcher. We don't
  run a central moderation team before Phase 2. How cross-community moderation works in Phase 2 is
  an open question.
- **Out of our sight after hand-off.** We don't record voice or read messages. Whatever happens in
  the session reaches us only through reports. That is a deliberate privacy trade-off, and it limits
  what moderators can do.
- **Ban evasion.** Identity is a Discord account. Alt accounts are a known limit. Lean mitigation: a
  minimum Discord account age and membership in the host server.
- **Anchor wellbeing.** Anchors can opt out instantly and silently. They aren't asked to absorb
  difficult players (lean; §14).
- **No paywalled safety.** Blocking, avoiding and reporting are never paid features. Dota's
  paywalled avoid list is the counter-example.

## 11. Privacy

- **Data held (minimum).** Platform user ID; games, size ranges and windows; comm-style,
  interests and region; outgoing edges; co-play records; reports. **Not held:** message content,
  voice, presence or activity scraped from Discord or games, contacts, or real names.
- **Edges are the most sensitive data we keep.** Nobody sees an edge except its author, and that
  includes the target. In a report review, moderators see the report and at most a *count* of
  avoids (lean), never who avoided whom.
- **No presence exposure.** No online indicators, no rosters and no "X is queued".
- **Retention (lean).** Windows are deleted when they close. "Recently played with" lasts 14 days.
  Soft avoids decay and are deleted once their weight is negligible. Co-play records older than 12
  months are deleted. Reports are kept per moderation policy.
- **User control.** Every user can view, export and delete their own data. Deleting an account
  removes edges in both directions, including other people's edges *about* that person.
- **No third parties.** No ads, no sale of data, no third-party analytics. Being open source means
  anyone can check the matching rules and the data handling.
- **Jurisdiction.** Lean: follow GDPR-style rights for everyone rather than by region.
- **Phase 0 uses synthetic data only.** No real person's data is involved before Phase 1.

## 12. Phases

### Phase 0: matcher simulator (nothing user-facing)

This phase builds the real matcher, runs it against **synthetic populations**, and measures the
risks from R3, R5 and R8 before any real person is involved. Its output is numbers, and those
numbers decide whether Phase 1 is worth building in the shape described here.

**Build:**

- **Population generator.** Players get game lists, size ranges, availability schedules (time zone
  and evening peaks), comm-styles, and a hidden *compatibility* vector. After each simulated session,
  that vector produces ground-truth "enjoyed / didn't" outcomes with noise, and those outcomes turn
  into `more` / `avoid` edges at configurable rates. Included archetypes: abrasive players,
  avoid-happy players, anchors, newcomers arriving over time, and a **coordinated clique** that
  hard-blocks one target.
- **Matcher v0.** This is the §7 algorithm as real, reusable code, not a mock, plus an exact CP-SAT
  solve on small pools as a quality baseline.
- **Simulation harness.** It runs simulated weeks under a parameter sweep over pool size, lobby
  size, window length, weights, noise, hard-block cap and decay.

**Measure:**

| Question | Metric |
|---|---|
| R8 lockout | Share of peak ticks in which any player is unplaceable because of hard blocks, by `N` and `L`. Also the clique scenario's lockout hours per week. |
| R3 density | Wait-time distribution for a lobby, by `M` and window habit. This replaces §9.1's guesses. |
| R2 rematch | For pairs with mutual `more`: time to next co-match, and the share reunited within 14 days. |
| Groups forming | Emergence of stable clusters (≥ 3 players, co-matched ≥ k times). Simulated hours per pair against Hall's ~50 h mark. |
| R5 rich-get-richer | Distribution of match rate and lobby affinity per player. Bottom-decile vs median. Assortativity of inbound-avoid count, i.e. whether high-avoid players get matched only with each other. |
| Newcomers / anchors | Sessions until a newcomer's first mutual `more`, with and without the boost and anchors. |
| R5 silent rejection | **Detection test:** how well can a motivated player's own match history tell whether a specific person avoided them, by pool size and noise level? |

**Exit criteria.** The thresholds are Ceryce's call, informed by the first run. Suggested starting
points for 4-player co-op, one region:

- Median peak wait under 10 minutes at `M` ≈ 200 with availability windows.
- Hard-block lockout in under 1% of peak ticks at realistic avoid rates.
- Bottom-decile match rate at least 50% of the median.
- Most newcomers reach a mutual `more` within 5 sessions.
- Detection-test advantage near chance at `N` ≥ 20.

**Kill / rethink criterion:** if no parameter set meets these at `M` ≤ ~500, the MVP shape needs
rethinking before Phase 1. Possible changes are longer windows, smaller lobbies, or cross-community
pooling from day one.

### Phase 1: Discord bot, closed alpha

One community, 1–3 co-op games, one region, 18+. It runs the §9.3 flow and uses matcher v0 from
Phase 0. Moderation is done by the host community's mods. Success: people use it more than once,
reunions happen, and at least one group graduates to its own server.

### Phase 2: more communities

Onboard additional servers. Opt-in cross-community pooling (§7.5 step 5). Self-hosting docs, so
communities can run their own instance. A cross-community moderation model.

### Phase 3: only if earned

Another front-end (for example web) or other platforms. This happens only if Phases 1–2 show real
pull. It isn't planned in any more detail now.

## 13. Deliberately not built

These go beyond the non-goals in §3. They are concrete features we will refuse even when someone
asks for them:

- Friends lists, followers, public profiles, people search, "people you may like".
- Showing that a `more` was mutual ("they liked you too!").
- Online presence, queue rosters, "your favourites are playing now".
- Visible reputation: karma, endorsements, ratings, badges (including anchor badges).
- Our own chat, DMs or voice.
- Calendars, recurring events, fixed group rosters.
- Skill ratings or MMR.
- Game API or overlay integrations (hand-off is by channel or handle).
- Streaks, engagement nudges, re-engagement notifications. Notifications are limited to "your lobby
  formed" and the post-session card.
- Paid tiers for safety features. Paid "more avoid slots" in particular.

## 14. Open questions

| # | Question | Lean | Whose call |
|---|---|---|---|
| 1 | **Product name** | Decide after Phase 0, once the MVP shape is settled. Check for clashes with Discord app directory and trademark listings before committing. | Ceryce |
| 2 | **Platform / MVP shape** | Discord bot in one existing community (§9.3 option A), then a cross-server network. | Ceryce |
| 3 | **First community and games** | A community she already belongs to, 4-player co-op PvE, one region. | Ceryce |
| 4 | **License** | AGPL-3.0, so hosted forks of a community service stay open. Alternative: Apache-2.0 for maximum reuse, which suits the "contribution to the world" framing but allows closed hosted forks. | Ceryce |
| 5 | **Monetization, or none** | None. Donations to cover hosting at most, and never paywalled safety (§13). | Ceryce |
| 6 | **Hosting** | Phase 0 needs none. Phase 1: the cheapest workable option, either one small VPS or a serverless HTTP-interactions bot with per-game queue state (for example Cloudflare Workers + Durable Objects). Decide at Phase 1 start. | Ceryce (tech recommendation from us) |
| 7 | Implementation language | Python for Phase 0 (OR-Tools CP-SAT baseline, fast iteration). Revisit when hosting is chosen. | Engineering; confirm with Ceryce |
| 8 | Hard-block cap | 5, then adjust using Phase 0 lockout data. | Ceryce, after Phase 0 |
| 9 | Soft-avoid decay | Half-life ~30 days. Tune in Phase 0. | Engineering |
| 10 | Reveal mutual `more`? | Never. That is the dating-app mechanic. | Ceryce |
| 11 | Implicit signals (co-queue, session length) | Not in v1. Explicit signals only. | Ceryce |
| 12 | Should anchors also absorb high-avoid players? | No. Anchors are for newcomers only. Asking volunteers to carry difficult players is unfair and will burn them out. | Ceryce |
| 13 | Minors | 18+ only. Revisit only with real age assurance and a separate design. | Ceryce |
| 14 | Microsoft patent US 7,677,970 status | Confirm it has lapsed before Phase 1. | Ceryce (legal) |
| 15 | Phase 0 exit thresholds | The §12 suggestions as the starting point. | Ceryce, after the first sim run |
| 16 | Banter/content-tolerance axis | Unsure. It could be a strong signal and it could also be a proxy for bad behaviour. Test in alpha. | Ceryce |
| 17 | Cross-community moderation model | Unsolved. Needed before Phase 2. | Ceryce + host communities |
