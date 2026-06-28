# P3 Maths Question Bank — Taxonomy Update Summary
**Version 0.3 | 23 papers analysed | Updated 2026-06-27**

---

## What Changed in This Update

The taxonomy grew from covering 13 questions across 1 paper (ACS Junior WA1) to cataloguing the full P3 assessment landscape across 23 papers.

---

## Papers Processed (21 new)

| Assessment | Schools |
|---|---|
| **WA1** (Term 1) | Henry Park, Nan Hua, Nanyang, Raffles Girls, Rosyth, Tao Nan |
| **WA2** (Term 2) | ACS Junior, Ai Tong, Henry Park, Maha Bodhi, Nan Hua, Nanyang, Northland, Raffles Girls, Rosyth, St Hilda, Tao Nan |
| **WA3** (Term 3) | ACS Junior, Ai Tong, Nan Hua, Rosyth |

---

## Topic Coverage by Assessment Period

### WA1 — Term 1 Topics
Every WA1 paper tests the same core syllabus: **place value** (the dominant topic, ~30% of marks), **addition/subtraction**, **money**, **number patterns**, and **ordering numbers**. A few schools extend to fractions (Henry Park), time (Tao Nan), measurement, multiplication and odd/even.

### WA2 — Term 2 Topics (New this update)
WA2 papers introduce a completely different topic set:
- **Multiplication** — multiplication tables, equal groups, repeated addition, 3-digit × 1-digit, multiplicative comparison
- **Division** — exact, with remainder, ceiling division, reverse division
- **Fractions** — equivalent fractions, ordering, simplification, addition/subtraction
- **Geometry: Angles** — identifying and counting acute/obtuse/right angles
- **Geometry: Lines** — parallel and perpendicular, drawing on grids
- **Data: Bar Graphs** — single and grouped bars, reading, comparing, drawing, true/false

### WA3 — Term 3 Topics (Partial data)
From preliminary reading: fractions continue to appear, alongside measurement (mass, volume) and time. Full catalogue pending deeper read.

---

## Taxonomy Growth

| Section | v0.2 (before) | v0.3 (now) |
|---|---|---|
| Topics | 5 | **15** |
| Question structures | 13 | **80** |
| Distractor patterns | 3 | **6** |
| Distractor types | 14 | **19** |
| Misconceptions | 12 | **17** |

---

## New Topics Added

1. **multiplication** — tables, equal groups, comparison, chain problems
2. **division** — sharing, grouping, remainder, ceiling, reverse
3. **fractions** — equivalent, ordering, simplification, operations
4. **geometry_angles** — acute, obtuse, right; count and identify
5. **geometry_lines** — parallel, perpendicular; identify and draw
6. **data_graphs** — single and grouped bar charts; full suite of sub-skills
7. **time** — clock reading, unit conversion, elapsed time
8. **measurement_mass** — scale reading
9. **measurement_volume** — counting containers
10. **odd_even** — parity constraints, digit-based number formation

---

## Key Structural Insights

### Question structure patterns across schools

**Every WA1 paper** tests: digit value MCQ, expanded form, ordering, number patterns, money word problems, addition/subtraction.

**Every WA2 paper** tests: multiplication/division (always ~40% of marks), bar graphs (2–4 questions per paper), fractions (HP and Maha Bodhi most heavily), geometry angles and lines (Ai Tong, HP, Maha Bodhi, Northland, Raffles Girls).

### Recurring structural templates (high-frequency)
These appear in 5+ papers and should be generator priority:
1. `digit_value_mcq` — appeared in every WA1 paper
2. `ordering_numbers_short` — every WA1 paper
3. `multiplication_as_repeated_addition_mcq` — every WA2 paper
4. `bar_graph_find_difference` — every WA2 paper
5. `division_with_remainder_round_up_word_problem` — every WA2 paper
6. `times_as_many_then_total_word_problem` — most WA2 papers

### Image-dependent questions
~25–30% of questions across all papers require an image (clock, scale, bar graph, geometry diagram, coins/notes, menu board, price tags). These cannot be auto-generated without visual assets. Flagged in taxonomy as `notes: "IMAGE ESSENTIAL"`.

### Novel/harder question types (appear in 1–2 papers only)
- `pictorial_algebra_system_of_equations` (Rosyth WA1 Q10 — fish/star/octopus puzzle)
- `calendar_reasoning_odd_even` (Nanyang WA2 Q7 — date from clues)
- `age_problem_sum_of_ages` (Tao Nan WA1 Q15 — sum + difference of ages)
- `combinations_counting_word_problem` (Nanyang WA1 Q8 — choose 2 from 4)
- `units_method_comparison_word_problem` (Nanyang WA2, Maha Bodhi WA2 — ratio method)
- `buy_n_get_k_free_promotion` (Ai Tong WA2 Q15 — promotional pricing)

---

## Generator Build Priority

Based on frequency and generatability (excludes image-dependent structures):

**Priority 1 — Build now:**
- `digit_value_mcq` ✅ (already built in `place_value_generator.py`)
- `expanded_form_mcq` ✅ (already in `generators.py`)
- `ordering_numbers_short`
- `number_pattern_missing_mcq`
- `multiplication_as_repeated_addition_mcq`
- `equal_groups_division_word_problem`
- `division_with_remainder_round_up_word_problem`
- `reverse_division_find_dividend`
- `fraction_addition_unlike_denominators`
- `fraction_simplification`

**Priority 2 — Build next:**
- `times_as_many_then_total_word_problem`
- `multiplicative_chain_word_problem`
- `units_method_comparison_word_problem`
- `two_step_subtract_then_add_word_problem`
- `ordering_fractions_ascending`
- `missing_fraction_in_equation`
- `buy_n_get_k_free_promotion`

**Priority 3 — Image-dependent (needs visual asset layer):**
- `bar_graph_read_single_value_mcq`
- `bar_graph_complete_given_relationship`
- `draw_perpendicular_on_grid`
- `draw_parallel_on_grid`
- `read_analogue_clock`
- `volume_counting_equal_containers_mcq`

---

## Files in This Project

| File | Description |
|---|---|
| `taxonomy.json` | Full taxonomy (v0.3) — all topics, structures, distractors, misconceptions |
| `generators.py` | Question generators for all 13 ACS Junior WA1 structures |
| `place_value_generator.py` | Standalone place value generator with 2×2 distractor pattern |
| `taxonomy_summary.md` | This file — human-readable summary |
