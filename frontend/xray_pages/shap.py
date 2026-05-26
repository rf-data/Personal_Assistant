from pathlib import Path

import streamlit as st


# ===== MAIN FUNCTION =====
def show():
    st.header("🔍 SHAP Explanation")
    # st.write("Upload an image, browse available files, and select one for prediction and/or visualization.")

    if "selected_image_path" in st.session_state:
        img_path = Path(st.session_state["selected_image_path"])
        #         st.info(f"Using selected image: {img_path.name}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Image**")
            st.image(
                img_path, caption=img_path.name, use_container_width=True
            )  # "Uploaded image")

        with col2:
            st.markdown("**SHAP**")
