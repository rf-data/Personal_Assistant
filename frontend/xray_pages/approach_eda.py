
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns

from pathlib import Path
from PIL import Image

EDA = Path("/workspaces/may25_bds_covid19/streamlit/app/static_files/eda_files")
    
def show():
    
    st.header("📊 Approach and EDA")
    st.write("Welcome to the COVID-19 X-Ray Classification app!")

    tab1, tab2 = st.tabs(["Methodical approach", 
                           "EDA"])

    with tab1:
        st.subheader("Balanced Sampling and Experimental Design")
        st.markdown("""
        To avoid learning class-specific probabilities from imbalanced data, the model was trained using a balanced dataset. The original class distribution
        was highly skewed (e.g., ~10,000 'normal' images vs. ~1,300 'viral pneumonia' cases). Therefore, the initial training subset was limited in size to ensure
        that even after two planned dataset enlargements**, the total sample size remained close to the smallest class.
        In the **initial sampling**, **800 images per class** were drawn using simple random sampling with replacement (**SRS_replace**, seed=42). In the second and third
        sampling stages, **400 additional images** per class were added, using seeds 321 and 123, respectively.
        The data was split into training and validation sets using an 80:20 ratio, while maintaining class balance. A 60:40 split was also tested in the
        initial training phase but yielded worse results.
        For the final test stage, the full dataset was used. This allowed us to evaluate the model's generalization ability and quality of the training scheme
        applied (as follows), as approximately 70% of the data had not been used during training or validation.
                """)

    with tab2:
        # st.subheader("📊 Explore Data")

        ## preparation: 
        # load images
        img = Image.open(os.path.join(EDA, "img_covid_1.png"))
        mask = Image.open(os.path.join(EDA, "mask_covid_1.png"))
        img_array = np.array(img)
        mask_array = np.array(mask)
        
        # load metadata as df
        covid_df = pd.read_excel(os.path.join(EDA, "COVID.metadata.xlsx"), sheet_name="Sheet1")
        lung_opacity_df = pd.read_excel(os.path.join(EDA, "Lung_Opacity.metadata.xlsx"), sheet_name="Sheet1")
        normal_df = pd.read_excel(os.path.join(EDA, "Normal.metadata.xlsx"), sheet_name="Sheet1")
        viral_pneumonia_df = pd.read_excel(os.path.join(EDA, "Viral Pneumonia.metadata.xlsx"), sheet_name="Sheet1")

        # Add new columns for grouping purposes
        covid_df["dataset"] = "COVID"
        lung_opacity_df["dataset"] = "Lung Opacity"
        normal_df["dataset"] = "Normal"
        viral_pneumonia_df["dataset"] = "Viral Pneumonia"

        data = pd.concat(
                    [covid_df, lung_opacity_df, normal_df, viral_pneumonia_df],
                    ignore_index=True
                    )

        num_images = {
                "COVID": len(covid_df),
                "Lung Opacity": len(lung_opacity_df),
                "Normal": len(normal_df),
                "Viral Pneumonia": len(viral_pneumonia_df),
                    }

        ### PART 1
        with st.popover("**(A) Dataset analysis**"):        
            st.markdown(f"""
        - **COVID dataset:**\t--> {covid_df.shape[0]} x-ray images\t ({covid_df.isna().sum().sum()} null-values) 
        - **Lung Opacity dataset:**\t-->{lung_opacity_df.shape[0]} x-ray images\t ({lung_opacity_df.isna().sum().sum()} null-values)
        - **Normal dataset:**\t--> {normal_df.shape[0]} x-ray images\t ({normal_df.isna().sum().sum()} null-values) 
        - **Viral Pneumonia dataset:**\t--> {viral_pneumonia_df.shape[0]} x-ray images\t ({viral_pneumonia_df.isna().sum().sum()} null-values)
        
        
                    """)

            fig_1 = plt.figure(figsize=(20, 10))
            plt.title("Overall Distribution of Images")
            sns.countplot(
                x="dataset",
                data=data,
                order=num_images.keys(),
                palette="viridis",
                hue="dataset",
                )
            plt.xlabel("")
            plt.ylabel("Number of Images")
            st.pyplot(fig_1)

        ### PART 2
        # st.divider()
        with st.popover("**(B) Analysis of images and masks**"):
            st.markdown(f"""
        - image size: {img.size}
        - image format: {img.format}
        - image mode: {img.mode}
        - mask size: {mask.size}
        - mask format: {mask.format}
        - mask mode: {mask.mode}

        Exemple image and mask:
                    """)
        
            # Display example image + mask
            fig_2 = plt.figure(figsize=(12, 12))

            # Display the image
            ax0 = fig_2.add_subplot(1, 2, 1)
            ax0.imshow(img_array, cmap="gray")
            ax0.set_title("(a) COVID-19 Chest X-ray Image")
            ax0.axis("off")

            # Display the mask
            ax1 = fig_2.add_subplot(1, 2, 2)
            ax1.imshow(mask_array, cmap="gray")
            ax1.set_title("(b) COVID-19 Chest X-ray Mask")
            ax1.axis("off")
            st.pyplot(fig_2)

            fig_3 = plt.figure(figsize=(6, 3))
            sns.countplot(
                x="dataset",
                data=data,
                order=num_images.keys(),
                palette="viridis",
                hue="dataset",
                    )
            plt.xlabel("")
            plt.ylabel("Number of Images")
            # fig.tight_layout()
            st.pyplot(fig_3)
            