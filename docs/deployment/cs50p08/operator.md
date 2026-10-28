# C08 operator procedure

**HOLD.** Codex ran no real course transfers, host changes, installation gate or
production processing. C16 remains disabled. This guide does not approve execution.
The existing positive frozen-wheelhouse installation and real Hetzner acceptance
remain separate gates. No public API, Coolify change, service activation, build,
setup script, automatic package installation or external Git clone is involved.

Use a reviewed interpreter and private external archive/output directories owned
by the unprivileged operator. Paths below are examples, not newly granted mounts.
Outputs must be new paths. Preserve all prior inventories, source grants, receipts,
checkpoints and failed artifacts; do not clean or adopt unknown partial files.

1. **READ-ONLY** inspect the official [week overview](https://cs50.harvard.edu/python/weeks/0/),
   linked Short pages, notes, source indexes, [problem set](https://cs50.harvard.edu/python/psets/0/)
   and each task. Compare live structure to the 1/5/5 control counts. Do not follow
   other weeks. Browser observation is not acquisition evidence.
2. **REQUIRES_APPROVAL / CHANGE** obtain bounded official HTML exports using the
   existing reviewed discovery process, then record `course_id`, `week_id`,
   `source_origin: official`, `pages: [{url,path,sha256}]` in `snapshots.json`.
   Each path is relative to that file; each hash must match the unchanged export.
   Supply at most 64 pages of at most 1 MiB. Include actual linked indexes if
   individual source files are wanted; do not infer CDN URLs. **CHANGE** build:

   ```bash
   python -m scripts.cs50p_week discover --completion \
     --snapshots /operator/review/snapshots.json --output /operator/review/inventory-01.json
   ```

3. **READ-ONLY** inspect inventory, known/missing URL ledger and proposed selection:

   ```bash
   python -m scripts.cs50p_week plan --inventory /operator/review/inventory-01.json \
     --output /operator/review/plan-01.json
   ```

   Choose required canonical files and one text candidate for each lecture/Short.
   Keep relevant references and variants visible. Provided task files are distinct
   child objects; inline starter code is part of the task HTML. Review every
   proposed byte/type ceiling and the actual course license/rights. A source index
   is not itself a source package. Missing hrefs require exports; unsupported files
   stay blocked. No file is complete merely because it has a URL.
4. **REQUIRES_APPROVAL / CHANGE** write an explicit `selection-01.json` list of
   SourceGrant objects with `material_id`, exact `source_url`, `source_format`,
   `max_bytes`, `license_reviewed: true`, `purpose: download`. Planning-only fields
   must be removed. Keep the sum of grant ceilings within the 32 MiB run budget;
   split the week into reviewed batches. Generate and check the exact grant:

   ```bash
   python -m scripts.cs50p_week approve --inventory /operator/review/inventory-01.json \
     --selection /operator/review/selection-01.json --reviewed-by OPERATOR \
     --review-reference REVIEW-ID --transfer-bytes 33554432 \
     --output /operator/review/approval-01.json
   python -m scripts.cs50p_week check-approval --inventory /operator/review/inventory-01.json \
     --approval /operator/review/approval-01.json
   ```

5. **REQUIRES_APPROVAL / CHANGE** on the separately accepted host only, download
   approved raw files with the existing unprivileged download-only lane:

   ```bash
   python -m scripts.cs50p_week acquire --inventory /operator/review/inventory-01.json \
     --approval /operator/review/approval-01.json --archive /operator/archive/week0 \
     --checkpoints /operator/review/checkpoints-01 --confirm \
     --output /operator/review/acquired-01.json
   ```

6. **READ-ONLY** verify automatic source ZIP/Python entries and their raw SHA,
   sizes and receipts. They use the same `acquire` command, not manual import.
   Re-running unchanged sources with a fresh inventory-bound grant reuses verified
   bytes. A failed/interrupted receipt needs investigation, `--retry-failed` and a
   fresh approval. Text fallback is recalculated separately per Short; replan and
   approve only the next required candidate. Audio/video remain **BLOCKED** here.
   For genuinely unavailable automatic source offers, **CHANGE** record the manual
   decision using `mark-manual --inventory ... --material-id ... --source-format zip
   --filename reviewed.zip --provenance REASON --output NEW.json`; then
   `import-code --inventory NEW.json --archive ... --material-id ... --file ...
   --sha256 ... --provenance ... --output NEXT.json`. This explicitly records an
   official context page and never treats it as a file download URL.
7. **READ-ONLY** calculate acquisition and manual completeness:

   ```bash
   python -m scripts.cs50p_week report --inventory /operator/review/acquired-01.json \
     --archive /operator/archive/week0 --output /operator/review/acquisition-report.json
   ```

   Overall HOLD is expected before processing. Inspect per-material IDs/reasons
   and per-lecture/Short/task content groups. Other batches require new input
   inventories and approvals. Rediscovery can use `--previous-inventory` together
   with `--archive`; it revalidates and retains receipts. Removal of an acquired
   material stops reconciliation rather than discarding evidence.
8. **READ-ONLY** prepare the isolated processing plan:

   ```bash
   python -m scripts.cs50p_week_processing plan --inventory /operator/review/acquired-01.json \
     --output /operator/review/processing-plan.json
   ```

   **BLOCKED** for real execution: production `process()` refuses it. Review host
   network denial, read-only raw inputs, separate writable outputs, parser/native
   dependency installation, memory/CPU/time/disk limits and PDF visual uncertainty.
   A separately reviewed isolated host adapter is necessary before real processing.
   There is no flag to bypass this gate and no C16 activation.
9. **READ-ONLY** after separately approved processing, validate retained artifacts:

   ```bash
   python -m scripts.cs50p_week_processing report --inventory /operator/review/acquired-01.json \
     --archive /operator/archive/week0 --processing-root /operator/processed/week0 \
     --output /operator/review/processing-report.json
   ```

10. **READ-ONLY → REQUIRES_APPROVAL / CHANGE** use concrete failing IDs and actions
    to obtain missing exports, approve a smaller batch or reprocess under a newly
    reviewed parser version. Preserve failed results and immutable raw bytes.
    FULLY_COMPLETE needs all four assessments, validated files/results and no
    required manual work; it never releases the independent C26 gates.

Reproduce the synthetic end-to-end acceptance without any course download:

```bash
python -m pytest tests/test_cs50p_week_completion.py -q
python -m artifacts.c26_cs50p_08.run_offline_e2e --output /tmp/NEW-c08-e2e.json
python deployment/cs50p-download-only/week_source_smoke.py --source "$PWD"
```

Tests create synthetic ZIP/Python/HTML/PDF/TXT/SRT/VTT bytes, deny real DNS/socket
calls, use mock transfers and model sufficient free disk only for fixtures. They
exercise failure, validation, provenance, resumption and a second identical run.
They are not a positive installation or real host acceptance result.
