# C26-CS50P-08 validation and handoff

**HOLD. C26 remains HOLD.** Implementation and offline evidence are ready for review; real Week-0 completion and default-branch integration are pending.

387 distinct tests passed and three external-artifact tests were skipped: 385 passed / 3 skipped in the main regression, plus two fresh download-only process tests. C08 adds 30 test cases. Final lint, compilation and whitespace checks passed. The test interpreter was Python 3.12.12 with pre-existing cached dependencies referenced from an isolated temporary environment; this is not a positive frozen-wheelhouse installation result.

Evidence: [machine validation](../../../artifacts/c26_cs50p_08/validation.json), [main JUnit](../../../artifacts/c26_cs50p_08/regression.xml), [runtime JUnit](../../../artifacts/c26_cs50p_08/runtime-tests.xml), [synthetic E2E](../../../artifacts/c26_cs50p_08/synthetic-e2e.json), [source-runtime smoke](../../../artifacts/c26_cs50p_08/source-runtime-smoke.json), [legacy-runtime smoke](../../../artifacts/c26_cs50p_08/c07-runtime-smoke.json).

The synthetic E2E reaches FULLY_COMPLETE only after separately validated local processing, then reuses all processed results and performs zero second-run transfers. Downloadreceipts remain byte-identical. Failed PDFs, unsafe/corrupt ZIPs, malformed subtitles and malformed/tampered processing evidence stay incomplete. An initial private-output-directory failure and a required-ledger downgrade finding were corrected and regression-tested. The legacy runtime smoke now correctly expects acquisition completeness with overall HOLD until processing exists.

The official [overview](https://cs50.harvard.edu/python/weeks/0/) and [problem set](https://cs50.harvard.edu/python/psets/0/) still identify one lecture, five Shorts and five tasks. Review metadata contains 105 material objects, 62 known URL occurrences / 41 distinct URLs, and 30 unresolved offered asset hrefs. The [URL ledger](../../course_sources/cs50p_week0_completion/url-ledger.json) provides exact IDs, known URLs, reasons and actions. The [browser observations](../../course_sources/cs50p_week0_completion/browser-observations.json) distinguish actual observations, historical evidence and tool-level index failures. No URL was inferred from a filename or CDN pattern.

Real review status by section (Y/N are independent completeness assessments):

| Section | Discovery | Acquisition | Processing | Manual |
|---|---|---|---|---|
| Week 0 | N | N | N | Y |
| Lecture 0 | Y | N | N | Y |
| Shorts | N | N | N | Y |
| Visual Studio Code for CS50 | N | N | N | Y |
| Functions | N | N | N | Y |
| Variables | N | N | N | Y |
| Return Values | N | N | N | Y |
| Side Effects | N | N | N | Y |
| Problem Set 0 | N | N | N | Y |
| Indoor Voice | N | N | N | Y |
| Playback Speed | N | N | N | Y |
| Making Faces | N | N | N | Y |
| Einstein | N | N | N | Y |
| Tip Calculator | N | N | N | Y |

Manual completeness is Y because unresolved automatic offers require discovery/approval, not fictitious manual downloads. It does not imply acquisition or processing completeness. Actual per-material acquisition/processing statuses and next actions are in [completeness.json](../../course_sources/cs50p_week0_completion/completeness.json).

Reproduce the main regression with a reviewed offline test environment:

```bash
python -m pytest tests/test_cs50p_week_completion.py tests/test_cs50p_week_acquisition.py \
  tests/test_cs50p_frozen_runtime.py tests/test_cs50p_download_only_install.py \
  tests/test_cs50p_mvp.py tests/test_cs50_week_materials.py \
  tests/test_cs50_material_processing.py tests/test_cs50_week_pilot.py \
  tests/test_cs50_code_zip.py tests/test_cs50_material_code.py \
  tests/test_cs50_material_download.py tests/test_cs50_material_pdf.py \
  tests/test_cs50_material_pdf_v2.py tests/test_official_transcript_import.py -q
python -m artifacts.c26_cs50p_08.run_offline_e2e --output /tmp/NEW-c08-e2e.json
```

The main recorded run collected the first 28 C08 cases; the final two fresh-process cases were then verified separately in runtime-tests.xml. Running this command on the delivered code collects 390 cases total. The three skips require real operator exports or original PDF artifacts and an explicit external-integration gate.

| Requested offline behavior | Coverage |
|---|---|
| Official ZIP/Python hrefs, index files, no guessed paths | source discovery and index-only tests |
| Automatic ZIP/Python transfer, same-source deduplication and cross-owner reuse | ZIP/Python, shared-source and E2E tests |
| Second run without transfer, retained receipts, interruption recovery | C07 resume tests, C08 E2E and processing-publication interruption |
| Missing/unsupported source, oversize, corruption, traversal/symlink/bomb | parametrized source failure tests plus 54 existing ZIP tests |
| Source obligations and explicit manual fallback | completeness/manual-export tests |
| Malformed/empty subtitles and independent Short fallbacks | C07/C08 subtitle and per-Short tests |
| Audio/video cannot bypass grants | separate audio/video rejection cases |
| Problem-set tree and reference anchors | child-tree/reference-fragment tests |
| HTML provenance, PDF pages/images, SRT/VTT segments | E2E plus existing PDF/importer regressions |
| Static code comments/functions/classes without execution | AST/marker, ZIP-member and individual-Python tests |
| Successful download with failed processing, untrusted status/output | invalid-PDF, forged-status and malformed/tampered-output tests |
| No C16/native-processing import during acquisition | two fresh-process runtime smokes |

Git and integration: the provided target branch/worktree already existed and was clean on the exact secured C07 commit. Shared Git metadata is read-only. No Git artifacts were created, no commit/push/PR/merge or cleanup was performed. The existing checkout and branch must remain for review. See [Git basis](../../../artifacts/c26_cs50p_08/git-basis.json).

The checked delivery patch is [c26-cs50p-08.patch](../../../artifacts/c26_cs50p_08/handoff/c26-cs50p-08.patch). Its forward/reverse application and byte equality are recorded in [handoff-validation.json](../../../artifacts/c26_cs50p_08/handoff-validation.json) and the final [package validation](../../../artifacts/c26_cs50p_08/handoff/package-validation.json). All code, intended review documents and validation records are included; the package directory is excluded to avoid recursive packaging. Apply only to a separate clean checkout of `1584a2807c8f9d75604ab17a4ea239d8f4a0882b`, not this already modified checkout.

Durable documentation is currently retained in this worktree and patch, not integrated into `master`. Repository lifecycle completion is therefore pending. The user prohibits automatic pushes/merges, and no integration or safe-cleanup condition is claimed. Live remote state was not verified. No pre-existing/shared worktree or branch may be deleted as part of this handoff.

Remaining gates: bounded official detail/index exports to resolve hrefs; source/type/size/rights approvals; real raw acquisition; reviewed production network/resource isolation and parser/native dependency installation; actual processing acceptance; positive frozen-wheelhouse installation; actual Hetzner acceptance; normal PR/review integration into master. No course files, production processing, Hetzner/Coolify changes, public APIs or C16 activation were performed.

Implementation details and constraints: [architecture](architecture.md). The ten-step labeled operator handoff is [operator.md](operator.md).
