def image_GRADCAM(
    image, model, layer_name, target_class_idx=None, return_overlay=False
):
    """Computes Grad-CAM heatmap for given image and layer."""
    resnet = model.get_layer("resnet50")
    resnet.trainable = True
    try:
        target_layer = resnet.get_layer(layer_name)
        target_output = target_layer.output
    except ValueError:
        print(f"❌ Layer '{layer_name}' not found in resnet50 – skipping")
        return None, None

    if not model.built or not hasattr(model, "input"):
        _ = model(tf.zeros((1, 224, 224, 3)))

    grad_model = Model(inputs=resnet.input, outputs=target_output)

    if not isinstance(image, tf.Tensor):
        image = tf.convert_to_tensor(image, dtype=tf.float32)
    if len(image.shape) == 3:
        image = tf.expand_dims(image, axis=0)
    elif len(image.shape) != 4:
        raise ValueError(f"Unexpected image shape: {image.shape}")

    with tf.GradientTape() as tape:
        tape.watch(image)
        conv_outputs = grad_model(image)
        if conv_outputs is None:
            print(f"❌ conv_outputs is None at layer: {layer_name}")
            return None, None

        x = tf.keras.layers.GlobalAveragePooling2D()(conv_outputs)
        x = tf.keras.layers.Dense(512, activation="relu", name="dense_second_last")(x)
        x = tf.keras.layers.Dropout(0.3, name="dropout_class_multi")(x, training=False)
        preds = tf.keras.layers.Dense(4, activation="softmax", name="dense_last")(x)
        if target_class_idx is None:
            target_class_idx = tf.argmax(preds[0])
        loss = preds[:, target_class_idx]

    grads = tape.gradient(loss, conv_outputs)
    if grads is None:
        print(f"❌ No gradients found for class={target_class_idx}, layer={layer_name}")
        return None, None

    conv_outputs = conv_outputs[0]
    grads = grads[0]
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1))

    if conv_outputs.shape[-1] != pooled_grads.shape[0]:
        print(f"❌ Shape mismatch in GradCAM at layer={layer_name}")
        return None, None

    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
    if heatmap is None or tf.reduce_max(heatmap) == 0:
        print(f"⚠️ Empty heatmap generated in layer '{layer_name}' – skipping")
        return None, None

    heatmap = tf.maximum(heatmap, 0)
    heatmap /= tf.reduce_max(heatmap) + 1e-8
    heatmap = heatmap.numpy()
    heatmap_resized = tf.image.resize(
        heatmap[..., np.newaxis], (image.shape[1], image.shape[2])
    ).numpy()
    return np.squeeze(heatmap_resized), target_class_idx


def image_SHAP(image, model, class_names, save_path=None, verbose=False):
    """Compute SHAP values for a single image."""
    if isinstance(image, str):
        image = load_image_from_path(image).numpy()
    elif isinstance(image, tf.Tensor):
        image = image.numpy()

    if image.ndim == 4:
        image = image[0]
    elif image.ndim == 2 or (image.ndim == 3 and image.shape[-1] != 3):
        raise ValueError(f"❌ Invalid image shape: {image.shape}")

    masker = shap.maskers.Image("blur(64, 64)", image.shape)
    explainer = shap.Explainer(cpu_model, masker, output_names=class_names)

    img_exp = np.expand_dims(image, axis=0)
    shap_values = explainer(
        img_exp,
        max_evals=1000,
        batch_size=16,
        outputs=shap.Explanation.argsort.flip[:4],
    )

    shap.image_plot(shap_values, show=False)
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight", pad_inches=0.1)

    if verbose:
        plt.show()
    else:
        plt.close()

    sparsity_dict = compute_sparsity(shap_values, threshold=None, mode="SHAP")
    return shap_values, sparsity_dict
