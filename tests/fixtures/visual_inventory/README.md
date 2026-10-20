# Synthetic visual source fixtures

Hand-authored HTML and generated two-page PDF; no downloaded or copied course data.
`source.pdf.b64` is the exact PDF bytes encoded for portable text-only storage.
Decode it to a temporary `source.pdf` for tests. `build_fixture.py` documents their
construction using the already optional PyMuPDF dependency. Rebuilding is optional;
checked-in bytes keep source hashes stable across native-library versions.

The same 2×2 PNG occurs twice in each source. The PDF also includes page backgrounds,
a repeated footer line, a separate rectangle and three spatially connected paths
on the first page. These are geometric test shapes, not a semantic diagram gold set.
HTML additionally covers relative/external/SVG references, inline SVG, captions,
missing `src`, unsafe schemes and responsive references. All are inert source text.
