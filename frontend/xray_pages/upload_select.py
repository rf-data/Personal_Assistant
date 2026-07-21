from pathlib import Path

import streamlit as st
from PIL import Image

# ===== CONFIG =====
UPLOAD_DIR = Path("/workspaces/may25_bds_covid19/streamlit/app/static_files/uploads")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===== MAIN FUNCTION =====
def show():
    st.header("🖼️ Upload & Select X-ray Image")
    st.write(
        "**Upload an image, browse available files, and select one for prediction and/or visualization.**"
    )

    types_allowed = [".jpg", ".jpeg", ".png"]

    # --- File browser section ---
    image_files = sorted(
        [f for f in UPLOAD_DIR.iterdir() if f.suffix.lower() in types_allowed]
    )

    st.markdown("#### 📂 Available Images in Folder")
    if image_files:
        # st.subheader("📂 Available Images in Folder")

        # Show small previews in grid
        with st.expander("Preview"):
            cols = st.columns(3)
            for i, file in enumerate(image_files):
                with cols[i % 3]:
                    img = Image.open(file)
                    st.image(img, caption=file.name, use_container_width=True)

    else:
        st.info("No X ray image available so far.")

    st.markdown("---")

    # --- Upload section ---
    uploaded_file = st.file_uploader("📤 Upload an image file", type=types_allowed)

    if uploaded_file:
        # Pfad vorbereiten
        file_path = UPLOAD_DIR / uploaded_file.name
        file_suffix = Path(uploaded_file.name).suffix.lower()

        if file_suffix not in types_allowed:
            st.error(f"❌ Unsupported file type: {file_suffix}")
        else:
            # --- 2️⃣ Doppelte Dateien verhindern ---
            if file_path.exists():
                st.warning(
                    f"⚠️ File '{uploaded_file.name}' already exists in upload folder."
                )
            else:
                # --- 3️⃣ Datei speichern ---
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ File '{uploaded_file.name}' saved successfully!")

                # Vorschau anzeigen
                st.image(file_path, caption="Uploaded image")  # use_column_width=True)

        if Path(uploaded_file.name).suffix.lower() in types_allowed:
            if Path(uploaded_file.name) not in image_files:
                save_path = UPLOAD_DIR / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

        #         st.success(f"✅ File '{uploaded_file.name}' saved.")
        #         st.image(save_path, caption="Uploaded Image Preview", use_container_width=False)

        #     else:
        #         st.warning(f"⚠️ **This image has already been uploaded.") # uploaded file has not the right format
        # else:
        #     st.warning(f"⚠️ **The uploaded file has not the right format: ({Path(uploaded_file.name).suffix.lower()})**")

    st.markdown("---")

    # --- Selection section ---
    selected_file = st.selectbox(
        "🎯 Choose an image for prediction:",
        options=[f.name for f in image_files],
        index=None,
        placeholder="Select a file...",
    )

    if selected_file:
        chosen_path = UPLOAD_DIR / selected_file
        st.success(f"✅ Selected file: {selected_file}")
        st.image(chosen_path, caption="Selected image")  # , use_column_width=True)

        # Placeholder for downstream processing
        st.session_state["selected_image_path"] = str(chosen_path)

        # Buttons for actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔮 Predict"):
                st.session_state["trigger_prediction"] = True
                st.info("Prediction triggered... (call your model here)")

        with col2:
            if st.button("🌈 Grad-CAM"):
                st.session_state["trigger_gradcam"] = True
                st.info("Grad-CAM visualization started...")

        with col3:
            if st.button("🔍 SHAP"):
                st.session_state["trigger_shap"] = True
                st.info("SHAP explanation started...")

    else:
        st.info("📁 No images selected. Please select an image or upload a new one.")


# def show():
#     st.header("Upload and select an image")

#


#     uploaded_files = st.file_uploader(
#     "Upload data", accept_multiple_files=False, type=types_allowed
#     )

# for uploaded_file in uploaded_files:
#     df = pd.read_csv(uploaded_file)
#     st.write(df)
