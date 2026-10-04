"""How the Mini Judge decides on its own, when there is no wizard.

It works out which case it is hearing from the words in the complaint, reads
each yes or no answer, and turns the answers into a verdict. Nothing here
touches the hardware, so it can be tested anywhere.

AI Disclaimer: written with help from AI (Claude Code).
"""

import re

from cases import CASES

YES = {"yes", "yeah", "yep", "yup", "yea", "ya", "sure", "correct", "right",
       "exactly", "definitely", "absolutely", "true", "totally", "course"}
NO = {"no", "nope", "nah", "never", "not", "nobody", "nothing", "wrong",
      "didn't", "wasn't", "weren't", "haven't", "hasn't", "don't", "doesn't",
      "isn't", "won't", "hadn't"}


def words(text):
    # Whisper sometimes writes curly apostrophes, so straighten them first
    return re.findall(r"[a-z']+", text.lower().replace("’", "'"))


def yes_or_no(text):
    """Returns "yes", "no", or None if the answer was neither.

    The first yes or no word wins, because people lead with it:
    "Yes, they didn't ask" is a yes.
    """
    for word in words(text):
        if word in YES:
            return "yes"
        if word in NO:
            return "no"
    return None


def which_case(text):
    """Returns the case whose keywords the complaint uses most, or None."""
    counts = []
    for case in CASES:
        hits = sum(1 for word in words(text) if word.startswith(case["keywords"]))
        counts.append((hits, case))
    counts.sort(key=lambda pair: pair[0], reverse=True)
    best, runner_up = counts[0][0], counts[1][0]
    if best == 0 or best == runner_up:
        return None  # no keywords, or a tie: ask instead of guessing
    return counts[0][1]


def score_answer(line, answer):
    """+1 if the answer points to unfair, -1 if it points to fair, 0 if unclear."""
    said = yes_or_no(answer)
    if said is None:
        return 0
    return 1 if said == line["unfair_if"] else -1


def verdict_for(score):
    if score >= 2:
        return "unfair"
    if score <= -1:
        return "fair"
    return "split"
