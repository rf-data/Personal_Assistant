## docling_helper.py
# imports
from PIL import Image
import hashlib
from functools import lru_cache

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    RapidOcrOptions,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    ImageFormatOption,
)
from docling_core.types.doc import (
    DocItemLabel,
)


@lru_cache(maxsize=2)
def get_docling_image_converter(
    formula_enrichment: bool,
) -> DocumentConverter:

    pipeline_options = PdfPipelineOptions()

    pipeline_options.do_ocr = True

    pipeline_options.ocr_options = RapidOcrOptions(
        lang=["iso:de"],
        mode="full_page",
    )

    # Frames enthalten keine Tabellen.
    pipeline_options.do_table_structure = False

    pipeline_options.do_formula_enrichment = formula_enrichment

    # schützt vor problematischen Frames
    pipeline_options.document_timeout = 90

    return DocumentConverter(
        allowed_formats=[InputFormat.IMAGE],
        format_options={
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=(pipeline_options))
        },
    )


@lru_cache(maxsize=2)
def get_docling_converter(
    # use_ocr: bool = False,
    enrich_formula: bool = False,
) -> DocumentConverter:

    pipeline_options = PdfPipelineOptions()

    pipeline_options.do_ocr = False
    pipeline_options.do_formula_enrichment = enrich_formula

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
