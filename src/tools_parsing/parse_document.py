## parse_document.py
# import
from pathlib import Path

from src.core.memory_parsing import ParseContext
from src.model_parsing.docx_extractor import DOCXCleanExtractor
from src.model_parsing.feature_enricher import FeatureEnricher
from src.model_parsing.pdf_extractor import PDFCleanExtractor
from src.model_parsing.text_extractor import (
    MDCleanExtractor,
    TXTCleanExtractor,
)
from src.tools_parsing.extract_pdf import extract_pdf_file
from src.tools_parsing.post_extract_processing_pdf import post_process_pdf
from src.tools_parsing.assemble_pdf import assemble_single_pdf


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
    parse_context,
):
    # source_path =  parse_context.local_path.with_suffix(".pdf")
    if file_path is None:
        raise ValueError(f"No local_path available for '{parse_context.save_name}'.")

    suffix = file_path.suffix.lower()

    enricher = FeatureEnricher(
        parse_context=parse_context,
    )

    match suffix:
        case ".pdf":
            return parse_pdf_document(
                file_path=file_path,
                parse_context=parse_context,
                enricher=enricher,
            )

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

        case _:
            raise ValueError(f"Unsupported document format: {suffix}")

    return None


def parse_pdf_document(
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
