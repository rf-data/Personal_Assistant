import streamlit as st


def show():
    st.header("📊 Study design")
    st.write("Welcome to the COVID-19 X-Ray Classification app!")

    # ======== STYLE ADAPTION ========
    st.markdown(
        """
        <style>
        /* Breitere Popover-Fenster */
        [data-testid="stPopoverContent"] {
            width: 750px !important;           /* Standard ~320px → jetzt 750px */
            max-width: 90vw !important;        /* Begrenzung auf Viewport */
            white-space: pre-wrap !important;  /* automatische Zeilenumbrüche */
            word-break: break-word !important;
            overflow-x: auto !important;       /* erlaubt horizontales Scrollen bei Bedarf */
        }

        /* Optional: Code-Blöcke im Popover etwas kompakter */
        [data-testid="stPopoverContent"] pre {
            font-size: 0.85rem !important;
            line-height: 1.3 !important;
            background-color: #1e1e1e !important;
            color: #dcdcdc !important;
            border-radius: 8px;
            padding: 0.8em;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # ======== CONTENT ========
    tab1, tab2 = st.tabs(["Preprocessing", "Training design"])

    with tab1:
        st.subheader("Preprocessing")
        st.markdown("""
            Before feeding images into the ResNet50 model, we applied the preprocessing function `keras.applications.resnet50.preprocess_input()`. This function is
            essential to align the input image values with the statistical expectations of the pretrained ResNet50 model.
            Specifically, it:
            - Converts image pixel values from RGB format to the format expected by ResNet50 (BGR channel order)
            - Subtracts the mean RGB values computed on the ImageNet training set
            - Ensures that input values match the scale and distribution the model was originally trained on

            This step is critical when using pretrained models, as discrepancies in input distributions can significantly affect model performance.
            Even though our dataset contains grayscale chest X-ray images, the use of `preprocess_input()` remains essential. These images are typically replicated
            into three identical RGB channels before being fed into the model. Applying ImageNet-style normalization ensures compatibility with the pretrained
            ResNet50 model and prevents inconsistencies in how the early convolutional layers process the input. Without this preprocessing, transfer learning
            would be less effective and convergence during training might be impaired.
            """)

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
                        #### *(A) Preparing the dataset*
                        """)
            with st.expander("**build_ds(??)**"):
                st.code(
                    """
def build_ds:
    '''Builds a frozen ResNet50 model for initial hyperparameter tuning.'''
                ??
                Insert the correct function
                ???
                        return model
                    """,
                    language="python",
                )

        with col2:
            st.markdown("""
                            #### *(B) Setting up a Keras Tuner model*
                            """)

            with st.popover("setup_kt_model(config, mode)"):
                st.code(
                    """
                            def setup_kt_model(config, mode):
                                '''Sets up a KerasTuner model and logging environment.'''
                                from configuration.paths import TUNER, LOGS

                                tz = pytz.timezone('Europe/Berlin')
                                now = datetime.now(tz).strftime("%Y-%m-%d_%H-%M")
                                csv_path = os.path.join(LOGS, f'CSV_Logger/{now}_{config.RUN_NAME}_TrainLog.csv')
                                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                                base_callbacks.append(CSVLogger(csv_path, append=True))

                                if config.STAGE == "Initial":
                                    build_fn = build_model_init
                                    hist_path = os.path.join(LOGS, f"{now}_{config.RUN_NAME}_history")
                                elif config.STAGE in ("Fine", "DataAug", "Val"):
                                    build_fn = build_model_fine
                                    hist_path = os.path.join(LOGS, f"{now}_{config.RUN_NAME}_history")
                                else:
                                    raise ValueError("Unknown STAGE mode.")

                                hypermodel = MyHyperModel(build_fn=build_fn, save_history_path=hist_path)
                                tuner = MyBayesTuner(
                                    hypermodel,
                                    objective=config.OBJECTIVE,
                                    max_trials=config.MAX_TRIALS,
                                    executions_per_trial=config.EXE_PER_TRIAL,
                                    directory=os.path.join(TUNER, f'multi_{config.STAGE}'),
                                    project_name=f"{now}_{config.RUN_NAME}",
                                    mode=config.STAGE
                                )

                                param_log = {
                                    "run_name": config.RUN_NAME,
                                    "stage": config.STAGE,
                                    "start_time": now,
                                    "label_mode": config.LABEL_MODE,
                                    "objective": config.OBJECTIVE,
                                    "objective_mode": config.OBJECTIVE_MODE,
                                    "objective_es_thresh": config.OBJECTIVE_ES_THRESH,
                                    "max trials": config.MAX_TRIALS,
                                    "executions per trial": config.EXE_PER_TRIAL,
                                    "epochs": config.EPOCHS,
                                    "initial_epoch": getattr(config, "INITIAL_EPOCH", None),
                                    "batch_size": getattr(config, "BATCH_SIZE", None),
                                    "initial_learning_rate": getattr(config, "INIT_LR", None),
                                    "unfrozen_layers": getattr(config, "UNFROZEN_LAYERS", None),
                                    "tuning_parameters": getattr(config, "TUNING_PARAMS", None),
                                    "augmentation": getattr(config, "AUG_SETTING", None),
                                    "reduce_lr": dict(config.LR_REDUCE),
                                    "early_stopping": dict(config.EARLY_STOPPING)
                                }

                                return tuner, param_log, now
                            """
                    # , language="python"
                )
            with st.popover("build_model_init(hp)"):
                st.code("""
                    def build_model_init(hp):
                        '''Builds a frozen ResNet50 model for initial hyperparameter tuning.'''
                        base = ResNet50(include_top=False, weights="imagenet", input_shape=(224, 224, 3), name="resnet50")
                        base.trainable = False

                        model = models.Sequential([
                                    base,
                                    layers.GlobalAveragePooling2D(),
                                    layers.Dense(hp.Int('dense_units', min_value=config.DENSE_MIN, max_value=config.DENSE_MAX, step=config.DENSE_STEP), activation='relu'),
                                    layers.Dropout(hp.Float('dropout_rate', min_value=config.DROP_RATE_MIN, max_value=config.DROP_RATE_MAX, step=config.DROP_RATE_STEP)),
                                    layers.Dense(4, activation='softmax')
                                ])

                        model.compile(
                            optimizer=Adam(learning_rate=hp.Float('learning_rate', config.INITIAL_LR_MIN, config.INITIAL_LR_MAX,
                                                                    sampling=config.INITIAL_LR_SAMPLING)),
                            loss='sparse_categorical_crossentropy',
                            metrics=['accuracy']
                                )
                        return model
                        """)

            with st.popover("build_model_fine(hp)"):
                st.markdown(
                    """
                            '''
                            def build_model_fine(hp):
                                '''Builds a fine-tunable ResNet50 model with loaded checkpoint support.'''
                                # EarlyStopping
                                es_patience = hp.Int("es_patience", min_value=config.ES_PATIENCE_MIN or 5, max_value=config.ES_PATIENCE_MAX or 15, step=config.ES_PATIENCE_STEP or 2)
                                es_min_delta = hp.Float("es_min_delta", min_value=config.ES_MIN_DELTA_MIN or 0.0001, max_value=config.ES_MIN_DELTA_MAX or 0.01, sampling=config.ES_MIN_DELTA_SAMPLING or "log")

                                # ReduceLROnPlateau
                                lr_patience = hp.Int("lr_patience", min_value=config.LR_PATIENCE_MIN or 3, max_value=config.LR_PATIENCE_MAX or 10, step=config.LR_PATIENCE_STEP or 1)
                                lr_cooldown = hp.Int("lr_cooldown", min_value=config.LR_PATIENCE_MIN or 0, max_value=config.LR_PATIENCE_MAX or 5, step=config.LR_PATIENCE_STEP or 1)
                                lr_min_delta = hp.Float("lr_min_delta", min_value=config.LR_MIN_DELTA_MIN or 0.0001, max_value=config.LR_MIN_DELTA_MAX or 0.01, sampling=config.LR_MIN_DELTA_SAMPLING or "log")
                                lr_factor = hp.Float("lr_factor", min_value=config.LR_FACTOR_MIN or 0.1, max_value=config.LR_FACTOR_MAX or 0.5, step=config.LR_FACTOR_STEP or 0.1)

                                if config.LOAD_MODEL:
                                    gc.collect()
                                    tf.keras.backend.clear_session()
                                    model = tf.keras.models.load_model(config.LOAD_MODEL)
                                    print(f"Loaded model from {config.LOAD_MODEL}")
                                    base = model.get_layer("resnet50")
                                else:
                                    base = ResNet50(include_top=False, weights="imagenet", input_shape=(224, 224, 3), name="resnet50")

                                base.trainable = True
                                if config.UNFROZEN_LAYERS is None:
                                    for layer in base.layers:
                                        layer.trainable = False
                                elif config.UNFROZEN_LAYERS > 0:
                                    for layer in base.layers[:-config.UNFROZEN_LAYERS]:
                                        layer.trainable = False

                                model = models.Sequential([
                                    base,
                                    layers.GlobalAveragePooling2D(),
                                    layers.Dense(config.DENSE_UNITS, activation='relu', name="dense_2nd_last"),
                                    layers.Dropout(config.DROP_RATE, name="dropout_last"),
                                    layers.Dense(4, activation='softmax')
                                ])

                                model.compile(
                                    optimizer=Adam(learning_rate=config.INIT_LR),
                                    loss='sparse_categorical_crossentropy',
                                    metrics=['accuracy']
                                )
                                return model
                            """
                    # , language="python"
                )
    with tab2:
        st.subheader("Training Stages")
        st.markdown("""
            The training was conducted in several steps, which can be divided into three blocks:
            - **Initial training**,
            - **Fine-tuning**,
            - **Data Augmentation**

            Before the first training step was conducted in each block, (additional) samples were drawn. The first training
            step in each block was among other used for determing a baseline from the current sample set. The name of
            these steps contain a '0' or 'None'.

            At each stage, a Bayesian optimization of the hyperparameter was applied. During the initial training, hyperparameters of the classification layer were
            optimized, while, during the other training steps, hyperparameters of the applied callbacks were tested (ReduceOnPlateau and ??). More details are provided
            in the expanders below.
            After each epoch, the model performance was evaluated on the training and validation by using accuracy. Additionally, the metric 'loss' was logged.
            After each step, the best model was evaluated in more depth, i.e. more metrics were calculated for the training and validation dataset.
            """)

        with st.expander("Initial Training"):
            st.markdown("""
                We trained a frozen ResNet50 model with a custom dense classification head on a limited dataset. Hyperparameter tuning was applied to the dense layer
                size, dropout rate, and initial learning rate. Batch sizes of 16, and 32 were tested after the data set has been divided 80:20 and
                60:40, respectively. After a 80:20 split, the dataset was also tested with a larger batch size (64) and feeded with smoothly augmented data ,
                respectively (RandomContrast: 0.05, RandomBrightness: 0.05, RandomZoom: 0.03, RandomRotation: 0.02).


                """)
            st.write("Table to be added")
            # st.table()

            st.markdown("""
            The best results were obtained by using:
            - **Dataset split: _80:20 (train:val)_**
            - **Batch size: _32_**,
            - **Dense layer size: _??_**
            - **Dropout rate: _??_**
            - **Initial learnings rate: _??_**
                """)

        with st.expander("Fine tuning - Part 1"):
            st.markdown("""
                #### __Part 1: Increased Data, Still Frozen__

                The best model from initial training was now trained with a larger subset of the dataset to investigate the isolated effect of more training data. No
                layers were unfrozen, but different hyperparameter settings of the applied callbacks `‘ReduceLearnRateOnPLateau’` and `‘EarlyStopping’` were tested
                using KerasTuner.
                [...]
                """)

        with st.expander("Fine tuning - Part 2"):
            st.markdown(
                """
                #### __Part 2: Last 20 Layers Unfrozen__

                We partially unfroze the ResNet50 model, training the top 20 layers in addition to the classification head. Callbacks for early stopping and reducing
                learning rate were used to stabilize training.
                In this setup, we included the following representative convolutional layers ("block_layer") as trainable:
                - <span style="color:#008000;">`conv4_block6_3_conv` _(new)_</span>
                - <span style="color:#008000;">`conv5_block1_3_conv` _(new)_</span>
                - <span style="color:#008000;">`conv5_block3_3_conv` _(new)_</span>

                These layers are part of the deeper stages of the network and contribute significantly to high-level feature extraction, which is especially relevant
                when adapting to domain-specific patterns in chest X-ray images.
                [...]
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Fine tuning - Part 3"):
            # st.subheader("Fine tuning - Part 3 (Last 50 Layers Unfrozen)")
            st.markdown(
                """
                #### __Part 3: Last 50 Layers Unfrozen__

                This experiment extended fine-tuning further by unfreezing the last 50 layers of the ResNet50 model. In this configuration, most of the deeper
                convolutional blocks were allowed to adapt to the CXR data.
                Relevant trainable layers from the block_layer list are now included:
                - <span style="color:#00AA00;">`conv3_block4_3_conv` _(new)_</span>
                - <span style="color:#008000;">`conv4_block1_3_conv` _(new)_</span>
                - `conv4_block6_3_conv` _(previously unfrozen)_
                - `conv5_block1_3_conv` _(previously unfrozen)_
                - `conv5_block3_3_conv` _(previously unfrozen)_

                This strategy allowed for more complex adaptation, though it increased the risk of overfitting and required careful regularization and learning rate
                scheduling.
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Fine tuning - Part 4"):
            # st.subheader("Fine tuning - Part 4 (Last 100 Layers Unfrozen)")
            st.markdown(
                """
                #### __Part 4: Last 100 Layers Unfrozen__

                To push the adaptation further, the final 100 layers were set to trainable. This allowed more than a half of all convolutional blocks from the
                ResNet50 architecture to learn from the X-Ray data. Included block_layer components:
                - <span style="color:#008000;">`conv2_block3_3_conv` _(new)_</span>
                - <span style="color:#008000;">`conv3_block1_3_conv` _(new)_</span>
                - `conv3_block4_3_conv` _(previously unfrozen)_
                - `conv4_block1_3_conv` _(previously unfrozen)_
                - `conv4_block6_3_conv` _(previously unfrozen)_
                - `conv5_block1_3_conv` _(previously unfrozen)_
                - `conv5_block3_3_conv` _(previously unfrozen)_

                This deeper unfreezing made the model more flexible and expressive but also required longer training time and stronger regularization.
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Fine tuning - Part 5"):
            st.markdown(
                """
                #### __Part 5:  All layers unfrozen__

                In this final fine-tuning variant, the entire ResNet50 model was unfrozen—including the early convolutional layers in the last 75 layers. This allows
                full adaptation of all model parameters to the specific data domain. All block_layer components were trainable:
                - <span style="color:#008000;">`conv1_conv`     &nbsp;&nbsp;&nbsp;&nbsp; _(new)_</span>
                - <span style="color:#008000;">`conv2_block1_3_conv` _(new)_</span>
                - `conv2_block3_3_conv` _(previously unfrozen)_
                - `conv3_block1_3_conv` _(previously unfrozen)_
                - `conv3_block4_3_conv` _(previously unfrozen)_
                - `conv4_block1_3_conv` _(previously unfrozen)_
                - `conv4_block6_3_conv` _(previously unfrozen)_
                - `conv5_block1_3_conv` _(previously unfrozen)_
                - `conv5_block3_3_conv` _(previously unfrozen)_

                While full unfreezing maximizes representational power, it also increases the risk of catastrophic forgetting of pretrained features and requires the
                most careful training configuration among all strategies.
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Data Augmentation"):
            # st.subheader("Data Augmentation Experiments")
            st.markdown("""
                We compared three levels of augmentation:
                - `DataAug_none`: No augmentation but additional samples
                - `DataAug_smooth`: Mild brightness/contrast/rotation
                - `DataAug_enhanced`: Stronger and combined transformations

                The following augmentation types were used in the stated ranges:
                *to be added*
                """)
            # st.table()

        with st.expander("INFO: Configuration and Hyperparameters"):
            st.text("""
                These strategies were applied subsequently to the same model setup to isolate the effect of input variability and .

                loss function: ??
                optimizer ??
                max_epochs ??

                """)
