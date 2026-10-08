## parse_document.py
# import
from pathlib import Path
import json

# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions
# from docling.document_converter import (
#     DocumentConverter,
#     PdfFormatOption,
# )

from src.core.memory_parsing import ParseContext, PARSER_BACKEND

# from src.model_parsing.docx_extractor import DOCXCleanExtractor
from src.model_parsing.feature_enricher import FeatureEnricher
from src.model_parsing.pdf_extractor import PDFCleanExtractor

# from src.model_parsing.text_extractor import (
#     MDCleanExtractor,
#     TXTCleanExtractor,
# )
from src.tools_parsing.extract_pdf import extract_pdf_file
from src.tools_parsing.post_extract_processing_pdf import post_process_pdf
from src.tools_parsing.assemble_pdf import assemble_single_pdf

from src.utils.path_helper import ensure_dir
from src.utils.docling_helper import get_docling_converter
from src.utils.text_file_helper import save_text_file

# def parse_document(
#     # file_path: Path,
#     parse_context: ParseContext,
#     # # resource: LectureResource,
#     # course_root: Path,
#     ) -> None:

#     source_path =  parse_context.local_path.with_suffix(".pdf")
#     # save_folder}/{parse_context.save_name}.json"
#     if source_path is None:
#         raise ValueError(
#             f"No local_path available for '{parse_context.save_name}'."
#         )

#     # source_path = Path(f_path)

#     if not source_path.exists():
#         raise FileNotFoundError(source_path)

#     enricher = FeatureEnricher(parse_context)
#     match source_path.suffix.lower():
#         case ".pdf":
#             parse_pdf_document(
#                 file_path=source_path,
#                 # course_root=course_root,
#                 parse_context=parse_context,
#                 enricher=enricher
#             )

#         case _:
#             raise ValueError(
#                 f"Unsupported document type: "
#                 f"{source_path.suffix}"
#             )

#     return None


def parse_document(
    file_path: Path,
    parse_context: ParseContext,
):
    # source_path =  parse_context.local_path.with_suffix(".pdf")
    if file_path is None:
        raise ValueError(f"No local_path available for '{parse_context.save_name}'.")

    suffix = file_path.suffix.lower()

    enricher = FeatureEnricher(
        parse_context=parse_context,
    )

    match parse_context.parser_backend:
        case PARSER_BACKEND.DIY if suffix == ".pdf":
            return parse_pdf_diy(
                file_path=file_path,
                parse_context=parse_context,
                enricher=enricher,
            )

        case PARSER_BACKEND.DOCLING:
            return parse_document_docling(
                file_path,
                save_folder=(file_path.parent.parent / "parsed"),
                # parse_context,
            )

        case _:
            raise ValueError(f"Unknown parser backend: {parse_context.parser_backend}")

        # case ".docx":
        #     extractor = DOCXCleanExtractor(
        #         parse_context=parse_context,
        #         enricher=enricher,
        #     )
        #     return extractor.extract(str(file_path))

        # case ".md":
        #     extractor = MDCleanExtractor(
        #         parse_context=parse_context,
        #         enricher=enricher,
        #     )
        #     return extractor.extract(str(file_path))

        # case ".txt":
        #     extractor = TXTCleanExtractor(
        #         parse_context=parse_context,
        #         enricher=enricher,
        #     )
        #     return extractor.extract(str(file_path))

    return None


# ! TODO --> pymupdf_helper
import pymupdf


def render_bbox(
    pdf_path: Path,
    page_no: int,
    bbox: dict,
):

    doc = pymupdf.open(pdf_path)
    page = doc[page_no - 1]

    height = page.rect.height

    rect = pymupdf.Rect(
        bbox["l"],
        height - bbox["t"],
        bbox["r"],
        height - bbox["b"],
    )

    pix = page.get_pixmap(
        clip=rect,
        matrix=pymupdf.Matrix(2, 2),
    )

    return pix


# ! TODO --> docling_helper

# class FormulaReference(BaseModel):
#     formula_id: str

#     page: int
#     bbox: tuple[float, float, float, float]

#     decoded: bool

#     text: str | None = None
#     original_text: str | None = None

#     image_path: Path | None = None


def find_unresolved_formulas(doc: dict) -> list[dict]:

    return [
        item
        for item in doc.get("texts", [])
        if (item.get("label") == "formula" and not item.get("text", "").strip())
    ]


def parse_document_docling(
    file_path: Path,
    save_folder: Path,
    *,
    enrich_formula: bool = False,
):

    converter = get_docling_converter(enrich_formula)

    result = converter.convert(file_path)

    doc = result.document

    ensure_dir(save_folder)

    json_path = save_folder / f"{file_path.stem}_docling.json"

    # md_path = (

    #     /
    # )

    with json_path.open("w", encoding="utf-8") as f:
        # write_text(
        json.dump(
            doc.export_to_dict(),
            f,
            ensure_ascii=False,
            indent=2,
        )

    save_text_file(
        doc.export_to_markdown(),
        file_name=f"{file_path.stem}_docling",
        folder=save_folder,
    )
    # with md_path.open("w", encoding="utf-8"):

    #     write_text(
    #     doc.export_to_markdown(),
    #     encoding="utf-8",
    # )

    return doc


def parse_pdf_diy(
    file_path: Path,
    parse_context: ParseContext,
    enricher: FeatureEnricher,
):
    # parse_context.parse_settings.file_name = str(file_path)

    extractor = PDFCleanExtractor(
        parse_context=parse_context,
        enricher=enricher,
    )

    return (
        extract_pdf_file(
            extractor=extractor,
            parse_context=parse_context,
        )
        .bind(post_process_pdf)
        .bind(assemble_single_pdf)
    )


if __name__ == "__main__":
    from src.core.config import folder_env_vars

    parse_context = ParseContext(parser_backend="docling")

    data_folder = folder_env_vars.data_lectures / "loviscach/mathe_1/documents"
    pdf_paths = [f for f in data_folder.rglob("*.pdf")]

    print(f"Found {len(pdf_paths)} pdf_files.")

    for path in pdf_paths:
        parse_document(file_path=path, parse_context=parse_context)
