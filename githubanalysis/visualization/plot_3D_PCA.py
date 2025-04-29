"""Plot 3-Dimensional PCA plot for labelled analysis dataset."""

from pathlib import Path
import datetime

import logging
import utilities.get_default_logger as loggit

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA

from matplotlib import pyplot as plt


class ThreeDimPCA:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path
    read_location: Path

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/plot_3D_PCA.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.read_location = Path("data/" if not in_notebook else "../../data/")
        self.write_location = Path("images/" if not in_notebook else "../../images/")

    def plot_threedim_PCA(
        self,
        cluster_labels: np.ndarray,
        labelled_data: pd.DataFrame,
        colours: list | dict = {
            0: "#D50032",
            1: "#1D2A3D",
            2: "#FDBC42",
        },  # universityred, epccnavy, dandelion,
        file_name: str = "sample_3D_PCA_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        label_color_dict = colours
        # label_color_dict = {0:'#D50032', 1:'#1D2A3D', 2:'#FDBC42'} # universityred, epccnavy, dandelion,

        fig = plt.figure(1, figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d", elev=-150, azim=110)

        # Label to color dict (manual)
        # ["#1D2A3D", "#FDBC42", "#D50032"] # epccnavy, dandelion, universityred
        # label_color_dict = {0:'#D50032', 1:'#1D2A3D', 2:'#FDBC42'} # universityred, epccnavy, dandelion,
        # Color vector creation
        labels = cluster_labels

        cvec = [label_color_dict[label] for label in labels]

        X_reduced = PCA(n_components=3).fit_transform(labelled_data)
        ax.scatter(
            X_reduced[:, 0],
            X_reduced[:, 1],
            # X_reduced[:, 2],
            c=cvec,
            s=40,
        )

        ax.set(
            title="First three PCA dimensions",
            xlabel="Eigenvector 1",
            ylabel="Eigenvector 2",
            zlabel="Eigenvector 3",
        )
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.zaxis.set_ticklabels([])

        plot_file = Path(
            self.write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")
