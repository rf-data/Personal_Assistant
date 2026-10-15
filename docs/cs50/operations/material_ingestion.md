# Course materials: CLI and controlled operation

Run from the repository root with the existing lecture-worker uv environment
(Pydantic, httpx, BeautifulSoup and PyMuPDF already declared). No new dependencies
or parser model downloads. Use an external artifact directory you own. No IDE is
required. Material imports/help need no application settings or API credentials.
The reused executor now loads its SRT adapter model only when constructing a real
SRT executor or reading an SRT CLI plan. Its algorithms remain unchanged.
The SDK-guarded material help test uses only PATH in the child environment.
The index worker remains separate; no material embeddings or uploads
are implicitly performed.

## Offline catalog and plan

```bash
uv run --offline --no-sync python -m scripts.cs50_materials inventory \
  --output /tmp/cs50-material-inventory.v1.json
uv run --offline --no-sync python -m scripts.cs50_materials plan \
  --course cs50_python --section 0 --output /tmp/python0-material-plan.v1.json
uv run --offline --no-sync python -m scripts.cs50_materials status \
  --plan /tmp/python0-material-plan.v1.json --workspace /tmp/python0-material-artifacts \
  --course cs50_python --section 0 --max-resources 100
```

All output files are exclusive: choose fresh names. Inventory is occurrence-based,
including external/unclassified snapshot references. Plan contains the full
Discovery graphs and primary candidate bindings. Raw links require explicit
classification before becoming new planned candidates. Scopes include --resource
(original candidate ID or material ID), --lecture, --course/--section, --all-courses.
Section ai and week 0 remain strings. --all-courses cannot accompany narrower scope.
Status never writes. A missing receipt is reported as blocked, not completed.

## Explicit local import, then parsing

Choose exactly one ResourceCandidate from the generated JSON by role/URL/ID;
RESOURCE_ID below is that explicit ID, never a filename-derived identity.

```bash
uv run --offline --no-sync python -m scripts.cs50_materials import-local \
  --plan /tmp/python0-material-plan.v1.json --workspace /tmp/python0-material-artifacts \
  --resource "$RESOURCE_ID" --local-file /tmp/own-reviewed-material.html
# Preview above. Explicit local copy/archive approval:
uv run --offline --no-sync python -m scripts.cs50_materials import-local \
  --plan /tmp/python0-material-plan.v1.json --workspace /tmp/python0-material-artifacts \
  --resource "$RESOURCE_ID" --local-file /tmp/own-reviewed-material.html --execute-import
uv run --offline --no-sync python -m scripts.cs50_materials parse \
  --plan /tmp/python0-material-plan.v1.json --workspace /tmp/python0-material-artifacts \
  --resource "$RESOURCE_ID" --execute-parse
```

Without the matching execution flag, import/download/parse/resume only preview.
Local import labels origin local_import: it proves bytes/binding but does not
prove that those bytes were fetched from Harvard. No remote authenticity claim.
Raw source is preserved under its explicit material directory. Parser output is
separate and bound to raw/config hashes. Resume is the same verified parsing path:
replace `parse` by `resume --execute-parse`; it never starts a download.

## Real download: separate manual release

Review license/terms and the exact official URL first. Create a **new** plan scoped
to that single resource using --license-reviewed. This records your explicit review
in its binding; it is not automatic license detection. Keep this reviewed plan for
all later commands so receipt identity stays identical.

```bash
uv run --offline --no-sync python -m scripts.cs50_materials plan \
  --resource "$RESOURCE_ID" --license-reviewed --output /tmp/reviewed-one-material.v1.json
uv run --offline --no-sync python -m scripts.cs50_materials download \
  --plan /tmp/reviewed-one-material.v1.json --workspace /tmp/reviewed-material-run \
  --resource "$RESOURCE_ID" --max-resources 1
# Only after your separate approval (NOT executed during implementation):
uv run --offline --no-sync python -m scripts.cs50_materials download \
  --plan /tmp/reviewed-one-material.v1.json --workspace /tmp/reviewed-material-run \
  --resource "$RESOURCE_ID" --max-resources 1 --license-reviewed --execute-download
```

Download and parse are separate releases. Default serial execution, at most one
resource per invocation unless explicitly raised (1..2000). Unsupported/blocked
entries have no download/parse actions. Redirects, external hosts, unknown MIME,
oversized/empty transfers fail rather than guessing alternatives. Corrupt/foreign
outputs are preserved as conflicts; use a separately reviewed new generation.
No auth, cookies, browser, audio/video, SRT fallback, code execution, LLM or DB upload.

## Reproducible synthetic demonstration

```bash
uv run --offline --no-sync python -m scripts.cs50_materials demo --output /tmp/new-material-lecture
uv run --offline --no-sync python -m scripts.cs50_materials demo --course cs50_python --output /tmp/new-material-python
uv run --offline --no-sync python -m scripts.cs50_materials demo --all-courses --output /tmp/new-material-six
```

Output must not exist and must be outside the repository. These use MockTransport,
real storage/import/parser/resume/mapping functions and own synthetic bytes. One
notes source for each selected real lecture identity plus three explicitly own
synthetic resources in the first lecture (PDF slides, Python code, assignment).
Those extra offers are never claimed as actual remote discovery. Counts are
1/10/50 lecture identities and 4/13/53 completed material artifacts. This is not a
full download or parser-quality test of every known candidate/reference.

## Proposed separately released detail crawl (not implemented/enabled)

Start only from an explicit reviewed seed URL list from this catalog. Suggested
first limits: 20 HTML pages, depth one, 1MiB/page and 8MiB total, one request/second,
120-second whole-job deadline, zero automatic retries on rate limits. Respect
Retry-After and license/robots/access restrictions; redirect targets need the same
host/course-path validation before contact. Same approved course/CDN prefix only;
no queries/auth/cookies/forms/JS, third-party links, archives, audio or video.
Record each request outcome, source URL, timestamp and content SHA in a new snapshot
manifest; never overwrite existing fixtures. Render a preview with exact requests
before a distinct future crawl approval. This is a design for a follow-up, not a
currently supported CLI option or permission to start a live crawl.
