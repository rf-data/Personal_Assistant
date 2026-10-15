# Material support and quality matrix

| Type | Capability | Provenance | Limit / unproven quality |
|---|---|---|---|
| Notes/public assignment HTML | Supported structure, partial semantic classification | DOM, URL, original role/IDs/raw SHA | JS not rendered; no-landmark boilerplate partial; unknown leaves retained |
| Lists/tables/code in HTML | Supported | DOM, ordered nesting/cells/literal code | complex rowspan/colspan layout not reconstructed; DOM paths describe the filtered parser tree |
| MathML/LaTeX | Partial: literal source notation | DOM/source markup | no formula reconstruction or semantic verification |
| PDF/exported slides | Partial | original page/bbox/role/raw SHA | font heuristics, geometric table candidates; no OCR; reading order/layout not gold-reviewed |
| Embedded PDF/raster HTML image data | Supported archive/reference | exact bytes/hash, DOM/page/bbox/context | no pictured-content validation; captions only when explicit |
| Linked HTML images | Partial: reference, optional separately reviewed raw resource | original resolved URL, DOM/caption/context | no recursive automatic image download or broken-image repair |
| SVG | Partial raw/reference only | source hash/URL | never rendered or evaluated |
| py/sql/js/html/css/c/h/txt/md source files | Supported UTF-8/BOM | exact source path/line/text/raw SHA | no syntax execution, arbitrary encodings or notebook interpretation |
| PPT/PPTX/Keynote native presentations | Unsupported | catalog reference retained | requires bounded archive/OOXML adapter |
| ZIP/tar/downloadable repos | Unsupported | catalog reference retained | no extraction; traversal/symlink/nesting attacks cannot trigger extraction |
| Audio/video/player/YouTube | Unsupported in materials path | complete existing variants retained in graph/catalog | existing separate source pipeline unaffected |
| SRT/VTT/TXT transcripts | Existing separate transcript path | original transcript contracts | timed/timeless compatibility remains as documented; no new fallback |
| External/private/unknown platform | Blocked or unsupported | original URL/context retained | no auth or automatic scope expansion |

Supported means a tested controlled technical path, not live availability or
expert semantic approval. Each normalized block is source input, never an asserted
Knowledge fact. Math/image/unknown blocks are excluded from factual-unit mapping.
Tables with text have exact normalized windows and original structured cells.
Future gold review should separately check content completeness, reading order,
list/table/code fidelity, formula fidelity, image context and source references.
Use a small licensed mixed-material lecture before scaling. No LLM evaluation
or real material downloads were performed here.
