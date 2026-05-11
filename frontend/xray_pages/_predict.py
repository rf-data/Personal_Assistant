import streamlit as st
from app.utils.loader import load_model, load_image
from app.utils.predict import infer

st.header("🔮 Make Prediction")

uploaded = st.file_uploader("Upload a chest X-ray", type=["png","jpg","jpeg"])
model_path = st.text_input("Model path", "models/covid_model.h5")

if uploaded and model_path:
    img = load_image(uploaded, size=(224, 224))
    st.image((img * 255).astype("uint8"), caption="Uploaded", use_container_width=True)
    model = load_model(model_path)
    out = infer(model, img)
    st.success(f"Prediction: **{out['label']}** (p={out['proba']:.2f})")
