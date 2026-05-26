## page 3
import streamlit as st


def show():
    st.header("🏠 Objectives")
    st.write("Welcome to the COVID-19 X-Ray Classification app!")


st.title("Objectives for the model development")

st.markdown("""
In our setup, the convolutional base of ResNet50 was initially frozen to retain its learned feature representations. A custom classification head
consisting of global average pooling, dropout, and one dense layer was appended to adapt the model to our four-class prediction task: COVID,
LUNG_OPACITY, NORMAL, and VIRAL_PNEUMONIA.
In addition to the main objective of training a deep learning model, the following secondary goals were defined:
- **_Enable future improvements of ResNet-based pipelines:_**
  * Identify "Good" and "Bad Performers" early on for targeted refinement.
  * Search for differences between both groups 
- **_Apply the principle of minimal input:_**
  * Achieve satisfactory results with as few training samples as possible.
  * Smaller training subsets allow more experiments and longer training per run.
- **_Develop internal model indicators beyond standard metrics:_**
  * Use model interpretability techniques (GradCAM and SHAP) to visualize important regions.
  * Quantify these visual explanations by calculating modified sparsity scores.
  * These scores offer an additional layer of insight when evaluating model quality (see also: 'Evaluation of Good and Bad Performers').
""")
