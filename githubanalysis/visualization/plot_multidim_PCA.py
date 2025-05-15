"""Plot 3-Dimensional PCA plot for labelled analysis dataset."""

from pathlib import Path
import datetime

import logging
import utilities.get_default_logger as loggit

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA

from matplotlib import pyplot as plt


class PlotPCA:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    image_write_location: Path

    def __init__(
        self,
        in_notebook: bool,
        image_write_location: Path,
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
        self.image_write_location = image_write_location

    def plot_threedim_PCA(
        self,
        cluster_labels: np.ndarray,
        clustering_data: pd.DataFrame,
        colours: list | dict = {
            0: "#D50032",
            1: "#1D2A3D",
            2: "#FDBC42",
        },  # universityred, epccnavy, dandelion,
        file_name: str = "sample_3D_PCA_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        clustering_data_labelled = pd.concat(
            [pd.DataFrame({"cluster_labels": cluster_labels}), clustering_data], axis=1
        )
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

        X_reduced = PCA(n_components=3).fit_transform(clustering_data_labelled)
        if clustering_data_labelled["cluster_labels"].nunique() == 2:
            ax.scatter(
                X_reduced[:, 0],
                X_reduced[:, 1],
                c=cvec,
                s=40,
            )
        else:
            assert (
                clustering_data_labelled["cluster_labels"].nunique() == 3
            ), "there should be two or three unique labels, this doesn't seem to be the case. Check this."
            ax.scatter(
                X_reduced[:, 0],
                X_reduced[:, 1],
                X_reduced[:, 2],
                c=cvec,
                s=40,
            )

        PCA_3 = PCA(n_components=3)
        PCA_3_df = pd.DataFrame(
            data=PCA_3.fit_transform(clustering_data),
            columns=[
                "principal component 1",
                "principal component 2",
                "principal component 3",
            ],
        )

        self.logger.info(
            f"{'Explained variability per principal component: {}'.format(PCA_3.explained_variance_ratio_)}"
        )

        eigenvec1 = (PCA_3.explained_variance_ratio_)[0] * 100
        eigenvec2 = (PCA_3.explained_variance_ratio_)[1] * 100
        eigenvec3 = (PCA_3.explained_variance_ratio_)[2] * 100
        ax.set(
            title="Principal Component Analysis of Repo-Individuals Interactions Data",
            xlabel=f"Eigenvector 1: ({round(eigenvec1, 2)}%)",
            ylabel=f"Eigenvector 2: ({round(eigenvec2, 2)}%)",
            zlabel=f"Eigenvector 3: ({round(eigenvec3, 2)}%)",
        )
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.zaxis.set_ticklabels([])

        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"PCA 3D Plot saved out to file {plot_file}.")

    def plot_twodim_PCA(
        self,
        cluster_labels: np.ndarray,
        clustering_data: pd.DataFrame,
        colours: list | dict = {
            0: "#D50032",
            1: "#1D2A3D",
            2: "#FDBC42",
        },  # universityred, epccnavy, dandelion,
        file_name: str = "sample_2D_PCA_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        clustering_data_labelled = pd.concat(
            [pd.DataFrame({"cluster_labels": cluster_labels}), clustering_data], axis=1
        )

        PCA_2 = PCA(n_components=2)
        PCA_2_df = pd.DataFrame(
            data=PCA_2.fit_transform(clustering_data),
            columns=["principal component 1", "principal component 2"],
        )

        self.logger.info(
            f"{'Explained variability per principal component: {}'.format(PCA_2.explained_variance_ratio_)}"
        )

        eigenvec1 = (PCA_2.explained_variance_ratio_)[0] * 100
        eigenvec2 = (PCA_2.explained_variance_ratio_)[1] * 100

        plt.figure()
        plt.figure(figsize=(10, 10))
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=14)
        plt.xlabel(f"Principal Component 1: ({round(eigenvec1, 2)}%)", fontsize=20)
        plt.ylabel(f"Principal Component 2: ({round(eigenvec2, 2)}%)", fontsize=20)
        plt.title(
            "Principal Component Analysis of Repo-Individuals Interactions", fontsize=20
        )
        if clustering_data_labelled["cluster_labels"].nunique() == 2:
            targets = [0, 1]
            if isinstance(colours, dict):
                colours = list(colours.values())
            for target, color in zip(targets, colours):
                indicesToKeep = clustering_data_labelled["cluster_labels"] == target
                plt.scatter(
                    PCA_2_df.loc[indicesToKeep, "principal component 1"],
                    PCA_2_df.loc[indicesToKeep, "principal component 2"],
                    c=color,
                    s=50,
                )
            plt.legend(targets, prop={"size": 15})
        else:
            assert (
                clustering_data_labelled["cluster_labels"].nunique() == 3
            ), "there aren't 2 or 3 clusters to plot - is this right?"
            targets = [0, 1, 2]
            if isinstance(colours, dict):
                colours = list(colours.values())
            for target, color in zip(targets, colours):
                indicesToKeep = clustering_data_labelled["cluster_labels"] == target
                plt.scatter(
                    PCA_2_df.loc[indicesToKeep, "principal component 1"],
                    PCA_2_df.loc[indicesToKeep, "principal component 2"],
                    c=color,
                    s=50,
                )
            plt.legend(targets, prop={"size": 15})

        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"PCA 2D Plot saved out to file {plot_file}.")
