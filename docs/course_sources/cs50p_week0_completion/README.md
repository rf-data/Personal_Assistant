# C08 Week-0 review inventory

**HOLD — no real Week-0 archive or processing acceptance.**

The official [week overview](https://cs50.harvard.edu/python/weeks/0/), five linked
Short pages and [Problem Set 0](https://cs50.harvard.edu/python/psets/0/) with five
task pages were inspected through read-only browser discovery on 2026-10-28.
The control counts still match 1 lecture / 5 Shorts / 5 tasks. They are checked,
not built into the reusable discovery algorithm.

This directory is C08-owned. C07's historical evidence is retained unchanged.
The manifest combines its hashed historical overview with explicitly identified
browser observations. It does not substitute generated HTML for official exports.

- `manifest.json`: v2 material tree; automatic source packages require grants.
- `url-ledger.json`: every material ID, known URL or unresolved reason and action.
- `download-plan.json`: unapproved selection/size/rights planning, not a grant.
- `processing-plan.json`: local parser routes and the production isolation blocker.
- `completeness.json`: independent discovery/acquisition/processing/manual reports
  for the whole week, lecture, each Short, problem set and each task.

Known task references now include Python documentation and the linked contextual
references. Redirect destinations are not automatic acquisition permissions.
Tip Calculator supplies inline starter code in its HTML, not a downloadable `.py`.
The other four tasks require learner-created files; these filenames are not URLs.

The Short pages visibly offer transcripts, subtitles, audio and video. Four offer
source indexes/PDFs/ZIPs; the VS-Code Short offers slides but no source package.
Thirty offered asset hrefs remain unknown in the available browser representation.
They stay null with reasons. No naming-pattern inference, target-file fetch or
course-media download was used to resolve them. Source-index filenames alone are
not download permission. The next step is a bounded operator export of the linked
HTML pages/indexes and a fresh `discover --completion` run.

Rebuild offline from the preserved evidence:

```bash
python -m scripts.build_cs50p08_review
```

The [operator guide](../../deployment/cs50p08/operator.md) describes the genuine
export -> review -> acquisition -> offline processing handoff.
