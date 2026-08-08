## run_st_pdf_extract
# import
from pathlib import Path

from src.core.config import parsing_env_vars
from src.core.memory import ParseContext
from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.pdf_extractor import PDFCleanExtractor
from src.tools_parsing.assemble_pdf import assemble_single_pdf
from src.tools_parsing.extract_pdf import extract_pdf_file
from src.tools_parsing.post_extract_processing_pdf import post_process_pdf
from src.utils.path_helper import move_file, shorten_path


def run_pdf_extraction(parse_context):
    pdf_data = parsing_env_vars.data_pdf

    raw_data = f"{pdf_data}/raw"

    feat_enricher = FeatureEnricher(parse_context=parse_context)

    pdf_extractor = PDFCleanExtractor(
        parse_context=parse_context, enricher=feat_enricher
    )

    md_file = (
        extract_pdf_file(extractor=pdf_extractor, parse_context=parse_context)
        .bind(post_process_pdf)
        .bind(assemble_single_pdf)
    )

    f_name = parse_context.parse_settings.file_name
    dst_path = f"{raw_data}/{Path(f_name).stem}.pdf"

    move_file(f_name, dst_path)
    # html_assembler.render_text_file)

    parse_context.logger.info(
        "File '%s' has been moved to '%s'", shorten_path(f_name), shorten_path(dst_path)
    )

    return md_file


if __name__ == "__main__":
    parse_context = ParseContext()
    run_pdf_extraction(parse_context)
