## ident_by_pca.py
# imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
# from mpl_toolkits.mplot3d import Axes3D


############
# Part I
############
url = 'https://raw.githubusercontent.com/nevernervous78/nirpyresearch/master/data/coffee_classification.csv'
data = pd.read_csv(url)
 
labels = data['Coffee Type']
y = LabelEncoder().fit_transform(labels)
 
X = -np.log(data.values[:,1:].astype('float32'))
Xc = X - X.mean(axis=0)
X1 = savgol_filter(X, 11, polyorder = 2, deriv=1)
wl = np.linspace(1100,2300, X.shape[1])
 
colors = [plt.cm.jet(float(i)/max(y)) for i in y]
with plt.style.context(('seaborn-whitegrid')):
    for i,j in enumerate(colors):
        plt.plot(wl, X1[i,:], c=j, alpha=0.5)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('First derivative - NIR absorbance')
plt.show()


############
# Part II
############
# PCA decomposition
pca = PCA(n_components=3)
Xpca = pca.fit_transform(StandardScaler().fit_transform(X1))
 
## 3D Scatter plot
unique = list(set(y))
colors = [plt.cm.jet(float(i+1)/(max(unique)+1)) for i in unique]
with plt.style.context(('seaborn-whitegrid')):
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(111, projection="3d")
 
    for i, u in enumerate(unique):
        xi = [Xpca[j,0] for j  in range(len(Xpca[:,0])) if y[j] == u]
        yi = [Xpca[j,1] for j  in range(len(Xpca[:,1])) if y[j] == u]
        zi = [Xpca[j,2] for j  in range(len(Xpca[:,2])) if y[j] == u]
        ax.scatter(xi, yi, zi, color=colors[i], s=80, label=str(u))
 
    ax.view_init(10, 40)
 
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_zlabel('PC3')
 
    plt.legend(labels.unique(),loc='upper left')
 
plt.show()