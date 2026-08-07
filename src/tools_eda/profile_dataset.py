## profile_dataset.py
# import
import numpy as np
import pandas as pd
import streamlit as st

from _prototypes.utils.eda_helper import (
    compile_eda_summary,
    describe_features_stats,
)
from src.utils.st_eda_helper import st_df_profile

# tools_eda. import PCA_circle, flag_outliers


def profile_dataset(config: dict):
    f_path = config.get("f_path")
    assert f_path is not None

    df = pd.read_csv(f_path)

    corr_threshold = config.get("corr_thresh")
    assert corr_threshold is not None
    # : float = 0.8) -> None:

    summary = compile_eda_summary(data=df, config=config)

    #     too_many_nans = (df_num.isna().mean() > na_threshold) if na_threshold is not None else False
    # low_variance = (df_num.std(skipna=True) < min_std) if min_std is not None else False
    # to_drop = too_many_nans | low_variance
    # # df_num_filtered = df_num.loc[:, ~to_drop]

    # if verbose and to_drop.any():
    #     print(f"🧹 Drop recommendation (numeric features): {to_drop[to_drop].index.tolist()}")

    # num_feats = set(df.select_dtypes(include=[np.number]).columns.tolist())
    # cat_feats = set(df.select_dtypes(exclude=[np.number]).columns.tolist())

    with st.expander("Dataset Profile"):
        st_df_profile(df)
        #         st.markdown(f"""
        # ## DATASET PROFILE\n
        # **Row count:** {df.shape[0]:,}  \t|  **Column count:** {df.shape[1]}\n
        # **Count 'numeric columns' 📊 :** {len(num_feats)} \n
        # **Count 'categorical columns' 🔤 :** {len(cat_feats)} \n
        # **Column names:**  {list(df.columns)}\n
        # **Memory usage:** {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n

        # ### Head
        # """)
        #         df_head = df.head(5).T  # if config["df_transponse"] else df.head(5)
        #         st.dataframe(df_head)
        st.markdown("\n### Summary ")
        st.dataframe(summary)  # .to_string()}
    # """) # .to_string())

    ####### column profile

    # # compiling statistical data
    stat_num, stat_cat = describe_features_stats(df, config)

    # stats_num = flag_outliers(stat_num, config)

    # if config["visualize_numeric"]:
    ## --> visualise_eda_stats
    # print(f"\n{'='*30}\n{name}\n{'='*30}")
    if len(stat_num) > 0:
        with st.expander("NUMERICAL FEATURES"):  # \n{'='*30}
            st.dataframe(pd.DataFrame(stat_num))

            # if config.get("visualize_num_stats"):
            #     # print(f"NUMERIC FEATURES\n{'='*30}")
            #     num_keys = [stat.keys() for stat in stat_num]
            #     num_data = df[num_keys]        # .index.tolist()

            #     with st.popover("**Numeric Features**"):
            #         # print(f"\n{'='*30}\nNUMERIC FEATURES\n{'='*30}")
            #         if len(num_data) == 0:
            #             st.error("DataFrame contains no numerical features.")

            #         # visualize_num_features(
            #             data=num_data,
            #             # config=config,
            #             # cat_data=None,
            #             # save_dir=FIGURE_NUM,
            #             # f_name=name
            #             )
            # fig = visualize_num_features(num_data)
            # st.pyplot(fig)

    else:
        st.markdown("DataFrame contains no numerical features.")
        # {name}

    if len(stat_cat) > 0:
        with st.expander("CATEGORICAL FEATURES"):
            # \n{'='*30}
            # {'='*30}\n
            # st.dataframe(pd.DataFrame(stat_cat))
            st.json(stat_cat)
            # .T}

            # if config.get("visualize_cat_stats"):
            #     cat_data = df[stats_cat.index.tolist()]

            #     # if len(cat_data) == 0:
            #     #     print(f"DataFrame contains no numerical features.")

            #     with st.popover("**Categorical Features**"):
            #         # print(f"\n{'='*30}\nCATEGORICAL FEATURES\n{'='*30}")
            #         visualize_cat_features(
            #                     data=cat_data,
            #                     # config=config,
            #                     # cat_data=None,
            #                     # save_dir=FIGURE_NUM,
            #                     # f_name=name
            #                     )
    else:
        st.markdown("DataFrame contains no categorical features.\n")
        # {name}

    #     # preparing data for DataViz'

    # print(f"\n{'='*30}\n{name}\n{'='*30}")

    ### --> PLOTLY:
    # Auswahl plot_type
    # v.a.KDE_PLOTS mit Auswahl Features

    # print("[...]")

    # if config.get("flag_column_outliers"):
    #         results = flag_column_outliers(df)

    #         st.markdown(f"### Outliers (per column)      ")
    #         st.dataframe(results)

    #     if config.get("flag_pca_outliers"):
    #         flag_pca_outliers(df, config)

    #         st.markdown(f"### Outliers (PCA)       ")
    #         st.dataframe(results)

    # if config.get("pca_circle") and config.get("n_opt_pca") == 2:
    #     # --> compile_pca_circle()
    #     PCA_circle(data=df, config=config)

    if config.get("feat_corr"):
        ## --> compile_feature_corr()
        corr_matrix = df.corr(numeric_only=True).abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        redundant_pairs = [
            (col, row, round(upper_triangle.loc[row, col], 3))
            for col in upper_triangle.columns
            for row in upper_triangle.index
            if upper_triangle.loc[row, col] > corr_threshold
        ]
        with st.popover("Column Profile"):
            st.markdown(f"""
## COLUMN PROFILE \n
### HIGHLY CORRELATED PAIRS (threshold: {corr_threshold})
""")
        if redundant_pairs:
            for col_a, col_b, corr_val in redundant_pairs:
                st.markdown(f"  {col_a}  ↔  {col_b}  |  correlation: {corr_val}")
        else:
            st.markdown("  None found.")

    return


# def profile_dataset(filepath: str) -> None:
#     df = pd.read_csv(filepath)

#     print("=== DATASET PROFILE ===\n")
#     print(f"Rows: {df.shape[0]:,}  |  Columns: {df.shape[1]}")
#     print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n")

#     summary = pd.DataFrame({
#         "col_names": df.columns,
#         "dtype":   df.dtypes,
#         "nulls":   df.isnull().sum(),
#         "null_%":  (df.isnull().mean() * 100).round(2),
#         "unique":  df.nunique(),
#         "sample":  df.iloc[0]
#     })

#     print(summary.to_string())

## Call the function
# profile_dataset("sales_data.csv")
