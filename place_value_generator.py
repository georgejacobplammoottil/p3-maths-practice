"""
Place Value Question Generator
================================
Generalised from Q1 (ACS Junior P3 Maths Weighted Assessment 1, 2025):

  "What is the value of the digit 7 in 3875?"
   Options: (1) 700  (2) 100  (3) 70  (4) 10

The options follow a precise 2×2 structure based on place value:

                  | with digit          | without digit  |
  ----------------+---------------------+----------------|
  one place UP    |  digit × (pv × 10)  |  pv × 10       |  e.g. 700, 100
  current place   |  digit × pv   ✓     |  pv            |  e.g.  70,  10

  where pv = place value of the target digit (10 for the tens place).

Usage
-----
  # Single question
  q = generate(3875, digit_position=1)   # 1 = tens place

  # Batch of random questions
  questions = generate_batch(n=10, num_digits=4)

  # Print any question
  display(q)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ── Constants ──────────────────────────────────────────────────────────────────

PLACE_NAMES = {
    0: "ones",
    1: "tens",
    2: "hundreds",
    3: "thousands",
}


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Option:
    label: int        # 1, 2, 3, or 4
    value: int        # Numeric value shown to student
    is_correct: bool


@dataclass
class PlaceValueQuestion:
    number: int                  # The full number, e.g. 3875
    target_digit: int            # The digit being asked about, e.g. 7
    digit_position: int          # 0=ones, 1=tens, 2=hundreds, 3=thousands
    place_value: int             # e.g. 10 for tens place
    correct_answer: int          # e.g. 70
    options: list[Option]        # Always 4 options
    section: str = "A"
    marks: int = 1
    topic: str = "place value"

    @property
    def text(self) -> str:
        return f"What is the value of the digit {self.target_digit} in {self.number}?"

    @property
    def correct_option(self) -> Option:
        return next(o for o in self.options if o.is_correct)


# ── Core logic ────────────────────────────────────────────────────────────────

def _extract_digit(number: int, position: int) -> int:
    """Return the digit at the given position (0=ones, 1=tens, …)."""
    return (number // (10 ** position)) % 10


def _build_options(digit: int, place_value: int, shuffle: bool = True) -> list[Option]:
    """
    Build 4 options using the observed 2×2 distractor pattern:

      one place up  │  digit × (pv×10)   │  pv×10
      current place │  digit × pv  ✓     │  pv
    """
    pv_up = place_value * 10

    raw = [
        (digit * pv_up, False),   # e.g. 700 — digit in next place up
        (pv_up,         False),   # e.g. 100 — next place value itself
        (digit * place_value, True),   # e.g.  70 — CORRECT
        (place_value,   False),   # e.g.  10 — current place value itself
    ]

    # Remove duplicates (e.g. if digit == 1, digit×pv == pv)
    seen: set[int] = set()
    unique: list[tuple[int, bool]] = []
    for value, correct in raw:
        if value not in seen:
            seen.add(value)
            unique.append((value, correct))

    if shuffle:
        random.shuffle(unique)
    else:
        unique.sort(key=lambda x: x[0], reverse=True)  # descending, as in original

    return [
        Option(label=i + 1, value=val, is_correct=correct)
        for i, (val, correct) in enumerate(unique)
    ]


def generate(number: int, digit_position: int, shuffle_options: bool = False) -> PlaceValueQuestion:
    """
    Generate a single place-value question.

    Args:
        number:           The number to use, e.g. 3875.
        digit_position:   Which digit to ask about (0=ones … 3=thousands).
        shuffle_options:  Randomise option order (default: descending, as in original).

    Returns:
        PlaceValueQuestion
    """
    digit = _extract_digit(number, digit_position)
    place_value = 10 ** digit_position
    options = _build_options(digit, place_value, shuffle=shuffle_options)
    correct = digit * place_value

    return PlaceValueQuestion(
        number=number,
        target_digit=digit,
        digit_position=digit_position,
        place_value=place_value,
        correct_answer=correct,
        options=options,
    )


def generate_random(
    num_digits: int = 4,
    avoid_digit: int | None = None,
) -> PlaceValueQuestion:
    """
    Generate a question with a random number and random non-zero target digit.

    Args:
        num_digits:   How many digits the number should have (2–4).
        avoid_digit:  Skip this digit value (e.g. 0 to avoid zeros).
    """
    low = 10 ** (num_digits - 1)
    high = 10 ** num_digits - 1

    while True:
        number = random.randint(low, high)
        position = random.randint(0, num_digits - 1)
        digit = _extract_digit(number, position)
        if digit != 0 and digit != avoid_digit:
            return generate(number, position, shuffle_options=True)


def generate_batch(n: int, num_digits: int = 4) -> list[PlaceValueQuestion]:
    """Generate n random place-value questions."""
    return [generate_random(num_digits=num_digits, avoid_digit=0) for _ in range(n)]


# ── Display helpers ────────────────────────────────────────────────────────────

def display(q: PlaceValueQuestion, show_answer: bool = False) -> None:
    place_name = PLACE_NAMES.get(q.digit_position, f"10^{q.digit_position}")
    print(f"{q.text}")
    print(f"  [digit {q.target_digit} is in the {place_name} place → value = {q.correct_answer}]"
          if show_answer else "")
    for opt in q.options:
        marker = " ✓" if (show_answer and opt.is_correct) else ""
        print(f"  ({opt.label}) {opt.value}{marker}")
    print()


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Original Q1 (exact reproduction) ===")
    q1 = generate(3875, digit_position=1)   # digit 7 in tens place
    display(q1, show_answer=True)

    print("=== 5 randomly generated questions ===")
    for i, q in enumerate(generate_batch(5), start=1):
        print(f"Q{i}.", end=" ")
        display(q, show_answer=True)
