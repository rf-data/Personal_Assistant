import streamlit as st
from pathlib import Path

from app.utils.loader import load_model
from app.utils.predict import image_classification

def show():
    st.header("🎯 Prediction")

    labels = ["covid", "lung", "normal", "viral"]

    MODEL_PATH = Path("/workspaces/may25_bds_covid19/streamlit/models/2025-07-23_06-26_DataAug_enhanced_msk_multi_LR_5e-5_best_model.keras")
   #  /workspaces/may25_bds_covid19/streamlit/models/2025-07-22_17-43_DataAug_enhanced_msk_multi_LR_3e-5_best_model.keras")

    if "selected_image_path" in st.session_state:
        img_path = Path(st.session_state["selected_image_path"])
        # st.info(f"Using selected image:\t\t{img_path.name}")
        
        col1, col2 = st.columns(2)

        with col1:        
            st.markdown("**Image**")
            st.image(img_path, caption=img_path.name, use_container_width=True) #"Uploaded image") 

        with col2:        
            st.markdown("**Predictions**")
            if st.button("🎯 Run Prediction"):
                model = load_model(MODEL_PATH)
                try:
                    df_result = image_classification(model, img_path, class_names=labels)
                    st.dataframe(df_result)

                    st.success(f"✅ Predicted class: {df_result.loc[0, 'pred_label']} "
                    f"({df_result.loc[0, 'pred_proba']:.2%})")

                except Exception as e:
                    st.write(f"An error occured: {e}")
            

    
        # st.bar_chart(df_result["proba_vector"].T)    #         pred = infer(model, )

    #         st.image(img_path, caption="Selected Image", use_column_width=True)

    # if st.button("🎯 Run Prediction"):
    #     df_result = image_classification(model, img_path, class_names=labels)
    #     st.dataframe(df_result)

    #     st.success(f"✅ Predicted class: {df_result.loc[0, 'pred_label']} "
    #                f"({df_result.loc[0, 'pred_proba']:.2%})")