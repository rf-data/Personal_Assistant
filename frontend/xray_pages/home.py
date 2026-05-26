import streamlit as st


def show():
    # st.header("🏠 Home")
    st.set_page_config(page_title="COVID-19 Chest X-Ray Classification", layout="wide")

    st.subheader("🏠 X-Ray Classification app")
    st.markdown("""
    #### Multiclass classification of thorax X-ray images by using the convolutional neural network ResNet 50 
    """)
