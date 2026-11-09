# Final Project Concept: Lit Windows

**Yun-Chung Liu (yl4445)** · Concept submitted November 9, 2026

## The idea in one sentence

A small paper apartment building sits on each friend's desk, with one window for each person in the group. A window lights up when that friend is at their desk, so late at night you can look over and see who else is still up working, the way you might look across a courtyard and notice whose lights are on.

## The problem and who it is for

During finals, my friends and I study in separate dorms. We study better knowing other people are grinding too, but texting "still up?" interrupts everyone, and a group video call is more than anyone wants to keep open for six hours. Lit windows are a cue that already works in real buildings: you can see that someone is home without them doing anything, and they do not have to answer you.

**Primary users:** a group of 3 to 5 friends who have all agreed to share their desk presence with each other, each in their own room.
**Setting:** desks in dorm rooms and apartments, mostly in the evening and late at night.
**Other people around:** roommates, who never agreed to anything. The sensor has to watch only the owner's chair, as in Lab 5.

## The interaction

**Being there (passive).** A sensor at my desk notices when someone is in my chair and publishes `here` or `away` over MQTT. On every friend's building, my window glows warm. When I leave, my window does not snap off. It fades over about ten minutes, so a glance tells you "just left" apart from "gone for the night."

**Knocking (active).** Each window has a capacitive pad on the sill. If I tap Hong's window, Hong's own window, the one that stands for them on their building, pulses twice like a knock. If Hong taps my window back, both buildings flash once together. That is the whole conversation: "you there?" and "yeah." No text and no notifications.

**Closing the curtain (privacy).** A small paper curtain on my own window can be pulled down (it presses a switch). With the curtain closed, my friends see a dim, curtained window: I am around but do not knock. Nothing is sensed or sent beyond "curtain closed." This is our Lab 6 "quiet please" idea, made physical.

**Morning (optional).** Along the bottom of the building is a row of tiny lights for the hours of the night. In the morning it shows when each window was lit, like the 24-hour history idea from our Lab 1 feedback. Whether this should exist at all is one of my open questions below.

## Storyboard (to draw in class)

1. **10 PM.** I sit down to study. My window lights up on three other desks across campus.
2. **1 AM.** I'm tired and glance at the building. Two other windows are still lit. I keep going.
3. **1:30 AM.** Daniel's window starts fading: he just left. I tap Pablo's window. On Pablo's desk, his window knocks. He taps mine back, and both buildings flash.
4. **2 AM.** I pull my curtain down to focus. Friends see a curtained window and leave me alone.
5. **Morning.** The bottom row shows who was up until when.

## What it builds on from the labs

| Lab | What I am carrying forward |
| --- | --- |
| **Lab 1: Pulse Room** | Light as the main channel. Your presence becomes part of a shared display next to other people's. The fix for the weakness we found: you should *see* someone leave (the slow fade) instead of having them disappear. Breathing light instead of blinking. |
| **Lab 2: Sun and moon clock** | A glanceable display that shows time of night without numbers. The building at night is the same move: ambient, not literal. |
| **Lab 3: Mini Judge** | Clear state cues. When I knock, my own building has to show "sent," "seen," and "knocked back." Otherwise it feels like the judge freezing during its pause. |
| **Lab 4: Fly Shoo** | One deliberate physical action leads to one clear response (tap → knock). Mounting and placement matter as much as code. Jovian's note that the control has to sit where your hand already is. |
| **Lab 5: Desk Curfew** | Watching the chair, not the person or the bed. Saving only text states, no images. Keeping the honest meaning of the data: `away` means "nobody detected," not "asleep." Showing a "no data" state instead of guessing. |
| **Lab 6: Mouse Game and Part A ideas** | Several Pis talking over MQTT, using the desk presence board and friends' sky clock ideas from Part A. The lesson from the playtest: presence can tolerate delay, but a knock and its reply have to feel immediate. |

## Design questions I want to work through

- **Consent and roommates.** The sensor must only cover the owner's chair. A proximity or pressure sensor on the chair might be better than a camera: it cannot see a roommate at all, and nobody has to worry about images.
- **What absence means.** A dark window could mean asleep, at the library, or a sensor failure. In Lab 5, the language model confidently got this wrong. Here the device should show only what it knows: lit, fading, curtained, dark, or "offline" (a slow flicker, like Desk Curfew's amber).
- **Does it turn into surveillance?** The morning history row and "who is up at 3 AM" could make friends feel judged, or push people to stay up longer. Should it exist, be opt-in, or be visible only to yourself?
- **Asymmetry.** If I can see you, you can see me. There is no watching without being watched. Closing my curtain should also stop me from knocking, so privacy is not one-sided.
- **Glanceability.** Each window needs to be readable from across the room, and the building has to be dim enough to live on a desk at 2 AM without being a light source you want to turn off.
- **Scaling the group.** Five windows are easy to read. What about ten? Or a second building for a different group?

## Other scenarios to test the concept against

- **Long-distance partners or family in another time zone:** the window could show a night sky behind it when it is night for them (Lab 2's sky clock idea).
- **Checking on a grandparent:** our first Lab 1 setting. The same building but a different meaning. A dark window at noon is worrying in a way it is not for a college student.
- **Lab or studio space:** one building for everyone in a shared workspace, showing whose bench is occupied.

## Rough build

- **Per person:** Raspberry Pi, one presence sensor (Qwiic proximity or a chair switch; webcam with YOLO as the fallback from Lab 5), a capacitive sensor with one pad per window, a curtain switch, and LEDs or a NeoPixel strip behind paper windows in a cardboard building.
- **Shared:** the course MQTT broker. Topics like `IDD/<team>/windows/<name>/presence`, `/knock`, `/curtain`, and `/status` with a last-will message, so an unplugged device shows as offline instead of "away."
- **Fits a team of 3 or 4:** each person builds and lives with their own building, which makes the testing real.

## How I would test it

Build two buildings first and run them for one real evening between two rooms. I would check whether the fade timing reads as "just left," whether a knock gets noticed without being annoying, and whether the reply feels immediate over the network. Then I would add the remaining windows and run it for a few nights with the whole group, and ask afterward whether it made studying feel less lonely or more watched.

## Alternatives I considered

- **Roommate Court across rooms** (Lab 6 Part A): a fun extension of the Mini Judge, but it is mostly a speech-recognition problem, and Lab 3 showed how much it depends on the script.
- **Pulse Room on the last train** (Lab 1, Storyboard 4): the concept I like most emotionally, but I could not test it in a real setting with real strangers.
- **Desk Curfew 2.0:** add accountability between friends. This is folded into Lit Windows as an open question rather than a feature, because it pushes toward judging people.

> **AI Disclaimer:** This concept write-up was drafted with help from AI (Claude Code), working from my six lab write-ups. The concept direction and final edits are mine.
