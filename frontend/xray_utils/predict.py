import numpy as np


def image_classification(model, image_path, class_names=None, target_size=(224, 224)):
    """
    Classify a single image and return a DataFrame with predictions and probabilities.

    Parameters
    ----------
    model : keras.Model
        Trained model used for prediction.
    image_path : str | Path
        Path to the image file.
    class_names : list[str], optional
        List of class labels corresponding to model output indices.
    target_size : tuple[int, int]
        Image resize dimensions (default: (224, 224)).

    Returns
    -------
    pd.DataFrame
        DataFrame containing predicted class, probability vector, and top-1 probability.
    """
    image_path = Path(image_path)
    img = keras_image.load_img(image_path, target_size=target_size)
    img_array = keras_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0  # normalize

    # Predict
    proba = model.predict(img_array, verbose=0)[0]
    pred_idx = int(np.argmax(proba))
    pred_proba = float(np.max(proba))
    pred_label = class_names[pred_idx] if class_names else str(pred_idx)

    # Optional: extract "true label" from filename
    # try:
    #     true_label = str(image_path.name).split("_")[0]
    # except Exception:
    #     true_label = None

    # Build result DataFrame
    df_clf = pd.DataFrame(
        [
            {
                "filename": image_path.name,
                "true_label": true_label,
                "pred_label": pred_label,
                "pred_idx": pred_idx,
                "pred_proba": pred_proba,
                "proba_vector": proba.tolist(),
            }
        ]
    )

    return df_clf


# def predict_image(model, image_array):
#     image_array = np.expand_dims(image_array, axis=0)  # batch dimension
#     preds = model.predict(image_array)
#     classes = ["Normal", "Viral Pneumonia", "COVID-19"]
#     return classes[np.argmax(preds)]


# CLASSES = ["Normal", "Viral Pneumonia", "COVID-19"]

# def infer(model, image_arr):
#     x = np.expand_dims(image_arr, axis=0)
#     proba = model.predict(x, verbose=0)[0]
#     idx = int(np.argmax(proba))
#     return {"label": CLASSES[idx], "proba": float(proba[idx]), "proba_vec": proba.tolist()}
