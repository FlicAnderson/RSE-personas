"""Generate Dendrogram Plot from Data."""

from pathlib import Path
import datetime
import gc

import logging
import utilities.get_default_logger as loggit

import pandas as pd

from matplotlib import pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram
import sys

sys.setrecursionlimit(10000)


class Dendrogrammer:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    image_write_location: Path

    def __init__(
        self,
        image_write_location: Path,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/plot_dendrograms.txt",
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

    def plot_dendrogram(
        self,
        clustering_data: pd.DataFrame,
        colours: list | dict,
        file_name: str = "sample_dendrogram_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        # THIS IS THE SCIPY HIERARCHICAL CLUSTERING METHODS
        self.logger.info(
            f"Attempting to use {len(clustering_data)} repo-individuals dataset for clustering"
        )

        label_color_dict = [
            "#D50032",
            "#1D2A3D",
            "#FDBC42",
        ]  # REVERESED COLOUR ORDER AS I'VE SET DISTANCE_SORT to TRUE!!!
        sns.set_palette(label_color_dict)

        sys.setrecursionlimit(100000)  # attempt to address recursion limit error
        gc.collect()  # garbage collection to free up space/mem: spring cleaning!

        ward_clustering = linkage(clustering_data, method="ward", metric="euclidean")
        self.logger.info(
            "Created ward clustering linkage object, now attempting to generate dendrogram"
        )

        plt.figure(figsize=(25, 10))
        plt.xlabel("Clustered Repo-individuals")
        plt.ylabel("Distance")
        dendrogram(
            ward_clustering,
            show_contracted=True,
            truncate_mode="level",  # show only the last p merged clusters
            p=5,  # show only the last p merged clusters
            no_labels=True,
            color_threshold=4000,
            above_threshold_color="black",
        )
        # plt.savefig(f"../../images/dendrogram_ward_euclidian_x{n_repos}repos_x{len(clustering_data)}project_individuals_{current_date_info}.png")
        plt.title(
            f"Hierarchical Clustering (Ward Method, Euclidian Distance), N repo-individuals={len(clustering_data)}."
        )
        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")

    def plot_dendrogram_with_leaf_counts(
        self,
        clustering_data: pd.DataFrame,
        show_leaves: bool = False,
        file_name: str = "sample_dendrogram_leafcounts",
        save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
    ):
        assert isinstance(show_leaves, bool), "show_leaves must be boolean"
        # THIS IS THE SCIPY HIERARCHICAL CLUSTERING METHODS
        self.logger.info(
            f"Attempting to use {len(clustering_data)} repo-individuals dataset for clustering"
        )

        label_color_dict = [
            "#D50032",
            "#1D2A3D",
            "#FDBC42",
        ]  # REVERESED COLOUR ORDER AS I'VE SET DISTANCE_SORT to TRUE!!!
        sns.set_palette(label_color_dict)

        sys.setrecursionlimit(100000)  # attempt to address recursion limit error
        gc.collect()  # garbage collection to free up space/mem: spring cleaning!

        ward_clustering = linkage(clustering_data, method="ward", metric="euclidean")
        self.logger.info(
            "Created ward clustering linkage object, now attempting to generate dendrogram"
        )

        plt.figure(figsize=(25, 10))
        plt.xlabel("Clustered Repo-individuals")
        plt.ylabel("Distance")
        dendrogram(
            ward_clustering,
            show_contracted=True,
            no_labels=show_leaves,  # set this to false to re-allow values under leafs.
            color_threshold=4000,
            above_threshold_color="black",
            count_sort=False,
            distance_sort=False,
            show_leaf_counts=True,  # use =True to add numbers below leaves
            truncate_mode="level",  # show only the last p merged clusters
            p=5,  # show only the last p merged clusters
            leaf_rotation=360,  # this does nothing if show_leaf_counts is false
        )
        # plt.savefig(f"../../images/dendrogram_ward_euclidian_x{n_repos}repos_x{len(clustering_data)}project_individuals_{current_date_info}.png")
        plt.title(
            f"Hierarchical Clustering (Ward Method, Euclidian Distance), N repo-individuals={len(clustering_data)}."
        )
        plot_file = Path(
            self.image_write_location,
            f"{file_name}_leaves_{show_leaves}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")
