## assemble_pdf.py
# import
# import click
import streamlit as st

# from collections import defaultdict
from returns.result import Success

# from gmp_compliance.src.model_parsing.classes_html_parsing import PDFPageExtract
# from src.core.logger import create_logger
from src.core.memory import app_session
from src.model_tools_parsing.pdf_assembler import PDFAssembler

# from src.tools.chunk import prepare_chunk_df
# import src.utils.general_helper as gh
# import src.utils.dict_helper as dh
# import src.utils.path_helper as ph
# import src.utils.df_helper as dfh


# ------------------
# MAIN FUNCTION
# ------------------
# @click.command()
# @click.option("--config_name",
#               prompt="Name of 'config_file' (no suffix)",
#               help='The config_file to use.')
# def prepare_pdf_rag():

#     gh.load_env_vars()
#     data_processed = env_variables("DATA_PROCESSED")

#     config_name = input("Enter 'config_file' name (no suffix): ")

#     config = dh.get_yaml_config(config_name)
#     # session.model_config = config

#     general_config = config.get("general_args", {})
#     log_name = general_config["name_log"]
#     name_logfile = general_config["name_logfile"]

#     assemble_config = config.get("assemble", {})
#     file_timestamp = assemble_config["file_timestamp"]
#     file_folder = assemble_config["file_folder"]
#     data_folder = f"{data_processed}/{file_folder}"

#     # setup logger
#     logger = create_logger(name=log_name,
#                            file_name=name_logfile)
#     session.logger = logger

#     file_names = [f for f in Path(data_folder).iterdir()
#              if (f.suffix == ".json"
#                  and f.name.startswith(file_timestamp))]

#     logger.info("Collected %s files from folder '%s'.",
#                 len(file_names),
#                 ph.shorten_path(file_folder))

#     return run_prepare_pdf_rag(file_names, config)


def assemble_single_pdf(
    extracts: Success,  # list[PDFPageExtract],
    # assemble_config: dict,
    # save: bool = False
) -> dict:
    parse_context = app_session.run_context
    assemble = parse_context.parse_settings.pdf.assemble

    logger = parse_context.logger

    assembler = PDFAssembler(parse_context=parse_context)

    for p_extract in extracts:
        if isinstance(p_extract, Success):
            p_extract = p_extract.unwrap()

        assembler.collect(p_extract)

    doc_dict = assembler.assemble_document()

    if assemble:
        if "md" in assemble:
            md_file = assembler.create_md_from_extract(doc_dict["info_dict"])

        if "txt" in assemble:
            logger.info("'Text assembling' script has not been build yet.")

            try:
                st.warning("'Text assembling' script has not been build yet.")
            except ImportError:
                pass

    return ""


# def assemble_related_pdf(file_names: List[str],
#                  config: dict):
#     # load env variables and config
#     data_processed = env_variables("DATA_PROCESSED")

#     # if not session.model_config:
#     # config = session.model_config
#         # dh.get_yaml_config(config_name)

#     general_config = config.get("general_args", {})
#     now = general_config.get(
#                         "timestamp",
#                         datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                         )
#     session_state.timestamp = now

#     model_name = general_config["llm_model"]
#     session_state.encoder = encoding_for_model(model_name)

#     assemble_config = config.get("assemble", {})
#     percents = assemble_config["percentiles"]
#     file_folder = assemble_config["file_folder"]
#     data_folder = f"{data_processed}/{file_folder}"

#     files_sorted = {}
#     for f_name in file_names:
#         name_short =Path(f_name).stem
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

# ddh.save_df_to_parquet(df=df_merged,
#                        f_name=f"{now}_df_merged_all",
#                        folder=f"{data_processed}/assembled",
#                        chunked=True)

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


# if __name__ == "__main__":
#     prepare_rag()


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
# #                         df.describe(percentiles=percents))
# #         logger.info("\nDuplicates:\n%s\n",
# #                         df.duplicated().sum())

# #         logger.info("\nNaN values:\n%s\n",
# #                         df.isna().sum())

# #         logger.info("%s\n", "=" * 50)

# #     return dfs
