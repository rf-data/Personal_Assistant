# PDF/slides/images v1

> Historical v1 regression record. Current parser behavior and version-specific
> limits are documented in the [v2 evaluation](pdf_v2.md).
> These original test counts are retained as a dated package result.

PyMuPDF is already declared/installed. Docling is installed but not selected:
its richer layout/OCR/formula pipelines can require model assets and have broader
initialization dependencies. No dependency or model installation was performed.

Six offline cases pass: multipage text with distinct page positions, own embedded
image bytes/hash/ref, literal formula candidates, slide-role preservation, invalid
magic/corruption, page limit and actual subprocess timeout. Library diagnostics
were observed on stdout and are now isolated from the JSON result channel.

The isolated -I worker has address-space/CPU/file-output bounds, plus page/block/
image/count/aggregate-image-byte limits. Parent timeout kills the process group
and waits. Text is extracted without OCR. Page/bbox provenance is explicit.
Heading/code classification is heuristic; table candidates may overlap paragraph
text. Literal formula candidates are marked uncertain, never reconstructed.
Blank/scanned pages warn instead of inventing text. PDF-exported slides retain
slides role and page metadata. Image captions are not invented; page text is
available as context. Original compressed embedded bytes are kept separately.

Native PowerPoint PPT/PPTX and ZIP are explicitly unsupported: no existing
bounded OOXML/archive adapter is reused. Installing python-pptx implicitly or
extracting arbitrary archives would bypass the requested safety review. These
links remain cataloged. SVG is archived/reference-only, never rendered.
