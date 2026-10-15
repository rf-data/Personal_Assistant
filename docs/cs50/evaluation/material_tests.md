# Material offline regression matrix

All new tests use portable temporary files or the checked-in SHA-verified HTML
snapshots. HTTP is fake. No external course fetch, parser model, LLM, code execution
or Qdrant upload. Existing Lecture/Transcript/Knowledge/index contracts are unchanged.

| Module | Cases | Evidence |
|---|---:|---|
| test_cs50_material_inventory | 1 | six graphs, all candidate IDs and raw snapshot occurrences; no HTTP |
| test_cs50_material_contracts | 4 | IDs/keys/JSON; URL/language/role conflicts |
| test_cs50_material_download | 18 | preview; archive/hash/resume; 404/429/5xx/redirect; MIME/size/empty; timeout/connect/read; partial stream; exclusive/atomic lost-ack resume; paths |
| test_cs50_material_html | 7 | structure, math/code/list/table/images, limits, roundtrip; five existing real Notes/assignment snapshots read-only |
| test_cs50_material_pdf | 7 | two-page own slide PDF/image/formula; corruption; page limit; actual timeout and descendant termination |
| test_cs50_material_code | 9 | UTF8/BOM, Python/SQL/HTML/Markdown exact lines; corrupt/empty/binary, encoded traversal, ZIP rejection |
| test_cs50_material_processing | 8 | 653 graph bindings/tasks; missing raw prerequisite; corrupt/config conflict; actual post-publication interruption; persisted parser failure; unsupported no-write |
| test_cs50_material_mapping | 1 | exact windows, identity/JSON, separate collection, no visual/math facts |
| test_cs50_material_e2e | 5 | real mixed lecture/Python/six scopes + SDK-free CLI help and separated release flags |

60 cases total. Initial pre-refinement combined run: 59 passed in 39.18 seconds.
After adding the real snapshot test and correcting its inventory count from the
actual manifest (three notes and two assignments), final totals are taken from
the complete suite, not summed overlapping focused runs.

Two preparation-test defects were found and corrected: a traversal URL was already
normalized by HttpUrl, so the actual encoded-separator attack is now tested;
SIGKILL delivery to descendants is asynchronous, so the test observes termination
within a bounded two-second deadline. The production process-group kill path was
not weakened. A temporary missing import during receipt-error implementation was
fixed before the final run. PyMuPDF diagnostics were isolated from its JSON channel.

Reproduction in the existing uv worker:

```bash
CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest tests/test_cs50_material_*.py -q
CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest tests -q \
  --basetemp=/tmp/new-exclusive-materials-tests --junitxml=/tmp/materials.xml
```

Use an external new scratch directory and the declared configured worker; a root
base-only environment lacks optional worker packages. No new packages/upgrades.
The inherited composed regression worker also supports isolated -I children;
see [existing environment notes](../operations/transcript_index_completion.md).
A fully fresh offline installation still depends on exact cached wheels, unchanged.
Final material block after all boundary corrections: **60 passed, 0 failed,
0 skipped, 0 setup errors in 72.99 seconds** (JUnit suite time 72.680 seconds).
An actual separate CLI smoke also verified preview → local synthetic import →
parse → resume → status, with byte-identical successful resume/status JSON and
no HTTP. Ruff check and format (21 Python files), git diff --check and all material
documentation relative-link checks pass.

The initial 581-case run on c2e31dd was explicitly interrupted after source review
found the boundary follow-ups. It is not counted as a completed regression result.
The authoritative full run uses a new isolated worktree at the frozen final source
commit; its exact hash and JUnit module counts are recorded in the final report.
Final focused source check: **60 passed in 53.73 seconds**. Shared-component
regressions: **98 passed, 2 originalpilot skips in 269.09 seconds** (100 cases).
The API-/SDK-/settings-free actual CLI flow also passes with PATH alone.
An initial lazy-import change omitted the old module.CS50AdapterPlan re-export;
33 existing setup errors exposed that compatibility dependency. The alias is now
lazy and all those unchanged executor assertions pass. A four-case red/green
HTTP-status regression preserves failed-download reasons without accepting an
absent raw artifact as verified. No assertions were weakened.

Six known TXT errors must remain visible, not xfailed or fixed in this project.
