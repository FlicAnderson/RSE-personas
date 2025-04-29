"""Generate Dendrogram Plot from Data."""

from pathlib import Path
import datetime

import logging
import utilities.get_default_logger as loggit

import pandas as pd

from matplotlib import pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram


class Dendrogrammer:
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
                log_name="logs/pre-analysis_data_times_prep.txt",
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

    def plot_dendrogram(
        self,
        clustering_data: pd.DataFrame,
        colours: list | dict | sns.palettes._ColorPalette = sns.color_palette(
            "colorblind"
        ),
        file_name: str = "sample_dendrogram_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        # THIS IS THE SCIPY HIERARCHICAL CLUSTERING METHODS
        self.logger.info(
            f"Attempting to use {len(clustering_data)} repo-individuals dataset for clustering"
        )
        ward_clustering = linkage(clustering_data, method="ward", metric="euclidean")
        self.logger.info(
            "Created ward clustering linkage object, now attempting to generate dendrogram"
        )

        dendrogram(
            ward_clustering,
            show_contracted=True,
            no_labels=True,
            color_threshold=400,
            above_threshold_color="black",
        )
        # plt.savefig(f"../../images/dendrogram_ward_euclidian_x{n_repos}repos_x{len(clustering_data)}project_individuals_{current_date_info}.png")
        plt.title(
            f"Hierarchical Clustering (Ward Method, Euclidian Distance), N repo-individuals={len(clustering_data)}."
        )
        plot_file = Path(
            self.write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")
