## run_PCA.py
# imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA, KernelPCA
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.preprocessing import KernelCenterer, StandardScaler
from sklearn.utils import extmath

from src.core.config import parsing_env_vars
from src.core.memory import app_session

# from src.utils.general_helper import load_env_vars

# PART 1
## load data


def pca_impl(X, n_components=2):
    # Preprocessing - Standard Scaler
    X_std = StandardScaler().fit_transform(X)

    # Calculate covariance matrix
    cov_mat = np.cov(X_std.T)

    # Get eigenvalues and eigenvectors
    eig_vals, eig_vecs = np.linalg.eigh(cov_mat)

    # flip eigenvectors' sign to enforce deterministic output
    eig_vecs, _ = extmath.svd_flip(eig_vecs, np.empty_like(eig_vecs).T)

    # Concatenate the eigenvectors corresponding to the highest n_components eigenvalues
    matrix_w = np.column_stack([eig_vecs[:, -i] for i in range(1, n_components + 1)])

    # Get the PCA reduced data
    Xpca = X_std.dot(matrix_w)

    return Xpca


def ker_pca(X, n_components=3, gamma=0.01):
    # Calculate euclidean distances of each pair of points in the data set
    dist = euclidean_distances(X, X, squared=True)

    # Calculate Gaussian kernel matrix
    K = np.exp(-gamma * dist)
    Kc = KernelCenterer().fit_transform(K)

    # Get eigenvalues and eigenvectors of the kernel matrix
    eig_vals, eig_vecs = np.linalg.eigh(Kc)

    # flip eigenvectors' sign to enforce deterministic output
    eig_vecs, _ = extmath.svd_flip(eig_vecs, np.empty_like(eig_vecs).T)

    # Concatenate the eigenvectors corresponding to the highest n_components eigenvalues
    Xkpca = np.column_stack([eig_vecs[:, -i] for i in range(1, n_components + 1)])

    return Xkpca


def pca_vs_kernel_pca(f_path: str):
    # load env variables and config
    # load_env_vars()

    data_input = parsing_env_vars.data_dir

    data = pd.read_csv(f_path)
    # '../data/plums.csv')
    X = data.values[:, 1:]
    Xstd = StandardScaler().fit_transform(X)

    # Scikit-learn PCA
    pca1 = PCA(n_components=2)
    Xpca1 = pca1.fit_transform(X)

    # Our implementation
    Xpca2 = pca_impl(X, n_components=2)

    with plt.style.context("ggplot"):
        fig, ax = plt.subplots(1, 2, figsize=(14, 6))

        # plt.figure(figsize=(8,6))
        ax[0].scatter(Xpca1[:, 0], Xpca1[:, 1], s=100, edgecolors="k")
        ax[0].set_xlabel("PC 1")
        ax[0].set_ylabel("PC 2")
        ax[0].set_title("Scikit learn")

        ax[1].scatter(Xpca2[:, 0], Xpca2[:, 1], s=100, facecolor="b", edgecolors="k")
        ax[1].set_xlabel("PC 1")
        ax[1].set_ylabel("PC 2")
        ax[1].set_title("Our implementation")
        plt.show()

    kpca1 = KernelPCA(n_components=3, kernel="rbf", gamma=0.01)
    Xkpca1 = kpca1.fit_transform(Xstd)

    Xkpca2 = ker_pca(Xstd)

    with plt.style.context("ggplot"):
        fig, ax = plt.subplots(1, 2, figsize=(14, 6))

        # plt.figure(figsize=(8,6))
        ax[0].scatter(Xkpca1[:, 0], Xkpca1[:, 1], s=100, edgecolors="k")
        ax[0].set_xlabel("PC 1")
        ax[0].set_ylabel("PC 2")
        ax[0].set_title("Scikit learn")

        ax[1].scatter(Xkpca2[:, 0], Xkpca2[:, 1], s=100, facecolor="b", edgecolors="k")
        ax[1].set_xlabel("PC 1")
        ax[1].set_ylabel("PC 2")
        ax[1].set_title("Our implementation")
        plt.show()

    return


# def load_nir_data(f_path: str):
#     data = pd.read_csv(f_path)

#     y = data.values[:, 1].astype("uint8")
#     X_raw = data.values[:, 2:].astype("float32")

#     # reflectance → absorbance
#     X_abs = np.log(1.0 / X_raw)

#     return X_abs, y


def load_nir_data(f_path: str):
    logger = app_session.logger

    data = pd.read_csv(f_path)

    y = data.values[:, 1].astype("uint8")
    X_raw = data.values[:, 2:].astype("float32")

    # reflectance → absorbance
    X_abs = np.log(1.0 / X_raw)

    logger.info(
        "Loaded data from %s\nshape 'y': %s\shape 'X: %s'",
        shorten_path(f_path),
        y.shape,
        X_abs.shape,
    )

    return X_abs, y


def explained_variance_by_pca(
    f_path: str,
    config: dict,
    # url=None
):
    X_abs, y = load_nir_data(f_path)

    X_sg = preprocess_spectra(X_abs, config)

    # feat_deriv = savgol_filter(
    #                     x=feat,
    #                     window_length=window_length,
    #                     polyorder = polyorder,
    #                     deriv=deriv
    #                     )
    logger.info("d_feat shape:\n", feat_deriv.shape)

    # PART 2

    # Initialise
    nc = config.get("n_pca")  # 10
    assert nc is not None

    pca_1 = PCA(n_components=nc)
    pca_2 = PCA(n_components=nc)

    # Scale the features to have zero mean and standard devisation of 1
    # This is important when correlating data with very different variances
    n_feat_1 = StandardScaler().fit_transform(feat)
    n_feat_2 = StandardScaler().fit_transform(feat_deriv)

    # Fit the spectral data and extract the explained variance ratio
    X_1 = pca_1.fit(n_feat_1)
    expl_var_1 = X_1.explained_variance_ratio_

    # Fit the first data and extract the explained variance ratio
    X_2 = pca_2.fit(n_feat_2)
    expl_var_2 = X_2.explained_variance_ratio_

    expl_data = {
        "expl_var (feat)": expl_var_1,
        "expl_var_cum (feat)": np.cumsum(expl_var_1),
        "expl_var (feat_deriv)": expl_var_2,
        "expl_var_cum (feat_deriv)": np.cumsum(expl_var_2),
    }
    expl_df = pd.DataFrame(
        data=expl_data, index=[f"pca # {idx}" for idx in range(1, len(expl_var_1) + 1)]
    )
    st.markdown("""
### Explained variance 'Features' + 'Features derivative'

                """)
    # **single**
    st.dataframe(np.round(expl_df, 4))

    #     for idx, var in enumerate(list(expl_var_1)):
    #         st.markdown(f"[pca # {idx}] {np.round(var, 4)}")

    #     st.markdown(f"**cumulative sum**(dtype: {type(expl_var_1)})")
    #     for idx, sum_var in enumerate(list(np.cumsum(expl_var_1))):
    #         st.markdown(f"[pca # {idx}] {np.round(sum_var, 4)}")

    #     st.markdown("""\n
    # ### Explained variance 'Features_derivative'
    # **single**
    #                 """)
    #     for idx, var in enumerate(list(expl_var_2)):
    #         st.markdown(f"[pca # {idx+1}] {np.round(var, 4)}")

    #     st.markdown(f"**cumulative sum** (dtype: {type(expl_var_2)})")
    #     for idx, sum_var in enumerate(list(np.cumsum(expl_var_2))):
    #         st.markdown(f"[pca # {idx+1}] {np.round(sum_var, 4)}")

    # Plot data
    pc_array = np.linspace(1, nc, nc)
    with plt.style.context("ggplot"):
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(9, 6))
        fig.set_tight_layout(True)

        ax1.plot(pc_array, expl_var_1, "-o", label="Explained Variance %")
        ax1.plot(pc_array, np.cumsum(expl_var_1), "-o", label="Cumulative variance %")
        ax1.set_xlabel("PC number")
        ax1.set_title("Absorbance data")

        ax2.plot(pc_array, expl_var_2, "-o", label="Explained Variance %")
        ax2.plot(pc_array, np.cumsum(expl_var_2), "-o", label="Cumulative variance %")
        ax2.set_xlabel("PC number")
        ax2.set_title("First derivative data")

        plt.legend()

        if config.get("st_viz", False):
            st.pyplot(fig)

        else:
            plt.show()

    # PART 3
    # n_opt = input("Enter n_optimal (pca)")
    # n_opt = st.number_input(
    #                 "Enter n_optimal (pca)",
    #                 value=None,
    #                 placeholder="Type a number...",
    #                 # key="n_opt"
    #                 )

    # st.write("The current 'n_optimal (pca)' is ", n_opt)
    # # config.get("n_opt")

    # if n_opt is not None:
    #     pca_2 = PCA(n_opt)

    #     # Transform on the scaled features
    #     Xt_2 = pca_2.fit_transform(n_feat_2)

    #     # Define the labels for the plot legend
    #     plot_label= ["0/8 Milk",
    #             "1/8 Milk",
    #             "2/8 Milk",
    #             "3/8 Milk",
    #             "4/8 Milk",
    #             "5/8 Milk",
    #             "6/8 Milk",
    #             "7/8 Milk",
    #             "8/8 Milk"]

    #     # Scatter plot
    #     unique = list(set(lab))
    #     colors = [plt.cm.jet(float(i)/max(unique)) for i in unique]
    #     with plt.style.context(('ggplot')):
    #         plt.figure(figsize=(8,6))
    #         for i, u in enumerate(unique):
    #             col = np.expand_dims(np.array(colors[i]), axis=0)
    #             xi = [Xt_2[j,0] for j in range(len(Xt_2[:,0]))
    #                 if lab[j] == u]
    #             yi = [Xt_2[j,1] for j in range(len(Xt_2[:,1]))
    #                 if lab[j] == u]
    #             plt.scatter(xi,
    #                         yi,
    #                         c=col,
    #                         s=60,
    #                         edgecolors='k',
    #                         label=str(u))

    #         plt.xlabel('PC1')
    #         plt.ylabel('PC2')
    #         plt.legend(plot_label,
    #                 loc='upper right')
    #         plt.title('Principal Component Analysis')

    #         if config.get("st_viz", False):
    #             st.pyplot(plt.gcf())

    #         else:
    #             plt.show()
    #         # plt.show()

    return


if __name__ == "__main__":
    explained_variance_by_pca()
