"""
Question Generators — P3 Maths Practice Bank
=============================================
One generator function per question structure in taxonomy.json.
Each returns a dict with keys: text, options (MCQ) or None, answer, structure_id, topic.

Quick reference
---------------
MCQ questions (Section A):
  gen_digit_value_mcq(number, digit_position)          Q1  place value
  gen_expanded_form_mcq(number, missing_position)      Q2  expanded form
  gen_money_multi_item_mcq(n1, price1, n2, price2)     Q3  money multiplication
  gen_number_pattern_mcq(start, diff)                  Q4  number patterns
  gen_sum_difference_mcq(total, a)                     Q5  addition/subtraction
  gen_multiplication_repeated_addition_mcq(a, b)       --  multiplication (WA2)

Short-answer questions (Section B):
  gen_ordering(numbers, direction)                     Q6  ordering
  gen_direct_addition(a, b)                            Q7  addition
  gen_missing_digit_subtraction(minuend, subtrahend,
                                hidden_position)       Q8  subtraction
  gen_money_change(price1, price2, paid)               Q9  money change
  gen_money_budget(menu, budget)                       Q10 money budget
  gen_equal_groups_division(total, per_group)          --  division exact
  gen_division_round_up(total, per_container)          --  division with ceiling
  gen_reverse_division(divisor, quotient, remainder)   --  reverse division
  gen_fraction_simplification(numerator, denominator)  --  fractions
  gen_fraction_addition(num1, den1, num2, den2)        --  fraction addition

Long-answer questions (Section C):
  gen_diff_find_sum(diff, smaller)                     Q11 addition/subtraction
  gen_money_comparison_total(price1, less)             Q12 money two-step
  gen_money_sale_savings(unit_price, n, sale_price)    Q13 money savings

Batch helpers:
  generate_batch(structure_id, n, **kwargs)
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Any


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Question:
    structure_id: str
    topic: str
    text: str
    answer: Any                          # str or number
    options: list[str] | None = None     # None for open-answer questions
    correct_option: int | None = None    # 1-indexed; None for open-answer
    marks: int = 1
    section: str = "A"
    working: str = ""                    # Optional worked solution

    def display(self, show_answer: bool = False) -> None:
        marks_label = f"[{self.marks} mark{'s' if self.marks > 1 else ''}]"
        print(f"({self.section}) {marks_label}  [{self.structure_id}]")
        print(self.text)
        if self.options:
            for i, opt in enumerate(self.options, 1):
                marker = " ✓" if (show_answer and i == self.correct_option) else ""
                print(f"  ({i}) {opt}{marker}")
        if show_answer:
            print(f"  Answer: {self.answer}")
            if self.working:
                print(f"  Working: {self.working}")
        print()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_digit(number: int, position: int) -> int:
    return (number // (10 ** position)) % 10

def _shuffle_with_correct(values: list, correct_value) -> tuple[list, int]:
    """Shuffle a list and return (shuffled, 1-indexed position of correct_value)."""
    shuffled = values[:]
    random.shuffle(shuffled)
    return shuffled, shuffled.index(correct_value) + 1

def _cents_to_dollars(cents: int) -> str:
    return f"${cents // 100}.{cents % 100:02d}"


# ── Section A: MCQ generators ─────────────────────────────────────────────────

def gen_digit_value_mcq(
    number: int,
    digit_position: int,
    shuffle: bool = False,
) -> Question:
    """
    Q1 structure — "What is the value of the digit {d} in {number}?"
    Distractor pattern: 2x2_place_digit_grid
    """
    digit = _extract_digit(number, digit_position)
    pv = 10 ** digit_position
    correct = digit * pv

    raw = [digit * pv * 10, pv * 10, correct, pv]
    # Deduplicate while preserving order
    seen: set[int] = set()
    opts: list[int] = []
    for v in raw:
        if v not in seen:
            seen.add(v)
            opts.append(v)

    if shuffle:
        opts, correct_idx = _shuffle_with_correct([str(o) for o in opts], str(correct))
    else:
        opts = sorted(opts, reverse=True)
        correct_idx = opts.index(correct) + 1
        opts = [str(o) for o in opts]

    return Question(
        structure_id="digit_value_mcq",
        topic="place_value",
        section="A",
        marks=1,
        text=f"What is the value of the digit {digit} in {number}?",
        options=opts,
        correct_option=correct_idx,
        answer=str(correct),
        working=f"Digit {digit} is in the {'ones tens hundreds thousands'.split()[digit_position]} place → {digit} × {pv} = {correct}",
    )


def gen_expanded_form_mcq(
    number: int,
    missing_position: int,
    shuffle: bool = False,
) -> Question:
    """
    Q2 structure — fill the blank in an expanded-form equation.
    e.g. "5207 = 5 thousands + _____ + 7 ones"
    Distractor pattern: shifted_and_stripped_grid
    """
    place_names = ["ones", "tens", "hundreds", "thousands"]
    digits = [(number // (10 ** p)) % 10 for p in range(4)]

    # Build parts of the expanded form, hiding the target
    parts = []
    for p in range(3, -1, -1):  # thousands to ones
        d = digits[p]
        if d == 0:
            continue
        if p == missing_position:
            parts.append("_____")
        else:
            parts.append(f"{d} {place_names[p]}")

    digit = digits[missing_position]
    pv = 10 ** missing_position
    correct = digit * pv

    raw = [digit * pv * 10, digit, correct, digit * pv // 10 if pv >= 10 else digit]
    seen: set[int] = set()
    opts: list[int] = []
    for v in raw:
        if v not in seen:
            seen.add(v)
            opts.append(v)

    if shuffle:
        opts, correct_idx = _shuffle_with_correct([str(o) for o in opts], str(correct))
    else:
        opts = sorted(opts, reverse=True)
        correct_idx = opts.index(correct) + 1
        opts = [str(o) for o in opts]

    eq = " + ".join(parts)
    return Question(
        structure_id="expanded_form_mcq",
        topic="place_value",
        section="A",
        marks=1,
        text=f"{number} = {eq}",
        options=opts,
        correct_option=correct_idx,
        answer=str(correct),
        working=f"The missing part is the {place_names[missing_position]}s: {digit} × {pv} = {correct}",
    )


def gen_money_multi_item_mcq(
    n1: int, price1_cents: int,
    n2: int, price2_cents: int,
    item_type: str = "stamps",
    shuffle: bool = False,
) -> Question:
    """
    Q3 structure — total cost of two groups of items at different cent prices.
    Distractors: adds_quantities_wrong_unit, quantity_as_dollars,
                 concatenates_quantities_and_denominations
    """
    correct_cents = n1 * price1_cents + n2 * price2_cents
    correct = _cents_to_dollars(correct_cents)

    qty_sum = n1 + n2
    price_sum = price1_cents + price2_cents

    d1 = _cents_to_dollars(qty_sum * 10)            # (n1+n2) × 10¢
    d2 = f"${n1}.{price2_cents:02d}"                 # n1 as dollars + price2 as cents
    d3 = f"${qty_sum}.{price_sum:02d}"               # concatenate sums

    raw = [d1, correct, d2, d3]
    seen: set[str] = set()
    opts: list[str] = []
    for v in raw:
        if v not in seen:
            seen.add(v)
            opts.append(v)

    if shuffle:
        opts, correct_idx = _shuffle_with_correct(opts, correct)
    else:
        correct_idx = opts.index(correct) + 1

    return Question(
        structure_id="money_multi_item_mcq",
        topic="money",
        section="A",
        marks=2,
        text=(f"What is the total cost of {n1} {price1_cents}-cent {item_type} "
              f"and {n2} {price2_cents}-cent {item_type}?"),
        options=opts,
        correct_option=correct_idx,
        answer=correct,
        working=(f"{n1} × {price1_cents}¢ = {n1*price1_cents}¢,  "
                 f"{n2} × {price2_cents}¢ = {n2*price2_cents}¢,  "
                 f"total = {correct_cents}¢ = {correct}"),
    )


def gen_number_pattern_mcq(
    start: int,
    diff: int,
    shuffle: bool = False,
) -> Question:
    """
    Q4 structure — fill two consecutive blanks in an arithmetic sequence.
    Sequence shown: start, start+d, ..., start+3d, __, __, start+6d
    Distractor pattern: wrong_common_difference (d−30, d−20, d−10)
    """
    seq = [start + i * diff for i in range(7)]
    visible = seq[:4] + ["_____", "_____", seq[6]]
    seq_str = ",  ".join(str(x) for x in visible)

    correct = (seq[4], seq[5])

    options_raw = [
        (start + 4*(diff-30), start + 5*(diff-30)),
        (start + 4*(diff-20), start + 5*(diff-20)),
        (start + 4*(diff-10), start + 5*(diff-10)),
        correct,
    ]
    # Remove any duplicates
    seen: set = set()
    opts: list = []
    for pair in options_raw:
        if pair not in seen:
            seen.add(pair)
            opts.append(pair)

    if shuffle:
        random.shuffle(opts)

    opts_str = [f"{a},  {b}" for a, b in opts]
    correct_str = f"{correct[0]},  {correct[1]}"
    correct_idx = opts_str.index(correct_str) + 1

    return Question(
        structure_id="number_pattern_missing_mcq",
        topic="number_patterns",
        section="A",
        marks=2,
        text=f"What are the missing numbers in the number pattern?\n{seq_str}",
        options=opts_str,
        correct_option=correct_idx,
        answer=correct_str,
        working=f"Common difference = {diff}; blanks = {seq[4]}, {seq[5]}",
    )


def gen_sum_difference_mcq(
    total: int,
    a: int,
    shuffle: bool = False,
) -> Question:
    """
    Q5 structure — given sum and one number, find the difference.
    Distractors: intermediate result, wrong operation, compound errors
    """
    b = total - a          # the other number (b > a by construction)
    correct = b - a        # the difference

    d_intermediate = b                 # stops after step 1
    d_wrong_op     = total + a         # adds instead of subtracts
    d_compound     = total + 2 * a     # chains two wrong additions

    opts_raw = [correct, d_intermediate, d_wrong_op, d_compound]
    seen: set[int] = set()
    opts: list[int] = []
    for v in opts_raw:
        if v not in seen:
            seen.add(v)
            opts.append(v)

    opts_str = [str(o) for o in opts]
    correct_str = str(correct)

    if shuffle:
        opts_str, correct_idx = _shuffle_with_correct(opts_str, correct_str)
    else:
        correct_idx = opts_str.index(correct_str) + 1

    return Question(
        structure_id="two_number_sum_difference_mcq",
        topic="addition_subtraction",
        section="A",
        marks=2,
        text=(f"The sum of two numbers is {total}. "
              f"One of the numbers is {a}. "
              f"What is the difference between the 2 numbers?"),
        options=opts_str,
        correct_option=correct_idx,
        answer=correct_str,
        working=f"Other number = {total} − {a} = {b};  Difference = {b} − {a} = {correct}",
    )


# ── Section B: Short-answer generators ────────────────────────────────────────

def gen_ordering(
    numbers: list[int],
    direction: str = "decreasing",
) -> Question:
    """Q6 structure — arrange numbers in ascending or descending order."""
    sorted_nums = sorted(numbers, reverse=(direction == "decreasing"))
    answer = ",  ".join(str(n) for n in sorted_nums)
    return Question(
        structure_id="ordering_numbers_short",
        topic="ordering_numbers",
        section="B",
        marks=1,
        text=f"Arrange the following numbers in {direction} order.\n{',  '.join(str(n) for n in numbers)}",
        options=None,
        answer=answer,
    )


def gen_direct_addition(a: int, b: int) -> Question:
    """Q7 structure — find the sum of two numbers."""
    return Question(
        structure_id="direct_addition_short",
        topic="addition_subtraction",
        section="B",
        marks=1,
        text=f"Find the sum of {a} and {b}.",
        options=None,
        answer=str(a + b),
        working=f"{a} + {b} = {a + b}",
    )


def gen_missing_digit_subtraction(
    minuend: int,
    subtrahend: int,
    hidden_position: int,
) -> Question:
    """
    Q8 structure — vertical subtraction with one digit of the minuend hidden.
    Student recovers the minuend via addition, then reads off the hidden digit.
    """
    difference = minuend - subtrahend
    hidden_digit = _extract_digit(minuend, hidden_position)
    masked = str(minuend)
    pos_from_left = len(masked) - 1 - hidden_position
    masked = masked[:pos_from_left] + "?" + masked[pos_from_left + 1:]

    return Question(
        structure_id="missing_digit_vertical_subtraction",
        topic="addition_subtraction",
        section="B",
        marks=2,
        text=(f"What is the missing number in the box?\n"
              f"  {masked}\n"
              f"−   {subtrahend}\n"
              f"  {difference}"),
        options=None,
        answer=str(hidden_digit),
        working=f"minuend = {difference} + {subtrahend} = {minuend};  hidden digit = {hidden_digit}",
    )


def gen_money_change(
    item1_name: str, price1: float,
    item2_name: str, price2: float,
    paid: float,
    buyer: str = "She",
) -> Question:
    """Q9 structure — change from a two-item purchase."""
    total_cost = round(price1 + price2, 2)
    change = round(paid - total_cost, 2)
    return Question(
        structure_id="money_change_from_purchase",
        topic="money",
        section="B",
        marks=2,
        text=(f"{buyer} bought {item1_name} (${price1:.2f}) and {item2_name} (${price2:.2f}). "
              f"{buyer} gave the cashier ${paid:.2f}. How much change did {buyer} receive?"),
        options=None,
        answer=f"${change:.2f}",
        working=(f"Total cost = ${price1:.2f} + ${price2:.2f} = ${total_cost:.2f};  "
                 f"Change = ${paid:.2f} − ${total_cost:.2f} = ${change:.2f}"),
    )


def gen_money_budget(
    menu: list[dict],
    budget: float,
    buyer: str = "She",
    item_type: str = "dish",
) -> Question:
    """
    Q10 structure — find a valid pair of items within a budget (open-ended).
    Returns all valid pairs in the answer field.
    """
    valid_pairs = []
    for i in range(len(menu)):
        for j in range(i + 1, len(menu)):
            total = round(menu[i]["price"] + menu[j]["price"], 2)
            if total <= budget:
                valid_pairs.append({
                    "items": (menu[i]["name"], menu[j]["name"]),
                    "total": total,
                })

    menu_str = "\n".join(f"  {m['name']}: ${m['price']:.2f}" for m in menu)
    answer_str = "; OR ".join(
        f"{p['items'][0]} + {p['items'][1]} = ${p['total']:.2f}"
        for p in valid_pairs
    )
    return Question(
        structure_id="money_budget_open_ended",
        topic="money",
        section="B",
        marks=2,
        text=(f"{buyer} had ${budget:.2f}. {buyer} bought two different {item_type}es. "
              f"Which two possible {item_type}es could {buyer} buy?\n{menu_str}"),
        options=None,
        answer=f"Any valid pair: {answer_str}",
    )


# ── Section C: Long-answer generators ─────────────────────────────────────────

def gen_diff_find_sum(diff: int, smaller: int) -> Question:
    """Q11 structure — given difference and smaller, find the sum."""
    larger = smaller + diff
    total = smaller + larger
    return Question(
        structure_id="two_number_difference_find_sum",
        topic="addition_subtraction",
        section="C",
        marks=3,
        text=(f"The difference between two numbers is {diff}. "
              f"The smaller number is {smaller}. "
              f"Find the sum of the two numbers."),
        options=None,
        answer=str(total),
        working=f"Larger = {smaller} + {diff} = {larger};  Sum = {smaller} + {larger} = {total}",
    )


def gen_money_comparison_total(
    item1: str, price1: float,
    item2: str, less: float,
    buyer: str = "She",
) -> Question:
    """Q12 structure — item2 costs 'less' dollars less than item1; find combined total."""
    price2 = round(price1 - less, 2)
    total = round(price1 + price2, 2)
    return Question(
        structure_id="money_comparison_total",
        topic="money",
        section="C",
        marks=3,
        text=(f"{buyer} bought a {item1} for ${price1:.2f}. "
              f"{buyer} also bought a {item2} that cost ${less:.2f} less than the {item1}. "
              f"How much money did {buyer} spend altogether?"),
        options=None,
        answer=f"${total:.2f}",
        working=(f"{item2} = ${price1:.2f} − ${less:.2f} = ${price2:.2f};  "
                 f"Total = ${price1:.2f} + ${price2:.2f} = ${total:.2f}"),
    )


def gen_money_sale_savings(
    item: str,
    unit_price: float,
    n: int,
    sale_price: float,
    buyer: str = "She",
) -> Question:
    """Q13 structure — savings when buying n items at a sale price."""
    normal_total = round(n * unit_price, 2)
    savings = round(normal_total - sale_price, 2)
    return Question(
        structure_id="money_sale_savings",
        topic="money",
        section="C",
        marks=3,
        text=(f"A {item} usually costs ${unit_price:.2f}. "
              f"{buyer} bought {n} {item}s for ${sale_price:.2f} during a sale. "
              f"How much money did {buyer} save altogether?"),
        options=None,
        answer=f"${savings:.2f}",
        working=(f"Normal total = {n} × ${unit_price:.2f} = ${normal_total:.2f};  "
                 f"Savings = ${normal_total:.2f} − ${sale_price:.2f} = ${savings:.2f}"),
    )


# ── Section A: New MCQ generators (WA2 topics) ───────────────────────────────

_SINGULAR = {
    "bags": "bag", "boxes": "box", "packets": "packet", "baskets": "basket",
    "trays": "tray", "containers": "container", "bottles": "bottle",
    "jars": "jar", "tins": "tin", "plates": "plate", "cups": "cup",
}

def _singular(word: str) -> str:
    """Return singular form of a container word."""
    return _SINGULAR.get(word, word.rstrip("s"))


def _repeated_addition_str(value: int, count: int) -> str:
    """e.g. value=6, count=7 → '6 + 6 + 6 + 6 + 6 + 6 + 6'"""
    return " + ".join([str(value)] * count)

def _repeated_mult_str(value: int, count: int) -> str:
    """e.g. value=6, count=7 → '6 × 6 × 6 × 6 × 6 × 6 × 6'"""
    return " × ".join([str(value)] * count)


def gen_multiplication_repeated_addition_mcq(
    a: int,
    b: int,
    shuffle: bool = True,
) -> Question:
    """
    "a × b is the same as ___."
    Convention: a × b = b added a times  (e.g. 6 × 7 → 6+6+6+6+6+6+6)
    Distractors:
      d1 — b × b × … (a times)   wrong operation, correct base
      d2 — a + a + … (b times)   correct operation, reversed addend
      d3 — a × a × … (b times)   wrong operation AND reversed base
    """
    correct = _repeated_addition_str(b, a)   # b added a times
    d1 = _repeated_mult_str(b, a)            # power-style, correct base
    d2 = _repeated_addition_str(a, b)        # addition, reversed addend
    d3 = _repeated_mult_str(a, b)            # power-style, reversed

    # Deduplicate (e.g. if a == b, correct == d2)
    seen: set[str] = set()
    opts: list[str] = []
    for o in [correct, d1, d2, d3]:
        if o not in seen:
            seen.add(o)
            opts.append(o)

    if shuffle:
        opts, correct_idx = _shuffle_with_correct(opts, correct)
    else:
        correct_idx = opts.index(correct) + 1

    return Question(
        structure_id="multiplication_as_repeated_addition_mcq",
        topic="multiplication",
        section="A",
        marks=1,
        text=f"{a} × {b} is the same as ___.",
        options=opts,
        correct_option=correct_idx,
        answer=correct,
        working=f"{a} × {b} means {b} added {a} times = {a * b}",
    )


# ── Section B: New short-answer generators (WA2 topics) ──────────────────────

def gen_equal_groups_division(
    total: int,
    per_group: int,
    item: str = "apples",
    container: str = "bags",
    name: str = "Ali",
) -> Question:
    """
    "Ali packed 56 apples into bags. 7 apples per bag. How many bags?"
    total must divide evenly by per_group (use gen_division_round_up for remainders).
    """
    if total % per_group != 0:
        raise ValueError(f"{total} does not divide evenly by {per_group}. "
                         "Use gen_division_round_up for problems with remainders.")
    groups = total // per_group
    return Question(
        structure_id="equal_groups_division_word_problem",
        topic="division",
        section="B",
        marks=1,
        text=(f"{name} packed {total} {item} into {container}. "
              f"There were {per_group} {item} in each {_singular(container)}. "
              f"How many {container} were there?"),
        options=None,
        answer=str(groups),
        working=f"{total} ÷ {per_group} = {groups}",
    )


def gen_division_round_up(
    total: int,
    per_container: int,
    item: str = "curry puffs",
    container: str = "containers",
    name: str = "Liming",
) -> Question:
    """
    "Liming has 65 curry puffs. Packs 9 per container. How many containers needed?"
    Key: if there is a remainder, one extra container is required (ceiling division).
    Distractor: floor quotient (most common error — ignores the remainder).
    """
    quotient, remainder = divmod(total, per_container)
    answer = quotient + (1 if remainder > 0 else 0)
    if remainder > 0:
        working = (f"{total} ÷ {per_container} = {quotient} remainder {remainder}; "
                   f"remainder > 0 → need 1 extra {_singular(container)} → {answer}")
    else:
        working = f"{total} ÷ {per_container} = {answer} (exact)"
    return Question(
        structure_id="division_with_remainder_round_up_word_problem",
        topic="division",
        section="B",
        marks=2,
        text=(f"{name} had {total} {item}. "
              f"{name} packed {per_container} {item} in each {_singular(container)}. "
              f"How many {container} did {name} need to pack all the {item}?"),
        options=None,
        answer=str(answer),
        working=working,
    )


def gen_reverse_division(
    divisor: int,
    quotient: int,
    remainder: int,
) -> Question:
    """
    "When a number is divided by {d}, the quotient is {q} and the remainder is {r}. Find the number."
    Answer: d × q + r
    Common error: students give just d × q (forget to add the remainder).
    """
    if remainder >= divisor:
        raise ValueError(f"remainder ({remainder}) must be less than divisor ({divisor}).")
    dividend = divisor * quotient + remainder
    return Question(
        structure_id="reverse_division_find_dividend",
        topic="division",
        section="B",
        marks=2,
        text=(f"When a number is divided by {divisor}, "
              f"the quotient is {quotient} and the remainder is {remainder}. "
              f"What is the number?"),
        options=None,
        answer=str(dividend),
        working=(f"{divisor} × {quotient} = {divisor * quotient};  "
                 f"{divisor * quotient} + {remainder} = {dividend}"),
    )


def _fraction_str(num: int, den: int) -> str:
    """Return simplified fraction string, e.g. '1/2' or '1' (if den becomes 1)."""
    g = math.gcd(num, den)
    n, d = num // g, den // g
    return str(n) if d == 1 else f"{n}/{d}"


def gen_fraction_simplification(
    numerator: int,
    denominator: int,
) -> Question:
    """
    "Write {num}/{den} in its simplest form."
    The fraction should not already be in simplest form (GCD > 1).
    """
    g = math.gcd(numerator, denominator)
    if g == 1:
        raise ValueError(f"{numerator}/{denominator} is already in simplest form. "
                         "Choose a fraction with GCF > 1.")
    answer = _fraction_str(numerator, denominator)
    return Question(
        structure_id="fraction_simplification",
        topic="fractions",
        section="B",
        marks=2,
        text=f"Write {numerator}/{denominator} in its simplest form.",
        options=None,
        answer=answer,
        working=(f"GCF({numerator}, {denominator}) = {g};  "
                 f"{numerator} ÷ {g} = {numerator // g},  "
                 f"{denominator} ÷ {g} = {denominator // g}  →  {answer}"),
    )


def gen_fraction_addition(
    num1: int, den1: int,
    num2: int, den2: int,
) -> Question:
    """
    "Find the sum of {num1}/{den1} and {num2}/{den2}. Express in simplest form."
    P3 level: one denominator is typically a multiple of the other.
    Result is simplified automatically; mixed-number form used if > 1.
    """
    lcm_den = den1 * den2 // math.gcd(den1, den2)
    result_num = num1 * (lcm_den // den1) + num2 * (lcm_den // den2)

    # Build working string before simplification
    n1_conv = num1 * (lcm_den // den1)
    n2_conv = num2 * (lcm_den // den2)

    whole = result_num // lcm_den
    frac_num = result_num % lcm_den
    g = math.gcd(frac_num, lcm_den) if frac_num else 1

    if whole > 0 and frac_num > 0:
        answer = f"{whole} {frac_num // g}/{lcm_den // g}"
    elif whole > 0:
        answer = str(whole)
    else:
        answer = _fraction_str(result_num, lcm_den)

    working = (f"{num1}/{den1} = {n1_conv}/{lcm_den};  "
               f"{num2}/{den2} = {n2_conv}/{lcm_den};  "
               f"Sum = {n1_conv + n2_conv}/{lcm_den} = {answer}")

    return Question(
        structure_id="fraction_addition_unlike_denominators",
        topic="fractions",
        section="B",
        marks=2,
        text=(f"Find the sum of {num1}/{den1} and {num2}/{den2}. "
              f"Express your answer in the simplest form."),
        options=None,
        answer=answer,
        working=working,
    )


# ── Batch helper ──────────────────────────────────────────────────────────────

def _rand_related_fraction_pair():
    """Generate two fractions with related denominators (one divides the other) for P3."""
    pairs = [
        (1, 5, 3, 10), (2, 5, 1, 10), (1, 4, 1, 2), (1, 3, 1, 6),
        (2, 3, 1, 6),  (3, 4, 1, 8),  (1, 2, 1, 4), (3, 5, 1, 10),
        (1, 4, 3, 8),  (1, 3, 1, 9),  (2, 9, 1, 3), (1, 6, 1, 3),
    ]
    # Filter to pairs where result ≤ 1 for simplicity
    valid = [(n1, d1, n2, d2) for n1, d1, n2, d2 in pairs
             if n1 * d2 + n2 * d1 <= d1 * d2]
    return random.choice(valid if valid else pairs)


# ── Random-parameter helpers (used by _RANDOM_GENERATORS) ─────────────────────

def _rand_expanded_form() -> Question:
    """Generate expanded_form_mcq ensuring the target digit is non-zero."""
    while True:
        num = random.randint(1000, 9999)
        pos = random.choice([1, 2, 3])
        if (num // (10 ** pos)) % 10 != 0:
            return gen_expanded_form_mcq(num, pos, shuffle=True)


def _rand_ordering() -> Question:
    nums = random.sample(range(1000, 9999), 4)
    return gen_ordering(nums, random.choice(["increasing", "decreasing"]))


def _rand_money_change() -> Question:
    items = ["a book", "a ruler", "an eraser", "a pen",
             "a notebook", "a pencil case", "a sharpener"]
    p1 = random.randint(50, 800)   # cents
    p2 = random.randint(50, 800)   # cents
    paid_c = next(p for p in [500, 1000, 2000, 5000] if p > p1 + p2)
    i1 = random.choice(items)
    i2 = random.choice([x for x in items if x != i1])
    return gen_money_change(
        i1, p1 / 100,
        i2, p2 / 100,
        paid_c / 100,
        random.choice(["She", "He"]),
    )


_RANDOM_GENERATORS = {
    "digit_value_mcq": lambda: gen_digit_value_mcq(
        random.randint(1000, 9999),
        random.randint(0, 3),
        shuffle=True,
    ),
    "direct_addition_short": lambda: gen_direct_addition(
        random.randint(1000, 5999),
        random.randint(100, 4000),
    ),
    "diff_find_sum": lambda: gen_diff_find_sum(
        random.randint(50, 500),
        random.randint(100, 499),
    ),
    "money_sale_savings": lambda: gen_money_sale_savings(
        random.choice(["bag", "book", "toy", "pen"]),
        round(random.uniform(10, 200), 2),
        random.randint(2, 5),
        round(random.uniform(5, 300), 2),
    ),
    "multiplication_as_repeated_addition_mcq": lambda: (
        lambda a, b: gen_multiplication_repeated_addition_mcq(a, b, shuffle=True)
    )(random.randint(2, 9), random.randint(2, 9)),
    "equal_groups_division_word_problem": lambda: (
        lambda d, q: gen_equal_groups_division(
            total=d * q,
            per_group=d,
            item=random.choice(["apples", "stickers", "sweets", "books", "cookies"]),
            container=random.choice(["bags", "boxes", "baskets", "packets"]),
            name=random.choice(["Ali", "Siti", "Ravi", "Mrs Lee", "Tom"]),
        )
    )(random.randint(3, 9), random.randint(3, 12)),
    "division_with_remainder_round_up_word_problem": lambda: (
        lambda d, q, r: gen_division_round_up(
            total=d * q + r,
            per_container=d,
            item=random.choice(["cupcakes", "muffins", "eggs", "biscuits", "pens"]),
            container=random.choice(["boxes", "bags", "packets", "trays"]),
            name=random.choice(["Lily", "Ben", "Ahmad", "Mrs Tan", "Priya"]),
        )
    )(random.randint(4, 9), random.randint(5, 15), random.randint(1, 8)),
    "reverse_division_find_dividend": lambda: (
        lambda d, q, r: gen_reverse_division(d, q, r)
    )(random.randint(3, 9), random.randint(10, 50), random.randint(1, 8)),
    "fraction_simplification": lambda: (
        lambda n, g: gen_fraction_simplification(n * g, random.choice([2, 3, 4, 5, 6]) * g)
    )(random.randint(1, 6), random.choice([2, 3, 4, 5, 6, 7])),
    "fraction_addition_unlike_denominators": lambda: (
        lambda t: gen_fraction_addition(t[0], t[1], t[2], t[3])
    )(_rand_related_fraction_pair()),
    # ── WA1 generators (added for web app) ──────────────────────────────────
    "expanded_form_mcq": _rand_expanded_form,
    "number_pattern_missing_mcq": lambda: gen_number_pattern_mcq(
        random.randint(1000, 4000),
        random.choice([30, 40, 50, 60, 100, 200]),
        shuffle=True,
    ),
    "two_number_sum_difference_mcq": lambda: (
        lambda total: gen_sum_difference_mcq(
            total, random.randint(100, total // 2 - 1), shuffle=True
        )
    )(random.randint(2000, 8000)),
    "money_multi_item_mcq": lambda: gen_money_multi_item_mcq(
        random.randint(3, 9), random.choice([5, 10, 20, 25, 30, 50]),
        random.randint(3, 9), random.choice([5, 10, 20, 25, 30, 50]),
        random.choice(["stamps", "stickers", "sweets", "erasers"]),
        shuffle=True,
    ),
    "money_change_from_purchase": _rand_money_change,
    "ordering_numbers_short": _rand_ordering,
}

def generate_batch(structure_id: str, n: int) -> list[Question]:
    """Generate n random questions of the given structure."""
    gen = _RANDOM_GENERATORS.get(structure_id)
    if gen is None:
        raise ValueError(f"No random generator registered for '{structure_id}'. "
                         f"Available: {list(_RANDOM_GENERATORS)}")
    return [gen() for _ in range(n)]


# ── Demo: reproduce all 13 source questions ───────────────────────────────────

def demo_all_source_questions() -> list[Question]:
    menu = [
        {"name": "Nasi Lemak",        "price": 7.80},
        {"name": "Fried Hokkien Mee", "price": 10.50},
        {"name": "Laksa",             "price": 9.40},
        {"name": "Fishball Noodles",  "price": 7.30},
        {"name": "Fried Rice",        "price": 8.50},
    ]
    return [
        gen_digit_value_mcq(3875, digit_position=1),                          # Q1
        gen_expanded_form_mcq(5207, missing_position=2),                      # Q2
        gen_money_multi_item_mcq(8, 20, 7, 50, item_type="stamps"),           # Q3
        gen_number_pattern_mcq(3448, diff=40),                                # Q4
        gen_sum_difference_mcq(total=3480, a=1207),                           # Q5
        gen_ordering([4098, 4890, 4089], direction="decreasing"),             # Q6
        gen_direct_addition(5999, 201),                                       # Q7
        gen_missing_digit_subtraction(3501, 1473, hidden_position=2),         # Q8
        gen_money_change("Nasi Lemak", 7.80, "Laksa", 9.40, paid=20.00,
                         buyer="Gerry"),                                      # Q9
        gen_money_budget(menu, budget=16.00, buyer="Faith"),                  # Q10
        gen_diff_find_sum(diff=198, smaller=257),                             # Q11
        gen_money_comparison_total("handbag", 85.20, "coin pouch", 24.80,
                                   buyer="Joan"),                             # Q12
        gen_money_sale_savings("watch", 176.20, 2, 305.50, buyer="Annie"),   # Q13
    ]


def demo_new_generators() -> list[Question]:
    """Show one example of each Priority 1 generator added in v0.3."""
    return [
        gen_multiplication_repeated_addition_mcq(6, 7),            # 6×7
        gen_multiplication_repeated_addition_mcq(4, 3),            # 4×3
        gen_equal_groups_division(56, 7, "apples", "bags", "Aini"),
        gen_division_round_up(65, 9, "curry puffs", "containers", "Liming"),
        gen_division_round_up(79, 6, "cookies", "boxes", "Siti"),
        gen_reverse_division(4, 36, 2),                            # ACS Jr WA2 Q9
        gen_reverse_division(3, 46, 2),                            # Ai Tong WA2 Q10
        gen_fraction_simplification(14, 42),                       # 14/42 → 1/3
        gen_fraction_simplification(4, 16),                        # 4/16 → 1/4
        gen_fraction_addition(1, 5, 3, 10),                        # 1/5 + 3/10
        gen_fraction_addition(1, 4, 1, 2),                         # 1/4 + 1/2
    ]


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "source"

    if mode == "new":
        print("=== Priority 1 generators (v0.3) ===\n")
        for i, q in enumerate(demo_new_generators(), 1):
            print(f"Q{i}.", end="  ")
            q.display(show_answer=True)
    elif mode == "batch":
        struct = sys.argv[2] if len(sys.argv) > 2 else "multiplication_as_repeated_addition_mcq"
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print(f"=== Batch: {n} × {struct} ===\n")
        for i, q in enumerate(generate_batch(struct, n), 1):
            print(f"Q{i}.", end="  ")
            q.display(show_answer=True)
    else:
        print("=== Original 13 source questions ===\n")
        for i, q in enumerate(demo_all_source_questions(), 1):
            print(f"Q{i}.", end="  ")
            q.display(show_answer=True)
