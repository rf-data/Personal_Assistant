## st_eda_helper.py
# import
import numpy as np
import streamlit as st


# **Column names:**  {list(df.columns)}\n

def st_df_profile(df):

    num_feats = set(df.select_dtypes(include=[np.number]).columns.tolist())
    cat_feats = set(df.select_dtypes(exclude=[np.number]).columns.tolist())
    
    st.markdown(f"""
## DATASET PROFILE\n
**Row count:** {df.shape[0]:,}  \t|  **Column count:** {df.shape[1]}\n
**Count 'numeric columns' 📊 :** {len(num_feats)} \n
""")
    for feat in num_feats:
        st.markdown(f"- {feat}")

    st.markdown(f"**Count 'categorical columns' 🔤 :** {len(cat_feats)}") 
    for feat in cat_feats:
        st.markdown(f"- {feat}")
    st.markdown(f"""
**Memory usage:** {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB

### Head
""")    
    df_head = df.head(5).T  # if config["df_transponse"] else df.head(5)
    st.dataframe(df_head)
    # st.markdown("\n### Summary """)
