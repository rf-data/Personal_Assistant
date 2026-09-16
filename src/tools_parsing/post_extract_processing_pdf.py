## post_extract_processing_pdf.py
# import
# import click

# from collections import defaultdict

from returns.result import Result, Success

# import pandas as pd
# from datetime import datetime
# from tiktoken import encoding_for_model
from src.core.memory import app_session
from src.model_parsing.base_classes_parsing import PDFPageExtract
from src.model_parsing.feature_enricher import FeatureEnricher

# from src.core.logger import create_logger
# from src.core.document_assembler import DocumentAssembler
# from gmp_compliance.src.model_parsing.classes_html_parsing import PDFPageExtract
from src.model_parsing.pdf_classifier import PDFClassifier
from src.model_parsing.pdf_cleaner import PDFCleaner
from src.model_parsing.pdf_merger import PDFMerger

# from src.tools.chunk import prepare_chunk_df
# import src.utils.general_helper as gh
from src.utils.dict_helper import save_base_model_as_dict, save_dict

# import src.utils.path_helper as ph
# import src.utils.df_helper as dfh


# ------------------
# MAIN FUNCTION
# ------------------
# @click.command()
# @click.option("--config_name",
#               prompt="Name of 'config_file' (no suffix)",
#               help='The config_file to use.')
# def process_pdf():

#     gh.load_env_vars()
#     config_name = input("Enter 'config_file' name (no suffix): ")

#     config = dh.get_yaml_config(config_name)
#     session.model_config = config

#     return run_process_pdf()


def post_process_pdf(
    extracts: Result,
    # prepare_config: dict,
    # enricher
) -> Result[list[PDFPageExtract], str]:
    parse_context = app_session.run_context
    logger = parse_context.logger

    classifier = PDFClassifier(parse_context=parse_context)

    cleaner = PDFCleaner(parse_context=parse_context)

    feat_enricher = FeatureEnricher(
        parse_context=parse_context,
        # encoder=app_session.encoder
    )
    merger = PDFMerger(parse_context=parse_context, enricher=feat_enricher)

    save = parse_context.parse_settings.pdf.save
    # if self.save and "assembled" in self.save:
    #         save_path = f"{self.save_folder}/{self.save_name}_assembled"
    #         save_dict(f_infos, save_path)

    for p_extract in extracts:
        if isinstance(p_extract, Success):
            p_extract = p_extract.unwrap()  # list[PDFPageExtract]

        line_groups = p_extract.elements
        page_no = p_extract.page_no

        logger.info("\n\nStart preparating text from page %s", page_no)

        save_path = f"{parse_context.save_folder}/{parse_context.save_name}_p{page_no}"

        page_attributes = {
            "median_size": p_extract.meta.median_font_size,
            "left_indent": p_extract.meta.left_indent,
            "height": p_extract.meta.height,
            "width": p_extract.meta.width,
        }

        groups_sorted = sorted(
            line_groups,
            key=lambda group: (group.meta.y_start_min, group.meta.x_start_min),
        )

        class_dict = classifier.classify_line(groups_sorted, page_attributes)
        # logger.info("Length 'text_segments' (after detect):\t%s", len(text_segments))

        if save and "class" in save:
            save_dict(class_dict, f"{save_path}_class")

        blocks_text = merger.merge_text_lines(
            class_dict["text"], class_dict["headings"], page_attributes
        )

        if save and "merge" in save:
            save_dict(class_dict, f"{save_path}_merge")

        blocks_text_clean = cleaner.handle_body_text_hyphens(blocks_text)

        p_extract.text_bodies = blocks_text_clean["text_bodies"]
        p_extract.bullets = blocks_text_clean["bullets"]
        p_extract.header_footer = class_dict["header_footer"]
        p_extract.headings = blocks_text["headings"]  # class_dict["headings"]
        p_extract.foot_notes = class_dict["foot_notes"]
        p_extract.content_table = class_dict["content_table"]
        p_extract.non_text = class_dict["other"]

        if save and "info" in save:
            save_base_model_as_dict(p_extract, f"{save_path}_info")
    # save = parse_context.parse_settings.pdf

    # if save and "info" in save:

    # self.save_folder = self.
    # self.save_name = self.parse_context.save_name

    # save_base_model_as_dict(p_extract, f"{save_path}_post_all")

    # full_text = [block.text for block in blocks_text]
    # full_text = "\n\n".join(full_text)

    # save_text_file(full_text,
    #                        file_name=f"{now}_{f_name}_p{page_no}_class",
    #                        folder=session.state.save_folder)
    # CLASSIFICATION etc. --> 'run_text_preparation.py'

    return Success(extracts)


# if __name__ == "__main__":
#     process_pdf()


#     # load env variables and config
#     data_processed = folder_env_vars("DATA_PROCESSED")

#     # if not session.model_config:
#     config = session.model_config
#         # dh.get_yaml_config(config_name)

#     general_config = config.get("general_args", {})
#     log_name = general_config["name_log"]
#     name_logfile = general_config["name_logfile"]
#     now = general_config.get(
#                         "timestamp",
#                         datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                         )
#     session.state.timestamp = now

#     model_name = general_config["llm_model"]
#     session.encoder = encoding_for_model(model_name)

#     assemble_config = config.get("assemble", {})
#     percents = assemble_config["percentiles"]
#     file_folder = assemble_config["file_folder"]
#     data_folder = f"{data_processed}/{file_folder}"

#     file_timestamp = assemble_config["file_timestamp"]

#     # setup logger
#     logger = create_logger(name=log_name,
#                            file_name=name_logfile)
#     session.logger = logger


#     # load text_dict
#     # 2026-04-18_17-38-11_beyond_DA_hypothesis_page_df.parquet
#     # folders = [
#     #         f"{data_processed}/chunk_df",
#     #         f"{data_processed}/page_df"
#     #         ]
#     # dfs_list = load_check_df(data_processed, timestamp, "parquet")


#     # if isinstance(file_name, str):
#     #     file_name = [file_name]

#     files = [f for f in Path(data_folder).iterdir()
#              if (f.suffix == ".json"
#                  and f.name.startswith(file_timestamp))]

#     logger.info("Collected %s files from folder '%s'.",
#                 len(files),
#                 ph.shorten_path(file_folder))

#     files_sorted = {}

#     for file in files:
#         name_short =Path(file).stem
#         chapter = name_short.split("_")[4]

#         files_sorted.setdefault(chapter, []).append(name_short)

#     doc_info = []
#     df_info = []
#     df_block = []
#     for chapter, f_list in files_sorted.items():

#         assembler = DocumentAssembler(
#                                 assemble_config=assemble_config,
#                                 doc_name=f"{now}_gmp_ch{chapter}_assembled.json",
#                                 save_folder=f"{data_processed}/assembled"
#                                 )

#         for f_name in f_list:
#             f_path = Path(f"{data_folder}/{f_name}.json")

#             results = dh.load_dict(f_path)

#             assembler.collect(results, f_name)

#         results = assembler.assemble_document()     # save_file=True)
#         # df_info.append(results["info_df"])
#         df_block.append(results["block_df"])
#         # doc_info.append(results["info_dict"])

#     # df_merged = pd.concat(df_info, ignore_index=True)
#     # logger.info("\n%s DF_MERGED %s\n",
#     #                     "=" * 15,
#     #                     "=" * 15,)
#     # logger.info("shape = %s",
#     #             df_merged.shape)
#     #     # self.logger.info("DF DESCRIPTION:\n%s",
#     #     #             df_info.describe(
#     #     #                         percentiles=percents
#     #     #                         ))
#     # logger.info("head:\n%s",
#     #             df_merged.head(5))

#     # ddh.save_df_to_parquet(df=df_merged,
#     #                        f_name=f"{now}_df_merged_all",
#     #                        folder=f"{data_processed}/assembled",
#     #                        chunked=True)

#     chunk_dfs = []
#     for idx, df in enumerate(df_block):

#         logger.info("Start chunking %s of %s dfs",
#                     idx,
#                     len(df_block))

#         chunk_df = prepare_chunk_df(df)
#         chunk_df["chunk_uid"] = (
#                     chunk_df["gmp_part"] + "_" +
#                     chunk_df["chapter"] + "_" +
#                     chunk_df["page"] + "_" +
#                     chunk_df["block_id"].astype(str) + "_" +
#                     chunk_df["chunk_id"].astype(str)
#                     )

#         uids = chunk_df["chunk_uid"].astype(str)

#         chunk_stem = uids.str.rsplit("_", n=1).str[0]
#         chunk_id   = uids.str.rsplit("_", n=1).str[1]

#         # chunk_stem, chunk_id = chunk_df["chunk_uid"].iloc[0].astype(str)[:1], chunk_df["chunk_uid"].iloc[0].astype(str)[-1]

#         # prev_chunk = chunk_split[:-1] + [chunk_split[-1].astype(int) - 1]
#         # next_chunk = chunk_split[:-1] + [chunk_split[-1].astype(int) + 1]

#         # chunk_df["prev_chunk_uid"] = (
#         #             chunk_df["gmp_part"] + "_" +
#         #             chunk_df["chapter"] + "_" +
#         #             chunk_df["page"] + "_" +
#         #             chunk_df["block_id"].astype(str)
#         #             )
#         # chunk_stem + "_" + chunk_id.astype(int) - 1
#         chunk_df["next_chunk_uid"] = f"{chunk_stem}_{chunk_id.astype(int) + 1}"

#         chunk_df["block_uid"] = (
#                     chunk_df["gmp_part"] + "_" +
#                     chunk_df["chapter"] + "_" +
#                     chunk_df["page"] + "_" +
#                     chunk_df["block_id"].astype(str)
#                     )

#         chunk_dfs.append(chunk_df)

#     # df_merge["embed_input"] = ""
#     # df_merge["text_for_llm"] = ""

#     df_chunk_merged = pd.concat(chunk_dfs, ignore_index=True)

#     logger.info("\n%s DF_CHUNK_MERGED %s\n",
#                         "=" * 15,
#                         "=" * 15,)
#     logger.info("shape = %s",
#                 df_chunk_merged.shape)
#         # self.logger.info("DF DESCRIPTION:\n%s",
#         #             df_info.describe(
#         #                         percentiles=percents
#         #                         ))
#     logger.info("head:\n%s",
#                     df_chunk_merged.head(5))

#     logger.info("\nDescription:\n%s\n",
#                     df_chunk_merged.describe(percentiles=percents))
#     # logger.info("\nDuplicates:\n%s\n",
#     #                 df_chunk_merged.duplicated().sum())

#     dfh.save_df_to_parquet(df=df_chunk_merged,
#                            f_name=f"{now}_df_chunk_merged_all",
#                            folder=f"{data_processed}/assembled",
#                            chunked=True)
#     return


#     # doc_info_red = []
#     # for d_info in doc_info:
#     #     doc_info_red.append({k:v for k, v in d_info.items()
#     #             if k in ["gmp_part", "chapter", "text"]})
#     # df_info = pd.DataFrame(doc_info_red)

#     # logger.info("DF SHAPE = %s",
#     #             df_info.shape)
#     # logger.info("DF DESCRIPTION:\n%s",
#     #             df_info.describe(
#     #                         percentiles=percents
#     #                         ))
#     # logger.info("DF HEAD:\n%s",
#     #             df_info.head(3))

#     # logger.info("\nShape:\t%s\n",
#     #                     df_merge.shape)
#     # logger.info("\nHead:\n%s\n",
#     #                     df_merge.head())
#     # logger.info("\nDescription:\n%s\n",
#     #                     )
#         # gmp_part = name_splits[3]
#         # chapter = name_splits[4]
#         # page = name_splits[-2]  # name_splits[5]


#         # for f"p{i}" in


#     # for

#     # df_dict = dfh.load_files_from_folder(
#     #                                 folder=data_processed,
#     #                                 df_names=file_name,
#     #                                 timestamp=timestamp,
#     #                                 # suffix="",
#     #                                 f_type="parquet"
#     #                                 )

#     # df_list = check_df_dict(df_dict, extract_dfs=True)

#     # df_merge = merge_clean_dfs(df_list, dup_col)

#     # df_merge["embed_input"] = ""
#     # df_merge["text_for_llm"] = ""


# # def merge_clean_dfs(df_list, duplicate_col):
# #     percents = session.percentiles
# #     logger = session.logger

# #     df_merge = pd.concat(df_list, ignore_index=True)

# #     logger.info("\n%s DF_MERGED %s\n",
# #                         "=" * 15,
# #                         "=" * 15,)
# #                         # \nName:\t%s", df_name)
# #     logger.info("\nShape:\t%s\n",
# #                         df_merge.shape)
# #     logger.info("\nHead:\n%s\n",
# #                         df_merge.head())
# #     logger.info("\nDescription:\n%s\n",
# #                         df_merge.describe(percentiles=percents))

# #     n_duplicates = df_merge.duplicated().sum()
# #     logger.info("\nDuplicates:\n%s\n",
# #                         n_duplicates)

# #     logger.info("\nNaN values:\n%s\n",
# #                         df_merge.isna().sum())

# #     if n_duplicates > 0:
# #         df_merge = df_merge.drop_duplicates(
# #                                     subset=[duplicate_col]
# #                                     )

# #     return df_merge


# # def check_df_dict(df_dict, extract_dfs=True):
# #     logger = session.logger
# #     percents = session.percentiles

# #     dfs = []
# #     for df_name, df in df_dict.items():
# #         if extract_dfs:
# #             dfs.append(df)

# #         logger.info("\n%s %s %s\n",
# #                         "=" * 15,
# #                         df_name.upper(),
# #                         "=" * 15,)
# #                         # \nName:\t%s", df_name)
# #         logger.info("\nShape:\t%s\n",
# #                         df.shape)
# #         logger.info("\nHead:\n%s\n",
# #                         df.head())
# #         logger.info("\nDescription:\n%s\n",
#                         df.describe(percentiles=percents))
#         logger.info("\nDuplicates:\n%s\n",
#                         df.duplicated().sum())

#         logger.info("\nNaN values:\n%s\n",
#                         df.isna().sum())

#         logger.info("%s\n", "=" * 50)

#     return dfs
