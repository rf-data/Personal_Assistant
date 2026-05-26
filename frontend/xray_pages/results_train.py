from pathlib import Path

import pandas as pd
import streamlit as st
from app.utils.loader import find_files, load_df, load_image

## FOLDER PATHS
METRICS = Path("/workspaces/may25_bds_covid19/streamlit/app/static_files/best_hp_df")
CLASS_REPORTS = Path(
    "/workspaces/may25_bds_covid19/streamlit/app/static_files/ClassReport"
)
CONF_MATRICES = Path(
    "/workspaces/may25_bds_covid19/streamlit/app/static_files/ConfMatrix"
)
GRADCAM = Path("/workspaces/may25_bds_covid19/streamlit/app/static_files/GradCam")
SHAP = Path("/workspaces/may25_bds_covid19/streamlit/app/static_files/SHAP")


## FUNCTIONS
def show():
    st.header("📊 Describing Data")
    # st.write("Welcome to the COVID-19 X-Ray Classification app!")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📉 Metrics from runs",
            "📏 Classification Report / 🔢 Confusion Matrix",
            "🌈 GradCam",
            "🔍 SHAP",
        ]
    )

    with tab1:
        st.markdown("""
        #### **Metrics from Runs  --  accuracy and loss**

        """)

        with st.popover("Choose a stage"):
            opt_1 = st.multiselect(
                "The run metrics from what stage do you want to see?",
                [
                    "Initial",
                    "Fine_0",
                    "Fine_20",
                    "Fine_50",
                    "Fine_100",
                    "Fine_complete",
                    "DataAug_None",
                    "DataAug_smooth",
                    "DataAug_enhanced",
                ],
                default=None,
                # max_selections=1,
                placeholder="Choose at least one stage.",
            )

        # st.divider()
        st.write("You selected:", opt_1)
        st.divider()

        if opt_1:
            my_table = st.empty()  # Platzhalter für Tabelle
            my_table.dataframe(pd.DataFrame())  # Start (optional)
            for stage in opt_1:
                files = find_files(METRICS, stage)
                if len(files) >= 1:
                    dfs = [load_df(file, extension=".html") for file in files]
                    for df in dfs:
                        if df is not None:
                            df.columns = df.columns.get_level_values(0)
                            df.rename(
                                columns={"Unnamed: 0_level_0": "trial_id"}, inplace=True
                            )
                            df["stage"] = stage
                        else:
                            st.warning(f"{stage} - File has invalid extension.")
                        my_table.add_rows(df)
                else:
                    st.warning(f"{stage} - Found no matching file")
                    # stage_best_hp[f"{stage}"])

        else:
            st.warning("No selection made so far.")
            # st.table(my_table)

    with tab2:
        st.subheader("Classification reports and confusion matrices")

        with st.popover("Choose a stage"):
            opt_2 = st.multiselect(
                "The classification report and confusion matrix from what stage do you want to see?",
                [
                    "Initial",
                    "Fine_0",
                    "Fine_20",
                    "Fine_50",
                    "Fine_100",
                    "Fine_complete",
                    "DataAug_None",
                    "DataAug_smooth",
                    "DataAug_enhanced",
                ],
                default=None,
                max_selections=1,
                placeholder="Choose a stage (max. 1)",
            )

        # st.divider()
        # st.write("You selected:", options)
        # st.divider()
        st.markdown(f"""
        **Selected Stage:**\t{None if not opt_2 else opt_2}
        """)

        """
        =============================================
        --- CLASSIFICATION REPORT TRAINING ---
        =============================================
                    precision  recall  f1-score  support  f2-score   auc
        covid             0.972   0.972     0.972  960.000     0.972 0.997
        lung              0.965   0.948     0.956  960.000     0.951 0.994
        normal            0.946   0.964     0.955  960.000     0.960 0.994
        viral             0.998   0.997     0.997  960.000     0.997 1.000

        accuracy          0.970   0.970     0.970    0.970       NaN   NaN

        macro avg         0.970   0.970     0.970 3840.000     0.970 0.996
        weighted avg      0.970   0.970     0.970 3840.000     0.970 0.996
        micro avg         0.970   0.970     0.970      NaN     0.970 0.997


        =============================================
        --- CLASSIFICATION REPORT VALIDATION ---
        =============================================
                    precision  recall  f1-score  support  f2-score   auc
        covid             0.942   0.954     0.948  240.000     0.952 0.993
        lung              0.917   0.925     0.921  240.000     0.923 0.990
        normal            0.918   0.883     0.900  240.000     0.890 0.987
        viral             0.975   0.992     0.983  240.000     0.988 1.000

        accuracy          0.939   0.939     0.939    0.939       NaN   NaN

        macro avg         0.938   0.939     0.938  960.000     0.938 0.993
        weighted avg      0.938   0.939     0.938  960.000     0.938 0.993
        micro avg         0.939   0.939     0.939      NaN     0.939 0.994
        """

        with st.expander("**Classification Reports**"):
            if opt_2:
                all_files = []

                for stage in opt_2:
                    files = find_files(CLASS_REPORTS, stage)
                    all_files.extend(files)

                if all_files is not None:
                    file_train = [
                        f
                        for f in all_files
                        if ("_train_" in f.name) and ("_ClassReport" in f.name)
                    ]
                    file_val = [
                        f
                        for f in all_files
                        if ("_val_" in f.name) and ("_ClassReport" in f.name)
                    ]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Training Dataset")
                        table = st.empty()
                        table.dataframe(pd.DataFrame())

                        if file_train:
                            for file in file_train:
                                df = load_df(file)
                                df = df.round(3)
                                '''
                                text = df.to_string(index=True)
                                st.markdown("""
                                =============================================
                                --- CLASSIFICATION REPORT TRAINING ---
                                =============================================
                                """)
                                # st.text(text)
                                st.markdown("<pre style='font-size:13px; font-family:Courier New;'>"+text+"</pre>", unsafe_allow_html=True)
                                '''
                                table.add_rows(df)
                        else:
                            st.write("Found no matching file")

                    with col2:
                        st.subheader("Validation Dataset")
                        table = st.empty()
                        table.dataframe(pd.DataFrame())

                        if file_val:
                            for file in file_val:
                                df = load_df(file)
                                df = df.round(3)

                                '''
                                text = df.to_string(index=True)
                                st.markdown("""
                                =============================================
                                --- CLASSIFICATION REPORT VALIDATION ---
                                =============================================
                                """)
                                st.text(text)
                                '''

                                table.add_rows(df)
                        else:
                            st.write("Found no matching file")

                else:
                    st.warning(f"{opt_2} - Found no matching file(s)")
            else:
                st.warning("No selection made so far.")

        with st.expander("**Confusion Matrices**"):
            if opt_2:
                files_cm = []
                for stage in opt_2:
                    matches = find_files(CONF_MATRICES, stage, extension=".png")
                    files_cm.extend(matches)
                    # find_files(CONF_MATRICS, opt_2)

                if files_cm:
                    train_cm = [
                        f
                        for f in files_cm
                        if ("_train_" in f.name) and ("_ConfMatrix" in f.name)
                    ]
                    val_cm = [
                        f
                        for f in files_cm
                        if ("_val_" in f.name) and ("_ConfMatrix" in f.name)
                    ]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Training Dataset")
                        if train_cm:
                            images_train = load_image(train_cm)
                            if images_train:
                                for name, img in images_train:
                                    # cm = [load_image(file) for file in train_cm]
                                    # img =
                                    st.image(
                                        img, caption=name, use_container_width=True
                                    )
                        else:
                            st.write("No Training confusion matrices found.")

                    with col2:
                        st.subheader("Validation Dataset")
                        if val_cm:
                            images_val = load_image(val_cm)
                            if images_val:
                                for name, img in images_val:
                                    # cm = [load_image(file) for file in val_cm]
                                    # img = load_image(img_path)
                                    st.image(
                                        img, caption=name, use_container_width=True
                                    )

                        else:
                            st.write("No validation confusion matrices found.")

                else:
                    st.write(f"{opt_2} - Found no matching .png file")
            else:
                st.warning("No selection made so far.")

        st.divider()
        st.subheader("**_Further Info_**")
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.popover("**_INFO: Classification Metrics_**"):
                st.markdown("""
                **Recall (Sensitivity):**  
                > Measures the proportion of true positives among positive samples.
                > It's the model's ability to correctly identify positive instances.    
                """)
                st.latex(r"Recall = \frac{TP}{TP + FN}")

                st.markdown("""
                **Specificity:**  
                > Measures the proportion of true negatives among negative samples. <br>
                > It's the model's ability to correctly identify negative instances.    
                """)
                st.latex(r"Specificity = \frac{TN}{TN + FP}")

                st.markdown("""
                **Precision:**  
                > Measures the proportion of true positives among positive predictions. <br>
                > It's the model's ability to avoid false positives.   
                """)
                st.latex(r"Precision = \frac{TP}{TP + FP}")

                st.markdown("""
                **Accuracy:**  
                > Measures the proportion of all correct predictions (true positives and <br>
                > true negatives) among all samples. It's a global measure of model performance.
                """)
                st.latex(r"Accuracy = \frac{TP + TN}{TP + TN + FP + FN}")

                st.markdown("""
                **Fβ-Score (including F1 and F2):**  
                > The Fβ-Score is a generalized harmonic mean of precision and recall.  
                > It adjusts the weight between recall and precision using the parameter β:
                >
                > - **F1-Score:** β = 1 → equal weight for precision and recall  
                > - **F2-Score:** β = 2 → recall is weighted four times higher  
                """)
                st.latex(
                    r"F_\beta = (1+\beta^2) \cdot \frac{\text{Precision} \cdot \text{Recall}}{\beta^2 \cdot \text{Precision} + \text{Recall}}"
                )

        with col2:
            with st.popover("**_INFO: Multi-Class Metrics_**"):
                st.markdown("""
                <span style="font-size:85%">
                >   
                > **Macro Average:**  
                > Unweighted mean of the metric across classes.    
                > $$\text{Macro-Avg} = \frac{1}{N}\sum_{i=1}^{N} \text{Metric}_i$$
                >
                > **Weighted Average:** 
                > where \(n_i\) = support for class \(i\)   
                > Mean of the metric weighted by the number of samples per class.    
                > $$
                > \text{Weighted-Avg} = \frac{\sum_{i=1}^{N} n_i \cdot \text{Metric}_i}{\sum_{i=1}^{N} n_i}
                > $$  
                >   
                >
                > **Micro Average:**  
                > Aggregates true positives, false positives, and false negatives globally 
                > across classes.     
                > $$ 
                > \text{Micro-Avg Precision} = \frac{\sum_{i} TP_{i}}{\sum_{i} (TP_{i} + FP_{i})} 
                > $$
                >
                > $$ 
                > \text{Micro-Avg Recall} = \frac{\sum_{i} TP_{i}}{\sum_{i} (TP_{i} + FN_{i})} 
                > $$
                > </span>
                """)

        with col3:
            with st.popover("**_INFO: Confusion Matrix_**"):
                st.markdown("""
                **Confusion matrix**
                > A confusion matrix shows how many samples of each true class were predicted as each class.  
                > - **Diagonal:** correct predictions  
                > - **Off-diagonal:** misclassifications  
                >
                > |              | Pred Class 0 | Pred Class 1 | Pred Class 2 | Pred Class 3 |
                > |--------------|-------------|--------------|--------------|--------------|
                > | **True 0**    | TP          | FP           | …            | …            |
                > | **True 1**    | FN          | TP           | …            | …            |
                > | **True 2**    | …           | …            | TP           | …            |
                > | **True 3**    | …           | …            | …            | TP           |

                """)

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("GradCAM images")
            # st.divider()

        with col2:
            with st.popover("**_INFO: GradCAM_**"):
                st.markdown(
                    """
                #### **(B) Grad-CAM heatmaps per image**
                > **📷 What is Grad-CAM?**  
                > <span style="font-size:85%">
                > **Gradient-weighted Class Activation Mapping (Grad-CAM)** is a visualization technique used to interpret Convolutional Neural Networks (CNNs).  
                > - It highlights the regions of an input image that contribute most to a model’s prediction for a specific class.  
                > - Uses the gradients of the target class flowing into the final convolutional layer to produce a **heatmap**.  
                >
                > **How it’s visualized:**  
                > - A colored heatmap is overlaid on the original X-ray image.  
                > - Warmer colors (red/yellow) indicate regions with stronger influence on the model’s decision.  
                > - Cooler colors (blue) indicate less relevant areas.  
                > </span>
                """,
                    unsafe_allow_html=True,
                )

            with st.popover("**_INFO 'Sparsity Score'_**"):
                st.markdown("""
                
                **🟦 What is Sparsity in Explanations?**  
                """)
                # st.divider()
                st.markdown("""
                ---
                **Sparsity** measures how focused or distributed a model’s explanation is over the input image.  
                  - High sparsity → The model relies on a **small, concentrated region** of the image.  
                  - Low sparsity → The model spreads its attention over **larger areas** of the image.  
                ---
                """)
                # st.divider()
                st.markdown("""
                **Mathematical intuition:**  
                Given a normalized heatmap :red[H] of width :red[W] and height :red[H\_i],  
                where :blue['Active Pixels'] are those above a chosen intensity threshold,  
                sparsity can be approximated as:
                """)
                st.latex(r"Sparsity = 1 - \frac{\text{Active Pixels}}{W \cdot H\_i}")
                # st.divider()
                st.markdown("""
                ---
                **How it’s visualized:**  
                  - Typically displayed as a **percentage or numeric score**  
                  - Helps compare how localized different explanations are.
                ---
                """)
                # st.divider()
                st.markdown(
                    """
                **How it is used here:**  
                Because many images often show homogeneous pixel distributions, and meaningful  
                comparison across thresholds is required during training, the formula above has been slightly adapted.  
                In our implementation, sparsity scores are additionally **divided by the applied threshold**,  
                making it easier to compare values at a glance.
                """,
                )

        with st.popover("Choose a stage"):
            opt_3 = st.multiselect(
                "The GradCAM images from what stage do you want to see?",
                [
                    "Initial",
                    "Fine_0",
                    "Fine_20",
                    "Fine_50",
                    "Fine_100",
                    "Fine_complete",
                    "DataAug_None",
                    "DataAug_smooth",
                    "DataAug_enhanced",
                ],
                default=None,
                max_selections=1,
                placeholder="Choose a stage (max. 1).",
            )

        option_map = {
            0: "COVID",
            1: "Lung Opacity",
            2: "Normal",
            3: "Viral Pneumonia",
        }

        select_3 = st.segmented_control(
            "**Choose a label**",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            key="GradCAM",
        )

        if not opt_3:
            st.warning("Please select a training stage.")

        if select_3 is None:
            st.warning("Please select a label")
            # st.write(f"You selected the stage ")
        if opt_3 and select_3:
            st.write(
                f"You selected the label **{option_map[select_3]}** at the stage **{opt_3}**"
            )

        # st.divider()
        # st.write(f"")
        # st.divider()

        sel_dict = {0: "covid", 1: "lung", 2: "normal", 3: "viral"}

        with st.expander("**GradCAM images**"):
            if opt_3 and (select_3 is not None):
                imgs = find_files(
                    GRADCAM, opt_3, extension=".png"
                )  # adapt if extended/incresed (see above)
                img = [img for img in imgs if sel_dict[select_3] in img.name]
                # st.write(f"DEBUG: {imgs}")
                # st.write(f"DEBUG: {img}")
                if not img:
                    st.warning("No matching image found for this label/stage.")

                image = load_image(img)
                if image:
                    for name, img in image:
                        st.image(img, caption=name, use_container_width=True)

            else:
                st.warning("Please complete your selection.")
                # st.write(f"DEBUG:  {opt_3} and {select_3}")

        with st.expander("**Sparsity scores**"):
            if opt_3 and (select_3 is not None):
                """
                imgs = find_files(GRADCAM, opt_3, extension=".png")                   # adapt if extended/incresed (see above)
                img = [img for img in imgs if sel_dict[select_3] in img.name]
                # st.write(f"DEBUG: {imgs}")
                # st.write(f"DEBUG: {img}")
                if not img:
                    st.warning("No matching image found for this label/stage.")

                image = load_image(img)
                if image:
                    for name, img in image:
                        st.image(img, caption=name, use_container_width=True)
                """
                st.write("to be added")
            else:
                st.warning("Please complete your selection.")
                # st.write(f"DEBUG:  {opt_3} and {select_3}")
        """ 
        my_df = pd.DataFrame()
            for stage in options:
                df = load_df(stage_best_hp[f"{stage}"])
                my_table.add_rows(df)

            st.table(my_df)
        """

    with tab4:
        st.subheader("SHAP images")
        st.divider()

        with st.popover("Choose a stage"):
            opt_4 = st.multiselect(
                "The run metrics from what stages you want to see?",
                [
                    "Initial",
                    "Fine_0",
                    "Fine_20",
                    "Fine_50",
                    "Fine_100",
                    "Fine_complete",
                    "DataAug_None",
                    "DataAug_smooth",
                    "DataAug_enhanced",
                ],
                default=None,
                max_selections=1,  # maybe increase!?
                placeholder="Choose a stage (max. 1).",
            )

        if not opt_4:
            st.warning("Please, select a training stage.")
        else:
            st.write(f"You selected the stage **{opt_4}**")

        option_map = {0: "COVID", 1: "Lung Opacity", 2: "Normal", 3: "Viral Pneumonia"}

        select_4 = st.segmented_control(
            "Choose a label",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",  # maybe extend to 'multiple'!?
            key="SHAP",
        )

        st.divider()
        # st.write(f"You selected:\t{None if select_4 is None else option_map[select_4]}.")
        # st.divider()

        sel_dict = {0: "covid", 1: "lung", 2: "normal", 3: "viral"}

        if select_4 is None:
            st.warning("Please, choose a label.")
        else:
            st.write(f"You selected the label **{option_map[select_4]} ({select_4})**")

        img_width = st.slider("Image width", 200, 600, 400)

        if (select_4 is not None) and opt_4:
            img_found = find_files(
                SHAP, opt_4, extension=".png"
            )  # adapt if extended/incresed (see above)
            img_list = [
                img
                for img in img_found
                if sel_dict[select_4].lower() in img.name.lower()
            ]
            # st.write(f"DEBUG: {img_found}")
            # st.write(f"DEBUG: {img_list.count()}")
            if not img_found:
                st.warning("No matching image found for this label/stage.")

            cols = st.columns(2)

            good_img = [f for f in img_list if "_good_" in f.name]
            bad_img = [f for f in img_list if "_bad_" in f.name]
            # st.write(f"DEBUG: {bad_img}")
            # st.write(f"DEBUG: {good_img}")

            g_images = load_image(good_img)
            b_images = load_image(bad_img)

            if g_images and b_images:
                with cols[0]:
                    st.subheader("Best Performer")
                    for img in g_images:
                        st.image(img, width=img_width)

                with cols[1]:
                    st.subheader("Worst Performer")
                    for img in b_images:
                        st.image(img, width=img_width)

            """
            for img in enumerate(image):
                with cols[i % 2]:
                    st.image(img, use_container_width=True)
            
            
            for img in img_list:
                name = img.stem.lower()
                for i, label in enumerate(["good", "bad"]):
                    if label in name:
                        with cols[i]:
                            # image = load_image(img)
                            st.image(str(img), caption=label, use_container_width=True)
            """
        else:
            st.warning("Please complete your selection.")
        """
        my_df = pd.DataFrame()
        for stage in options:
            df = load_df(stage_best_hp[f"{stage}"])
            my_table.add_rows(df)

        st.table(my_df)
        """


######
# START HERE
