## A_p2_emails.py
# imports

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.core.config import parsing_env_vars

# from src.core.memory import app_session # , RunContext
from src.tools_eda.profile_dataset import profile_dataset

# from frontend.


def show():
    st.header("🏠 Startseite ")
    st.subheader("**Data visualisations & Dashboards**")

    # run_config = app_session.run_settings
    st.divider()

    # st.markdown("**Under Construction**")

    # file_select, file_preview = st.columns(2)

    # with file_select:
    st.subheader("🖼️ Select a CSV file")

    input_data = parsing_env_vars.data_dir

    st.warning("ADAPT TO NEW FILE SYSTEM")

    file_eda = st.selectbox(
        label="Which csv file should be explored?",
        options=list(Path(input_data).rglob("*.csv")),
        # [shorten_path(f, n=1) for f in Path(input_data).iterdir()
        #         if f.suffix == ".csv"],
        key="file_eda",
    )

    st.write(f"You selected: {file_eda}")
    # run_config.file_names = st.session_state["files_html"] # html_select

    idx_col = st.number_input(
        "Insert number of index_column",
        value=None,
        placeholder="Type a number...",
        key="index_col",
    )
    st.write("Indicated 'index_column': ", idx_col)
    # for idx, file in enumerate(files_html):
    #     st.write(f"({idx}) ",files_html)

    st.toggle("Feature Correlation", key="feat_corr")

    corr_thresh = 1
    if st.session_state["feat_corr"]:
        corr_thresh = st.slider(
            label="Choose 'correlation threshold'",
            min_value=float(0),
            max_value=float(1),
            step=0.05,
            key="corr_thresh",
        )
        st.write("Correlation threshold:", corr_thresh)

    num, cat = st.columns(2)

    with num:
        st.toggle("DataViz -- Numeric Features", key="visualize_num")

        st.toggle("DataViz -- Stats 'NumFeats'", key="visualize_num_stats")

    with cat:
        st.toggle("DataViz -- Categorical Features", key="visualize_cat")

        st.toggle("DataViz -- Stats 'CatFeats'", key="visualize_cat_stats")

    values = np.logspace(-6, 3, 100)
    std_idx = st.slider(
        label="Choose default 'minimal std'",
        min_value=0,
        max_value=len(values) - 1,
        value=50,
        # format="scientific",
        # step=0.05,
        key="min_std",
    )
    min_std = values[std_idx]

    st.write("Selected 'min_std':", min_std)

    st.slider(
        label="Choose IQR multiplier",
        min_value=float(1),
        max_value=float(10),
        step=0.5,
        key="iqr_multiplier",
    )

    st.slider(
        label="Choose 'NaN threshold'",
        min_value=float(0),
        max_value=float(1),
        # format="scientific",
        step=0.05,
        key="nan_thresh",
    )

    st.subheader("File Preview")
    for idx, file in enumerate([file_eda]):
        f_path = f"{input_data}/{file}"
        index_col = int(idx_col) if idx_col is not None else None
        csv_data = pd.read_csv(f_path, index_col=index_col)

        with st.popover(
            label=f"**File #{idx}: '{Path(file).stem}'**", use_container_width=True
        ):
            st.write(csv_data.head())

        st.divider()

        config = {
            "f_path": f_path,
            "min_std": st.session_state["min_std"],
            "nan_thresh": st.session_state["nan_thresh"],
            "features": None,
            "iqr_multiplier": st.session_state["visualize_num"],
            "visualize_num_stats": st.session_state["visualize_num"],
            "visualize_cat_stats": st.session_state["visualize_cat"],
            "feat_corr": st.session_state["feat_corr"],
            "corr_thresh": corr_thresh,
            # "circle_x_label": "PCA 1",
            # "circle_y_label": "PCA 2",
            # "scatter_x_label": "Wavelength (nm)",
            # "scatter_y_label": "NIR reflectance (avg)"
        }

        profile_dataset(config)
