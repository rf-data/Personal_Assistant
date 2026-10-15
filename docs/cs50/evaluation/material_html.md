# HTML/assignment parser v1

Offline regression: six cases passed. Covers title/metadata, heading hierarchy,
nested ordered/unordered lists, table cells, preserved code, literal LaTeX and
MathML, links, image URLs/captions/context, inline-image byte deduplication,
empty/corrupt inputs, output limits and JSON/provenance roundtrip.

Main/article landmarks preferred; reliable nav/footer/aside/script/style removed.
Without landmarks, output warns that boilerplate isolation is partial. Unknown
leaf elements remain unknown_block; unsupported dynamic content is not rendered.
Public assignment/problem-set HTML uses the same structure-preserving parser;
no solutions, grading endpoints or private material are accessed. HTML image URLs
are references only. Inline raster data is separately archived by content hash;
no renderer or model validates the pictured subject. Literal math is unverified.
