import tensorflow.keras
import streamlit as st
import pandas as pd
import numpy as np
# import keras

from pathlib import Path
from PIL import Image
from tensorflow.keras import models, layers
from tensorflow.keras.applications import ResNet50
# from keras.api.models import load_model

stage_dict = {
    "Initial": "0_", 
    "Fine_0": "1_", 
    "Fine_20": "2_", 
    "Fine_50": "3_", 
    "Fine_100": "4_",
    "Fine_complete": "5_", 
    "DataAug_None": "6_", 
    "DataAug_smooth": "7_", 
    "DataAug_enhanced": "8_"
}

def get_model_without_augmentation(model):
    """Return a version of the model without data augmentation layers."""
    model_clean = models.Sequential()
    for layer in model.layers:
        if ("data_aug_" not in layer.name.lower()) and \
            ("data_augmentation" not in layer.name.lower()):
            model_clean.add(layer)

    return model_clean


@st.cache_data
def find_files(folder_path, stage_kw, extension=".csv"):
    """Find all files in a folder that contain a given keyword."""
    folder = Path(folder_path)
    if isinstance(stage_kw, str):
        stage_kw = [stage_kw]
    
    elif not stage_kw:
        return []
    
    kws = [stage_dict[f"{kw}"] for kw in stage_kw]
    candidates = [f for f in folder.glob(f"*{extension}") \
                    if f.is_file() and any(kw in f.name for kw in kws)]
    '''
    st.write("🔍 Folder:", folder)
    st.write("🔍 Keywords:", kws)
    st.write("🔍 Found files:", [f.name for f in folder.glob('*')])
    '''
    if not candidates:
        matching_dirs = [
                d for d in folder.iterdir()
                if d.is_dir() and any(kw in d.name for kw in kws)
                        ]

        candidates = []
        for d in matching_dirs:
            for f in d.glob(f"*{extension}"):
                if f.is_file():
                    candidates.append(f)

        # st.write(f"🔍 Folder: {matching_dirs}")
        # st.write(f"🔍 Keywords: {kws}")
        # st.write(f"🔍 Found candidates: {len(candidates)}")

        if not candidates:
            return []

        return candidates

    return candidates
    
@st.cache_data
def load_df(file_path, extension=".csv"):
    if extension == ".csv":
        df = pd.read_csv(file_path)
    
    elif extension == ".html":
        df = pd.read_html(file_path)[0]

    else:
        None

    return df

@st.cache_data
def load_image(file_path, extension=".png"):
    """
    Load multiple PNG images safely and return a list of PIL.Image objects.

    Parameters
    ----------
    file_list : list[Path]
        List of image file paths.
    extension : str, optional
        File extension to match (default: '.png').

    Returns
    -------
    list[PIL.Image.Image]
        Loaded images (only valid, readable ones).
    """
    if file_path is None:
        return None
    
    images = []
    for f in file_path:
        try:
            path = Path(f)
            if path.suffix.lower() == extension.lower() and path.is_file():
                img = Image.open(path).convert("RGB")
                images.append((path.name, img))
            
            else:
                st.warning(f"⚠️ File not found or wrong extension: {path}")

        except Exception as e:
            st.warning(f"⚠️ Could not load image: {f} ({e})")

    if len(images) == 0:
        return None
    else:
        return images


@st.cache_resource
def load_model(path: str):
    try:
    #     # Keras 3+ (new API)
    #     model = load_model(path, safe_mode=False)
    #     st.success("✅ Model loaded successfully.")
    # except TypeError:
        # Fallback for Keras 2.x style
        from tensorflow.keras.models import load_model as tf_load_model
        model = tf_load_model(path) #, compile=False)
        st.success("✅ Model loaded with Keras 2.x loader.")
    except Exception as e:
        st.warning(f"⚠️ Could not fully load model graph, rebuilding sequentially. ({e})")
        # Optional fallback:
        base = ResNet50(include_top=False, weights="imagenet", input_shape=(224,224,3))
        model = models.Sequential([
            base,
            layers.GlobalAveragePooling2D(),
            layers.Dense(512, activation='relu', name="dense_top"),
            layers.Dropout(0.3),
            layers.Dense(4, activation='softmax')
        ])
        model.load_weights(path)
    return model
    # return keras_load_model(path, compile=compile)

'''
@st.cache_data
def load_image(file, size=(224, 224)):
    img = Image.open(file).convert("RGB").resize(size)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr

sys.path = [
    '/workspaces/may25_bds_covid19/streamlit',
    '/home/codespace/.python/current/lib/python312.zip',
    '/home/codespace/.python/current/lib/python3.12',
    '/home/codespace/.python/current/lib/python3.12/lib-dynload',
    '/workspaces/may25_bds_covid19/streamlit/venv_app/lib/python3.12/site-packages',
]
USER_BASE: '/home/codespace/.local' (exists)
USER_SITE: '/home/codespace/.local/lib/python3.12/site-packages' (exists)
ENABLE_USER_SITE: False

streamlit/app/static_files/GradCam/5_GradCAM_viral_all_layer.png
'''
 