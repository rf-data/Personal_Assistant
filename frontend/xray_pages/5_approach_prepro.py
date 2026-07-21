##

import streamlit as st

tab1, tab2, tab3 = st.tabs(["General Approach", "Preprocessing", "Training steps"])

with tab1:
    st.markdown("""
    In our setup, the convolutional base of ResNet50 was initially frozen to retain its learned feature representations. A custom classification head
    > consisting of global average pooling, dropout, and one dense layer was appended to adapt the model to our four-class prediction task: COVID,
    > LUNG_OPACITY, NORMAL, and VIRAL_PNEUMONIA.

    ### **Balanced Sampling and Experimental Design**
    > To avoid learning class-specific probabilities from imbalanced data, the model was trained using a balanced dataset. The original class distribution
    > was highly skewed (e.g., ~10,000 normal images vs. ~1,300 viral pneumonia cases). Therefore, the initial training subset was limited in size to ensure
    > that even after two planned dataset enlargements, the total sample size remained close to the smallest class.
    > In the initial sampling, 800 images per class were drawn using simple random sampling with replacement (SRS_replace, seed=42). In the second and third
    > sampling stages, 400 additional images per class were added, using seeds 321 and 123, respectively.
    > The data was split into training and validation sets using an 80:20 ratio, while maintaining class balance. A 60:40 split was also tested in the
    > initial training phase but yielded worse results (see section 4.1).
    > For the final test stage, the full dataset was used. This allowed us to evaluate the model's generalization ability and quality of the training scheme
    > applied (as follows), as approximately 70% of the data had not been used during training or validation.
    """)

with tab2:
    st.markdown("""
    > Before feeding images into the ResNet50 model, we applied the preprocessing function `keras.applications.resnet50.preprocess_input()`. This function is
    > essential to align the input image values with the statistical expectations of the pretrained ResNet50 model.
    > Specifically, it:
    > - Converts image pixel values from RGB format to the format expected by ResNet50 (BGR channel order)
    > - Subtracts the mean RGB values computed on the ImageNet training set
    > - Ensures that input values match the scale and distribution the model was originally trained on
    >
    > This step is critical when using pretrained models, as discrepancies in input distributions can significantly affect model performance.
    > Even though our dataset contains grayscale chest X-ray images, the use of `preprocess_input()` remains essential. These images are typically replicated
    > into three identical RGB channels before being fed into the model. Applying ImageNet-style normalization ensures compatibility with the pretrained
    > ResNet50 model and prevents inconsistencies in how the early convolutional layers process the input. Without this preprocessing, transfer learning
    > would be less effective and convergence during training might be impaired.
    """)

with tab3:
    st.markdown(
        """
    #### **Initial Training**
    > We trained a frozen ResNet50 model with a custom dense classification head on a limited dataset. Hyperparameter tuning was applied to the dense layer
    > size (???), dropout rate (???), and initial learning rate (). Batch sizes of 16, and 32 were tested after the data set has been divided 80:20 and
    > 60:40, respectively. After a 80:20 split, the dataset was also tested with a larger batch size (64) and feeded with smoothly augmented data,
    > respectively (RandomContrast: 0.05, RandomBrightness: 0.05, RandomZoom: 0.03, RandomRotation: 0.02)
    > The best results were obtained by using:
    > →  dataset split: 80:20 (training:validation), batch size 32
    > → ??? Hyperparameter
    > [...]

    #### **Fine tuning - Part 1 (Increased Data, Still Frozen)**
    > The best model from initial training was now trained with a larger subset of the dataset to investigate the isolated effect of more training data. No
    > layers were unfrozen, but different hyperparameter settings of the applied callbacks `‘ReduceLearnRateOnPLateau’` and `‘EarlyStopping’` were tested
    > using KerasTuner.
    [...]

    #### **Fine tuning - Part 2 (Last 20 Layers Unfrozen)**
    > We partially unfroze the ResNet50 model, training the top 20 layers in addition to the classification head. Callbacks for early stopping and reducing
    > learning rate were used to stabilize training.
    > In this setup, we included the following representative convolutional layers ("block_layer") as trainable:
    > - <span style="color:#008000;">`conv4_block6_3_conv` _(new)_</span>
    > - <span style="color:#008000;">`conv5_block1_3_conv` _(new)_</span>
    > - <span style="color:#008000;">`conv5_block3_3_conv` _(new)_</span>
    >
    > These layers are part of the deeper stages of the network and contribute significantly to high-level feature extraction, which is especially relevant
    > when adapting to domain-specific patterns in chest X-ray images.
    [...]

    #### **Fine tuning - Part 3 (Last 50 Layers Unfrozen)**
    > This experiment extended fine-tuning further by unfreezing the last 50 layers of the ResNet50 model. In this configuration, most of the deeper
    > convolutional blocks were allowed to adapt to the CXR data.
    > Relevant trainable layers from the block_layer list are now included:
    > - <span style="color:#00AA00;">`conv3_block4_3_conv` _(new)_</span>
    > - <span style="color:#008000;">`conv4_block1_3_conv` _(new)_</span>
    > - `conv4_block6_3_conv` _(previously unfrozen)_
    > - `conv5_block1_3_conv` _(previously unfrozen)_
    > - `conv5_block3_3_conv` _(previously unfrozen)_
    >
    > This strategy allowed for more complex adaptation, though it increased the risk of overfitting and required careful regularization and learning rate
    > scheduling.


    #### **Fine tuning - Part 4 (Last 100 Layers Unfrozen)**
    > To push the adaptation further, the final 100 layers were set to trainable. This allowed more than a half of all convolutional blocks from the
    > ResNet50 architecture to learn from the X-Ray data. Included block_layer components:
    > - <span style="color:#008000;">`conv2_block3_3_conv` _(new)_</span>
    > - <span style="color:#008000;">`conv3_block1_3_conv` _(new)_</span>
    > - `conv3_block4_3_conv` _(previously unfrozen)_
    > - `conv4_block1_3_conv` _(previously unfrozen)_
    > - `conv4_block6_3_conv` _(previously unfrozen)_
    > - `conv5_block1_3_conv` _(previously unfrozen)_
    > - `conv5_block3_3_conv` _(previously unfrozen)_
    >
    > This deeper unfreezing made the model more flexible and expressive but also required longer training time and stronger regularization.


    #### **Fine-Tuning - Part 5 (All layers unfrozen)**
    > In this final fine-tuning variant, the entire ResNet50 model was unfrozen—including the early convolutional layers in the last 75 layers. This allows
    > full adaptation of all model parameters to the specific data domain. All block_layer components were trainable:
    > - <span style="color:#008000;">`conv1_conv`     &nbsp;&nbsp;&nbsp;&nbsp; _(new)_</span>
    > - <span style="color:#008000;">`conv2_block1_3_conv` _(new)_</span>
    > - `conv2_block3_3_conv` _(previously unfrozen)_
    > - `conv3_block1_3_conv` _(previously unfrozen)_
    > - `conv3_block4_3_conv` _(previously unfrozen)_
    > - `conv4_block1_3_conv` _(previously unfrozen)_
    > - `conv4_block6_3_conv` _(previously unfrozen)_
    > - `conv5_block1_3_conv` _(previously unfrozen)_
    > - `conv5_block3_3_conv` _(previously unfrozen)_
    >
    > While full unfreezing maximizes representational power, it also increases the risk of catastrophic forgetting of pretrained features and requires the
    > most careful training configuration among all strategies.


    #### **Data Augmentation Experiments**
    > We compared three levels of augmentation:
    > - `DataAug_none`: No augmentation but additional samples
    > - `DataAug_smooth`: Mild brightness/contrast/rotation
    > - `DataAug_enhanced`: Stronger and combined transformations

    TABLE_WITH_SETTINGS
    These strategies were applied subsequently to the same model setup to isolate the effect of input variability and .

    """,
        unsafe_allow_html=True,
    )
