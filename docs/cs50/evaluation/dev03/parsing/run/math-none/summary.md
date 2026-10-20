# Formula reconstruction evaluation v1

Offline evaluation harness; synthetic examples are not model quality measurements.

Input SHA-256: `2d7c5bb2f4c54508ff2436ff14fe81f9737930be77139ae9d650cc2e6184b836`
Equivalence backend: `none`

Exact/normalized rates use paired_count: confirmed gold and a present prediction, neither marked ambiguous; includes unsupported notation. Null means a zero denominator.
Evaluable means a decided reconstruction status; it includes missing/extra formulas and explicit partial reconstructions. Symbolic identity is separate from notation identity.

| Gold origin | Cases | Evaluable | Paired | Exact rate | Normalized rate | Structural matches/comparable | Equivalent | Via SymPy | Undetermined |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic | 42 | 17 | 37 | 0.2703 | 0.3243 | 12/33 | 12 | 0 | 25 |
| real | 0 | 0 | 0 | n/a | n/a | 0/0 | 0 | 0 | 0 |

## Error category counts

| Gold origin | Category | Count |
|---|---|---:|
| synthetic | ambiguous_source | 2 |
| synthetic | exponent_error | 8 |
| synthetic | extra_formula | 1 |
| synthetic | format_error | 2 |
| synthetic | fraction_error | 3 |
| synthetic | missing_formula | 1 |
| synthetic | not_evaluable | 25 |
| synthetic | operator_error | 10 |
| synthetic | structure_error | 21 |
| synthetic | subscript_error | 2 |
| synthetic | symbol_error | 17 |

## Cases requiring review

| Case | Status | Source | Categories | Decision |
|---|---|---|---|---|
| M03 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G01; page=None; section=G01 | not_evaluable, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M04 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G01; page=None; section=G01 | not_evaluable, operator_error, structure_error | symbolic_check_not_requested |
| M06 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G02; page=None; section=G02 | exponent_error, not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M08 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G04; page=None; section=G04 | not_evaluable, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M09 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G04; page=None; section=G04 | not_evaluable, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M10 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G05; page=None; section=G05 | exponent_error, not_evaluable, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M11 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G05; page=None; section=G05 | not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M13 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G06; page=None; section=G06 | fraction_error, not_evaluable, operator_error, structure_error | symbolic_check_not_requested |
| M15 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G07; page=None; section=G07 | fraction_error, not_evaluable, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M16 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G08; page=None; section=G08 | exponent_error, not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M17 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G09; page=None; section=G09 | exponent_error, not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M18 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G10; page=None; section=G10 | not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M19 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G11; page=None; section=G11 | exponent_error, not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M21 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G12; page=None; section=G12 | exponent_error, not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M23 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G13; page=None; section=G13 | exponent_error, not_evaluable, operator_error, structure_error, subscript_error, symbol_error | symbolic_check_not_requested |
| M25 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G14; page=None; section=G14 | not_evaluable, structure_error | symbolic_check_not_requested |
| M27 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G15; page=None; section=G15 | not_evaluable, structure_error, subscript_error, symbol_error | symbolic_check_not_requested |
| M29 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G17; page=None; section=G17 | not_evaluable, structure_error, symbol_error | symbolic_check_not_requested |
| M32 | extra_formula | docs/math_evaluation/gold_references.v1.json#/references/G19; page=None; section=G19 | extra_formula | no_comparable_formula_pair |
| M33 | missing_formula | docs/math_evaluation/gold_references.v1.json#/references/G01; page=None; section=G01 | missing_formula | no_comparable_formula_pair |
| M34 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G20; page=None; section=G20 | ambiguous_source, not_evaluable | no_comparable_formula_pair |
| M35 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G21; page=None; section=G21 | not_evaluable | no_comparable_formula_pair |
| M36 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G22; page=None; section=G22 | not_evaluable | no_comparable_formula_pair |
| M37 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G06; page=None; section=G06 | format_error, not_evaluable | no_comparable_formula_pair |
| M38 | partially_correct | docs/math_evaluation/gold_references.v1.json#/references/G06; page=None; section=G06 | fraction_error, operator_error, structure_error, symbol_error | symbolic_check_not_requested |
| M39 | partially_correct | docs/math_evaluation/gold_references.v1.json#/references/G23; page=None; section=G23 | exponent_error, structure_error, symbol_error | symbolic_check_not_requested |
| M40 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G24; page=None; section=G24 | not_evaluable, operator_error, structure_error | symbolic_check_not_requested |
| M41 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G25; page=None; section=G25 | format_error, not_evaluable | no_comparable_formula_pair |
| M42 | undetermined | docs/math_evaluation/gold_references.v1.json#/references/G24; page=None; section=G24 | ambiguous_source, not_evaluable | no_comparable_formula_pair |
