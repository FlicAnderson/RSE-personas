"""Plot 3-Dimensional PCA plot for labelled analysis dataset."""

from logging import Logger
import pandas as pd
import numpy as np
from typing import Literal
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
from pathlib import Path

from githubanalysis.setup_classes import DatasetSetup
# from utilities.rse_persona_info_utils import (
#     RSE_personas_info,
# )  # generates info used for pca3d not currently enabled in here

#  ruff: noqa: F841


class PlotPCA(DatasetSetup):
    def _log_name(self) -> str:
        return "plot_3D_PCA"

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.exists_ok = exists_ok
        self.data_write_location.mkdir(exist_ok=self.exists_ok)
        self.image_write_location.mkdir(exist_ok=self.exists_ok)
        # rse_persona_info = RSE_personas_info()

        def pca3d(
            self,
            cluster_labels: pd.Series,
            clustering_data: pd.DataFrame,
            cluster_names: list[str],  # = persona_name,
            colours: list[str],  # = persona_palette,
            marks: list[str],  # = persona_mark,
            fill_style: list[
                Literal["full", "left", "right", "bottom", "top", "none"]
            ],  # = persona_fill,
            edge_col: list[str],  # = persona_edge,
            file_name: str = "sample_3D_PCA_",
            save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
        ):
            clustering_data_labelled = pd.concat(
                [pd.DataFrame({"cluster_labels": cluster_labels}), clustering_data],
                axis=1,
            )

            fig = plt.figure(1, figsize=(8, 6))
            ax = fig.add_subplot(111, projection="3d", elev=-150, azim=110)

            X_reduced = PCA(n_components=3).fit_transform(clustering_data_labelled)

            # this pulls data from the PCA.fit_transform() output X_reduced into N arrays, which is the N of personas:
            arrays = tuple(
                np.array(
                    [r for i, r in enumerate(X_reduced) if cluster_labels[i] == label]
                )
                for label in cluster_labels.unique()
            )

            # get the appropriate data array, plotting mark and colour for each 'layer' of data (ie plotting in layers 1 persona at a time)
            mrks_used = []
            edges_used = []

            for arr, mark, col, fill, edge in zip(
                arrays, marks, colours, fill_style, edge_col
            ):
                mrks_used.append(mark)
                edges_used.append(edge)
                ax.scatter(
                    arr[:, 0],
                    arr[:, 1],
                    arr[:, 2],
                    c=[col] * len(arr),
                    s=5,
                    marker=MarkerStyle(mark, fillstyle=fill),  # noqa
                    edgecolor=edge,
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

            # Add a legends
            legend1 = ax.legend(
                cluster_names,
                title="RSE Personas",
                bbox_to_anchor=(1, 0.5),
            )
            plot_file = Path(
                self.image_write_location,
                f"{file_name}_{self.current_date_info}.{save_type}",
            )
            plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
            plt.close()

            self.logger.info(f"PCA 3D Plot saved out to file {plot_file}.")
            return fig

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
        save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
    ):
        print(
            "THIS FUNCTION (plot_threedim_PCA) HAS BEEN SUPERCEDED BY `PlotPCA.pca3d(): please consider using that function instead, as it works for (NAMED) sub-clusters. "
        )
        self.logger.warning(
            "THIS FUNCTION (plot_threedim_PCA) HAS BEEN SUPERCEDED BY `PlotPCA.pca3d(): please consider using that function instead, as it works for (NAMED) sub-clusters. "
        )

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
                s=5,
            )
        else:
            assert clustering_data_labelled["cluster_labels"].nunique() == 3, (
                "there should be two or three unique labels, this doesn't seem to be the case. Check this."
            )
            ax.scatter(
                X_reduced[:, 0],
                X_reduced[:, 1],
                X_reduced[:, 2],
                c=cvec,
                s=5,
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
        save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
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
                    s=5,
                )
            plt.legend(targets, prop={"size": 15})
        else:
            assert clustering_data_labelled["cluster_labels"].nunique() == 3, (
                "there aren't 2 or 3 clusters to plot - is this right?"
            )
            targets = [0, 1, 2]
            if isinstance(colours, dict):
                colours = list(colours.values())
            for target, color in zip(targets, colours):
                indicesToKeep = clustering_data_labelled["cluster_labels"] == target
                plt.scatter(
                    PCA_2_df.loc[indicesToKeep, "principal component 1"],
                    PCA_2_df.loc[indicesToKeep, "principal component 2"],
                    c=color,
                    s=5,
                )
            plt.legend(targets, prop={"size": 15})

        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"PCA 2D Plot saved out to file {plot_file}.")
