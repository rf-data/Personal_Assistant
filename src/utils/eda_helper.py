## eda_helper.py
# imports 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# === Feature description ===
def describe_features_stats(
                        data: pd.DataFrame, 
                        config: dict
):                      
    """Computes descriptive statistics for numerical and categorical features."""

    features = config["features"] or data.columns.tolist() 
    # na_threshold = config.get("na_thresh")
    # min_std = config.get("min_std") # 1e-6, 
    # verbose = config.get("verbose")
   
    num_feat = data[features].select_dtypes(include=[np.number]).columns.tolist()
    cat_feat = data[features].select_dtypes(exclude=[np.number]).columns.tolist()

    # if verbose:
    # print(f"📊 Numeric:")
    # for num in num_feat:
    #     print(f"- {num}")

    # print("\n🔤 Categorical:")
    # for cat in cat_feat:
    #     print(f"- {cat}")

    df_num = data[num_feat]

    stat_num = []
    for col in df_num.columns:
        stat_num.append({
        "count": len(df_num[col]),
        "count_clean": df_num[col].notna().sum(),
        "NaN_count": df_num[col].isna().sum(),
        "inf_count": np.isinf(df_num[col]).values.sum(),
        "min": np.nanmin(df_num[col]),
        "q01": df_num[col].quantile(0.01),
        "q05": df_num[col].quantile(0.05),
        "q10": df_num[col].quantile(0.10),
        "q25":df_num[col].quantile(0.25),
        "mean": np.nanmean(df_num[col]),
        "median": np.nanmedian(df_num[col]),
        "q75": df_num[col].quantile(0.75),
        "q90": df_num[col].quantile(0.90),
        "q95": df_num[col].quantile(0.95),
        "q99": df_num[col].quantile(0.99),
        "max": np.nanmax(df_num[col]),
        "std": np.nanstd(df_num[col]),
        "skewness": df_num[col].skew(numeric_only=True, skipna=True),
        "kurtosis": df_num[col].kurtosis(numeric_only=True, skipna=True)
    })

    # stats_num = pd.DataFrame(
    #                     stat_num,
    #                     index=num_feat
    #                     )
    #     {
    #     stat: [func(df_num[col]) for col in df_num.columns]
    #     for stat, func in statistics.items()
    # }, index=df_num.columns)

    df_cat = data[cat_feat]

    stat_cat =[]
    for col in df_cat.columns:
        # top_val = df_cat[col].mode(dropna=True)
        counts = data[col].value_counts()
        n_unique = df_cat[col].nunique()

        # if n_unique >= 10:
        top_values = ", ".join(
            [f"{idx} ({cnt})"
            for idx, cnt in counts.head(10).items()]
        )

        stats = {
            "col_name": col, 
            "n_unique": n_unique, 
            "NaN_count": df_cat[col].isna().sum(), 
            # "top_value": top_val
            }
        
        if len(top_values) > 0: 
            stats.update({
                    "top_5": top_values,
                    # "top_5_freq": df_cat[col]\
                    #         .value_counts(dropna=True)\
                    #         .iloc[:5]
            })

        stat_cat.append(stats)
    # stats_cat = pd.DataFrame(
    #                     stat_cat,
    #                     index=cat_feat
    #                     )
                                      
    #                                 ])
    # for col in cat_feat:
    #     stats_cat.loc[col, "n_unique"] = data[col].nunique(dropna=True)
    #     stats_cat.loc[col, "NaN_count"] = data[col].isna().sum()
    #     top_val = data[col].mode(dropna=True)
    #     if not top_val.empty:
    #         stats_cat.loc[col, "top"] = top_val[0]
    #         stats_cat.loc[col, "top_freq"] = data[col].value_counts(dropna=True).iloc[0]

    return stat_num, stat_cat


# === Feature visualisation ===
# def visualize_num_features(
#                     data: pd.DataFrame, 
#                     # config: dict
#                     ): # , cat_data=None):
#     """Plots boxplots for numeric and barplots for categorical data."""
#     # if num_data is not None and isinstance(num_data, pd.DataFrame):
#     feat = data.columns.tolist()
    
#     data.plot(
#         kind='box', 
#         subplots=True,
#         layout=(int(np.ceil(len(feat) / 3)), 3),
#         figsize=(15, 3 * int(np.ceil(len(feat) / 3))),
#         title="Boxplots of Numeric Features")
#     plt.tight_layout()
#     plt.show()
    
#     return 
def visualize_num_features(data):

    feat = data.columns.tolist()

    n_cols = 3
    n_rows = int(np.ceil(len(feat) / n_cols))

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(15, 4 * n_rows)
    )

    axes = np.array(axes).flatten()

    for ax, col in zip(axes, feat):

        ax.boxplot(data[col].dropna())

        ax.set_title(col)

    for ax in axes[len(feat):]:
        ax.set_visible(False)

    fig.tight_layout()

    return fig


def visualize_cat_features(data):
    # if cat_data is not None and isinstance(cat_data, pd.DataFrame):
    for col in data.columns:
        plt.figure(figsize=(8, 4))
        data[col].value_counts(dropna=False).plot(kind='bar')
        plt.title(f'Categorical Distribution: {col}')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()



def compile_eda_summary(data, config) -> pd.DataFrame: 
    num_data = data.select_dtypes(include="number")

    summary = {
        # "n_rows": data.shape[0],
        # "n_cols": data.shape[1],
        "dtype":   data.dtypes.astype(str).to_dict(),
        # "n_numeric_cols": num_data.shape[1],
        "n_missing": data.isna().sum().sum(),
        "n_missing_%":  (data.isna().sum().mean() * 100).round(2),
        "n_unique":  data.nunique(),
        "n_dups": data.duplicated().sum(),
        "ratio_dups": data.duplicated().mean(),
        "sample":  data.iloc[0]
    }

    # summary = {
    #     # "col_names": df.columns,
    #     "dtype":   data.dtypes,
    #     "mean (col)": np.mean(data, axis=0),
    #     "std (col)": np.std(data, axis=0),
    #     "nulls":   data.isnull().sum(),
    #     "null_%":  (data.isnull().mean() * 100).round(2),
    # }

    # if not num_data.empty:
    #     summary.update({
    #         "mean_row": num_data.mean(axis=1),
    #         "mean_col": num_data.mean(axis=0),
    #         "std_col": num_data.std(axis=0),
    #         "min_col": num_data.min(axis=0),
    #         "max_col": num_data.max(axis=0),
    #     })

    df_sum = pd.DataFrame(summary)

    # df_sum["problematic std"] = np.where(
    #             df_sum["std_col"].any() < config["min_std"],
    #             "Yes",
    #             "No"
    #             )
    df_sum["problematic nan"] = np.where(
                df_sum["n_missing_%"].any() > config["nan_thresh"],
                "Yes",
                "No"
                )
    
    return df_sum


def flag_outliers(
                df: pd.DataFrame, 
                config: dict
                ) -> pd.DataFrame:

    multiplier = config["iqr_multiplier"]       # : float = 1.5
    df["IQR"] = df["q75"] - df["q25"]
    df["low_limit"] = df["q25"] - multiplier * df["IQR"]
    df["up_limit"] = df["q75"] + multiplier * df["IQR"]
    # df["outlier"]

    value_cols = df.columns.difference(["low_limit", "up_limit"])

    mask = (
        df[value_cols].lt(df["low_limit"], axis=0)
        | df[value_cols].gt(df["up_limit"], axis=0)
    )

    df["n_outlier"] = mask.sum(axis=1)

    # df["n_outlier"] = df[df < df["low_limit"] | df > df["up_limit"]].sum()
    # ((df < df["low_limit"]) | (df > df["up_limit"])).sum()
    df["%_outlier"] = round(df["n_outlier"] / len(df) * 100, 2)
    
    return df  

    # df["q25"] - multiplier * df["IQR"]

        #            # q3 - q1
        # lower = q1 - multiplier * iqr
        # upper = q3 + multiplier * iqr
        # outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
        # results.append({
        #     "column":        col,
        #     "lower_bound":   round(lower, 2),
        #     "upper_bound":   round(upper, 2),
        #     "outlier_count": outlier_count,
        #     "outlier_%":     round(outlier_count / len(df) * 100, 2)
        # })

    # return df       # pd.DataFrame(results)

# df = pd.read_csv("customer_features.csv")
# print(flag_outliers(df).to_string(index=False))


def visualize_features_grouped(num_data=None, cat_data=None, suffixes=None):
    """
    Plots grouped numeric boxplots (e.g. _F, _M, _T suffixes) and categorical barplots.
    """
    if suffixes is None:
        suffixes = ["_F", "_M", "_T"]

    if num_data is not None and isinstance(num_data, pd.DataFrame):
        feature_groups = {}
        for col in num_data.columns:
            base = col
            for suffix in suffixes:
                if col.endswith(suffix):
                    base = col[:-2]
            feature_groups.setdefault(base, []).append(col)

        num_groups = len(feature_groups)
        ncols = 2
        nrows = int(np.ceil(num_groups / ncols))

        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12, 4 * nrows))
        axes = axes.flatten() if nrows > 1 else [axes]

        for ax, (base, cols) in zip(axes, feature_groups.items()):
            num_data[cols].plot(kind='box', ax=ax)
            ax.set_title(f"{base} ({'Grouped' if len(cols) > 1 else 'Single'})")

        for ax in axes[num_groups:]:
            ax.axis('off')

        plt.suptitle("Boxplots of Grouped Numeric Features", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.show()

    if cat_data is not None and isinstance(cat_data, pd.DataFrame):
        for col in cat_data.columns:
            plt.figure(figsize=(8, 4))
            cat_data[col].value_counts(dropna=False).plot(kind='bar')
            plt.title(f'Categorical Distribution: {col}')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
