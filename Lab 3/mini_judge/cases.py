"""Everything the Mini Judge can say, grouped the way the wizard needs it.

AI Disclaimer: the charger case is ours; the food and chores cases were
suggested by AI, and the judge's lines for all three were drafted with AI help
(Claude Code).

Each line says what happens after the judge speaks it:
    listen      open the microphone and wait for an answer
    think       show THINKING and wait for the wizard
    deliberate  show THINKING for a fixed pause, then wait for the wizard
    verdict     show the verdict on screen
    adjourn     end the session and go back to waiting for the next person

`silence` is how many seconds of quiet end the participant's turn. Open
questions get 1.5 s so people can pause to think. Yes or no questions get
1.2 s: in Part 1 we planned 0.8 s, but that cut people off when they started
explaining instead of just answering.

`unfair_if` marks the yes or no questions the judge scores on its own: the
answer that points toward the roommate being unfair. `keywords` are the words
in a complaint that tell the judge which case it is hearing.
"""

OPEN = 1.5
YES_NO = 1.2


def ask(text, silence=OPEN, unfair_if=None):
    line = {"text": text, "then": "listen", "silence": silence}
    if unfair_if:
        line["unfair_if"] = unfair_if
    return line


OPENING = ask("Court is in session. What is your complaint?")
CLARIFY = ask("Is this about a charger, food, or chores?")
AGAIN = ask("Could you say that again?")
YES_OR_NO = ask("The court did not catch that. Please answer yes or no.", YES_NO)
DELIBERATE = {"text": "The court will now consider this dispute.",
              "then": "deliberate", "seconds": 3}
ADJOURN = {"text": "Court is adjourned. Thank you for your testimony.",
           "then": "adjourn"}

SHARED = {
    "Open": [
        OPENING,
    ],
    "Recover": [
        AGAIN,
        ask("Take your time. The court is patient."),
        ask("Tell the court more about that."),
        YES_OR_NO,
        CLARIFY,
    ],
    "Deliberate": [
        DELIBERATE,
    ],
    "Close": [
        ADJOURN,
    ],
}

CASES = [
    {
        "key": "charger",
        "name": "Borrowed charger",
        "question": "Is my roommate unfair for borrowing my charger without asking?",
        "keywords": ("charg", "cable", "cord", "phone", "batter", "plug"),
        "steps": {
            "Evidence": [
                ask("Did your roommate ask before taking the charger?", YES_NO, unfair_if="no"),
                ask("How long did they keep it?"),
                ask("Did your phone run out of battery because of it?", YES_NO, unfair_if="yes"),
                ask("Has this happened before?", YES_NO, unfair_if="yes"),
            ],
            "Confirm": [
                ask("So your roommate took your charger without asking. Is that right?",
                    YES_NO, unfair_if="yes"),
            ],
            "Remedy": [
                ask("What would make this right?"),
            ],
        },
        "verdicts": {
            "unfair": "Guilty of unauthorized charging. Your roommate must ask "
                      "first from now on, and owes you one full battery.",
            "fair": "Case dismissed. Borrowing a charger in an emergency is "
                    "forgivable. Next time, they should leave a note.",
            "split": "Split decision. They should have asked, but the charger "
                     "was left out in the open. Buy a second charger and share the cost.",
        },
    },
    {
        "key": "food",
        "name": "Eaten food",
        "question": "Is my roommate unfair for eating my food without asking?",
        "keywords": ("food", "ate", "eat", "snack", "leftover", "milk", "fridge", "meal",
                     "lunch", "dinner", "breakfast", "pizza", "cereal", "cookie", "drink"),
        "steps": {
            "Evidence": [
                ask("Was the food labeled with your name?", YES_NO, unfair_if="yes"),
                ask("How much of it did they eat?"),
                ask("Did they offer to replace it?", YES_NO, unfair_if="no"),
                ask("Is this the first time?", YES_NO, unfair_if="no"),
            ],
            "Confirm": [
                ask("So your roommate ate your food without asking. Is that right?",
                    YES_NO, unfair_if="yes"),
            ],
            "Remedy": [
                ask("What would make this right?"),
            ],
        },
        "verdicts": {
            "unfair": "Guilty of snack theft. Your roommate must replace the "
                      "food within twenty four hours.",
            "fair": "Case dismissed. Unlabeled food in a shared fridge is fair "
                    "game. Label it next time.",
            "split": "Split decision. Your roommate owes you half of the food, "
                     "and you owe the fridge a label.",
        },
    },
    {
        "key": "chores",
        "name": "Uneven chores",
        "question": "Is my roommate unfair for not doing their share of chores or costs?",
        "keywords": ("chore", "dish", "clean", "trash", "garbage", "laundr", "vacuum",
                     "bathroom", "rent", "bill", "pay", "paid", "toilet"),
        "steps": {
            "Evidence": [
                ask("Did you two agree on who does what?", YES_NO, unfair_if="yes"),
                ask("How long has this been going on?"),
                ask("Have you reminded them?", YES_NO, unfair_if="yes"),
                ask("Who has been doing the work instead?"),
            ],
            "Confirm": [
                ask("So your roommate keeps skipping their share. Is that right?",
                    YES_NO, unfair_if="yes"),
            ],
            "Remedy": [
                ask("What would make this right?"),
            ],
        },
        "verdicts": {
            "unfair": "Guilty of chore evasion. Your roommate takes the next "
                      "three turns, starting tonight.",
            "fair": "Case dismissed. Without an agreed schedule, there is no "
                    "rule to break. Make one together.",
            "split": "Split decision. You both write a chore chart tonight, "
                     "and both of you sign it.",
        },
    },
]

VERDICT_TITLES = {"unfair": "UNFAIR", "fair": "FAIR", "split": "SPLIT"}
