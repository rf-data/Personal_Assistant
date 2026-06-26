## nir_ident.py
# imports
from dataclasses import dataclass   # , field
from typing import ClassVar

import numpy as np
import pandas as pd

from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from returns.result import Success, Result, Failure

from src.core.memory import NIRContext


def load_nir_data(f_path: str):
    data = pd.read_csv(f_path)

    y = data.values[:, 1].astype("uint8")
    X_raw = data.values[:, 2:].astype("float32")

    # reflectance → absorbance
    X_abs = np.log(1.0 / X_raw)

    return X_abs, y


@dataclass
class PCA_Model: # (BaseModel):
    scaler: ClassVar # scaler,
    pca: ClassVar # pca,
    q_thresh: float
    #  = np.quantile(q_resid, q_quant),
    t2_thresh: float
    # = np.quantile(t2, t2_quant),
    q_train: ClassVar
    # = q_resid,
    t2_train: ClassVar
    # = t2


@dataclass
class NIR_Identification:

    def __init__(self, nir_context: NIRContext):

        self.logger = nir_context.logger
        self.nir_config = nir_context.nir_settings
        self.save_folder = nir_context.save_folder
        self.save_name = nir_context.save_name

        return 


    def run_pca_ident(self, f_path):
        X_abs, y = load_nir_data(f_path)

        X_proc = self._preprocess_spectra(
            X_abs
            # sg_window_len=25,
            # sg_poly=5,
            # sg_deriv=1
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X_proc,
            y,
            test_size=self.nir_config.get("test_size"),        # 0.25,
            stratify=self.nir_config.get("stratify"),         # y,
            random_state=self.nir_config.get("random_state"),     # 42
        )


        models = self._fit_ident_models(
            X_train,
            y_train,
            # n_components=5
        )

        sample = X_test[0:1]

        result = self._predict_identity(sample, models)

        for label, res in result.items():
            print(label, res.accepted, res.q_residual, res.t2)


    def _preprocess_spectra(self, X_abs):
    
        # X_abs, y = load_nir_data(f_path) 
        # # =25, =5, sg_deriv=1):
        
        # # Calculate first derivative applying a Savitzky-Golay filter
        # sg_window_len = config["sg_window_len"]   # 25
        # # assert sg_window_len is not None

        # sg_poly = config["sg_poly"]   # 5
        # # assert polyorder is not None

        # sg_deriv = config["sg_deriv"]   # 1
        # # assert deriv is not None

        if self.nir_config.get("savgol", False):
            X_sg = savgol_filter(
                X_abs,
                window_length=self.nir_config.sg_window_len,
                polyorder=self.nir_config.sg_poly,
                deriv=self.nir_config.sg_deriv,
                axis=1
                )
            return Success(X_sg)
        
        if self.nir_config("msc", False):
            self.logger.info("Multiplicative Scatter Correction (MSC) is not yet implemented.")

        if self.nir_config("snv", False):
            self.logger.info("Standard Normal Variate (SNV) is not yet implemented.")

        return Failure("PCA preprocessing failed")


    def _fit_pca_model(self, X_class): 
        n_pca_comps = self.nir_config.n_pca_comps
        q_quant = self.nir_config.q_quantile
        t2_quant = self.nir_config.t2_quantile

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_class)

        pca = PCA(n_components=n_pca_comps)
        scores = pca.fit_transform(X_scaled)

        X_reconstructed = pca.inverse_transform(scores)
        residuals = X_scaled - X_reconstructed

        q_resid = np.sum(residuals ** 2, axis=1)

        # einfache T²-Näherung
        eigenvalues = pca.explained_variance_
        t2 = np.sum((scores ** 2) / eigenvalues, axis=1)

        return PCA_Model(
            scaler = scaler,
            pca = pca,
            q_thresh = np.quantile(q_resid, q_quant),
            t2_thresh = np.quantile(t2, t2_quant),
            q_train = q_resid,
            t2_train = t2
            )
    

    def _fit_ident_models(self, X_sg, y):

        models = {}

        for label in np.unique(y):
            X_class = X_sg[y == label]

            models[label] = self._fit_pca_model(
                X_class
                )

        return models


    def _verify_identity(self, X_sample, ref_model: PCA_Model):
        scaler = ref_model.scaler
        pca = ref_model.pca

        X_scaled = scaler.transform(X_sample)

        scores = pca.transform(X_scaled)
        X_reconstructed = pca.inverse_transform(scores)

        residuals = X_scaled - X_reconstructed
        q = np.sum(residuals ** 2, axis=1)

        eigenvalues = pca.explained_variance_
        t2 = np.sum((scores ** 2) / eigenvalues, axis=1)

        accepted = (q <= ref_model.q_thresh) & (t2 <= ref_model.t2_thresh)

        return NIRIdentResult(
            accepted = accepted,
            q_resid = q,
            t2 = t2,
            q_thresh = ref_model.q_thresh,
            t2_thresh = ref_model.t2_thresh
        )


    def _predict_identity(self, X_sample, models):
        results = {}

        for label, model in models.items():
            results[label] = self._verify_identity(X_sample, model)

        return results


    # def calculate_thresholds(self):

    #     return 
"""

fit_pca_model()
calculate_thresholds()
predict_identity()
evaluate_model()
"""