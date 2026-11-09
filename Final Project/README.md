# Final Project Concept: Lit Windows

**Yun-Chung Liu (yl4445)** · November 9, 2026

## The idea

Each friend in a group keeps a small paper apartment building on their desk, with one window per person. A window lights up when that friend is at their desk. Late at night you can look over and see who else is still up working, like noticing whose lights are on across a courtyard.

## Why

- During finals my friends and I study in separate dorms. Knowing others are working too helps, but texting "still up?" interrupts people, and a six-hour video call is too much.
- Lit windows are a cue people already understand: you can tell someone is home without them doing anything.

**Who:** 3 to 5 friends who all agree to share their desk presence.
**Where:** desks in dorms and apartments, mostly late at night.
**Also present:** roommates, who never agreed, so the sensor only watches the owner's chair.

## How it works

- **Being there:** a sensor notices when I'm in my chair. My window glows on every friend's building. When I leave, it fades over about ten minutes, so "just left" looks different from "gone for the night."
- **Knocking:** tap a friend's window and their own window pulses twice on their building. If they tap back, both buildings flash once. No text, no notifications.
- **Curtain:** pulling a paper curtain down over my window means "I'm here, but don't knock." Friends see a dim, curtained window.
- **Morning (maybe):** a row of tiny lights along the bottom shows when each window was lit overnight.

## Storyboard

1. **10 PM:** I sit down to study, and my window lights up on three desks across campus.
2. **1 AM:** I'm tired, glance over, see two other windows lit, and keep going.
3. **1:30 AM:** Daniel's window starts fading. I knock on Pablo's window, and he knocks back.
4. **2 AM:** I pull my curtain down to focus.
5. **Morning:** the bottom row shows who was up until when.

## What it builds on

- **Lab 1 (Pulse Room):** light as the medium, your presence shown beside others', and seeing someone leave instead of them just vanishing.
- **Lab 2 (sun and moon clock):** an ambient display you read at a glance, without numbers.
- **Lab 3 (Mini Judge):** clear state cues, so a knock shows "sent" and "knocked back" instead of feeling frozen.
- **Lab 4 (Fly Shoo):** one physical action, one clear response, with the control where your hand already is.
- **Lab 5 (Desk Curfew):** watch the chair, not the person; save no images; "away" only means nobody was detected.
- **Lab 6 (Mouse Game):** several Pis over MQTT, from our desk presence board idea. Presence can lag a little, but a knock has to feel instant.

## Open design questions

- **Roommates and privacy:** a chair switch or proximity sensor may be better than a camera, since it can't see anyone else.
- **What a dark window means:** asleep, at the library, or broken? Show only what's known, with a separate "offline" flicker.
- **Surveillance:** could the morning history make friends feel judged or push people to stay up later? Maybe it should be opt-in or private.
- **Fairness:** if I can see you, you can see me. Closing my curtain should also stop me from knocking.
- **Readability:** windows need to read from across the room while staying dim enough for 2 AM.

## Other scenarios

- **Long-distance partners:** show a night sky behind their window when it's night where they are.
- **A grandparent living alone:** a dark window at noon means something very different.
- **A shared lab:** one building showing whose bench is occupied.

## Rough build and test

- **Each person:** a Raspberry Pi, a chair presence sensor, a capacitive pad per window, a curtain switch, and LEDs behind paper windows in a cardboard building.
- **Shared:** the course MQTT broker, with topics for presence, knocks, curtain, and online status.
- **Test:** start with two buildings in two rooms for one evening. Check whether the fade reads as "just left" and whether knocks feel immediate. Then run the whole group for a few nights and ask whether it felt less lonely or more watched.

## Alternatives considered

- **Roommate Court across rooms:** fun, but mostly a speech-recognition problem.
- **Pulse Room on the last train:** my favorite emotionally, but hard to test with real strangers.
- **Desk Curfew between friends:** folded in as an open question, since it leans toward judging people.

> **AI Disclaimer:** This write-up was drafted with help from AI (Claude Code), working from my six lab write-ups. The concept direction and final edits are mine.
