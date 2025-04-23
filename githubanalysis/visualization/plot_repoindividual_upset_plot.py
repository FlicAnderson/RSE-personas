"""Generate UpSet Plot from Clustered Post-Analysis Data."""

from pathlib import Path
import datetime

import logging
import utilities.get_default_logger as loggit

import pandas as pd

from matplotlib import pyplot as plt
import seaborn as sns

from upsetplot import UpSet, from_memberships


class UpsetPlotter:
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

    def plot_upset_plot_interaction_combinations(
        self,
        data: pd.DataFrame | Path,
        colours: list | dict = sns.color_palette("colorblind"),
        separate_by_clusters: bool = False,
        sort_combos_by: str = "cardinality",
        file_name: str = "upset_plot_",
        save_type: str = "svg",  # one of: ['png', 'pdf', 'svg']
        # min_repo_individs_per_combo: int = 2,
        # show_counts_per_combo: boolean = True,
        # show_pc: boolean = False,
    ):
        """
        This generates UpSet plots from GH interaction data from a dataframe or csv file.
        Data must be in a per-repo-individual format, and cluster labels must be in column titled "cluster_labels".

        TODO: pull the plot upsetplot into a function, so I can loop it for n_clusters from data and avoid repetition

        """

        assert isinstance(
            data, (pd.DataFrame, Path)
        ), "Data is not of type pandas dataframe or Path; check your inputs."
        assert save_type in [
            "svg",
            "pdf",
            "png",
        ], "save_type is not valid; check you have entered one of: 'svg', 'pdf', 'png'."
        assert (
            sort_combos_by
            in ["cardinality", "-cardinality", "degree", "-degree", "input", "-input"]
        ), "sort_combos_by is not valid, check you've entered one of: 'cardinality', 'degree', 'input' or '-cardinality', '-degree', '-input'."

        # what type is data?
        if isinstance(data, pd.DataFrame):
            assert data.empty is False, "Dataframe data is empty; check inputs."
            self.logger.info(f"data is df, with shape: {data.shape}.")

        if isinstance(data, Path):
            self.logger.info(f"data is a path: {data}")
            data = pd.read_csv(filepath_or_buffer=data, header=0)
            assert isinstance(data, pd.DataFrame), "data could not be read in properly."
            self.logger.info(f"data is df, with shape: {data.shape}.")

        # if colours is a list and separate_by_clusters is true, does len(colours) match nunique('cluster_labels')?
        if separate_by_clusters:
            assert (
                "cluster_labels" in data.columns
            ), "df has no column 'cluster_labels - please check this is present in the data."
            n_clusters = data.cluster_labels.nunique()
            assert (
                len(colours) >= n_clusters
            ), f"length/number of colours supplied not enough for number of clusters: N colours={len(colours)} but N of clusters is {n_clusters}."

            assert (
                n_clusters > 2
            ), "Support for 3+ clusters not written into this function yet."

            data_by_interaction = from_memberships(
                data.which_interactions.apply(
                    lambda x: [x.strip() for x in x.split(",")]
                ),
                data=data,
            )

            upset = UpSet(
                data_by_interaction.query("cluster_labels == 0"),
                show_counts="{:,}",
                sort_by=sort_combos_by,
                facecolor=colours[0],
                orientation="horizontal",
                min_subset_size=2,
            )
            upset.plot()
            plt.suptitle(
                f"Interaction-Combinations made by >1 Repo-Individuals in CLUSTER 0,  N={len(data_by_interaction.query('cluster_labels == 0'))}"
            )
            plt.show()
            plot_file = Path(
                self.write_location,
                f"{file_name}_cluster0_{self.current_date_info}",  # << NOTE: hardcoded cluster name
            )
            plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
            self.logger.info(f"Plot saved out to file {plot_file}.")
            plt.close()

            upset = UpSet(
                data_by_interaction.query("cluster_labels == 1"),
                show_counts="{:,}",
                sort_by=sort_combos_by,
                facecolor=colours[1],
                orientation="horizontal",
                min_subset_size=2,
            )
            upset.plot()
            plt.suptitle(
                f"Interaction-Combinations made by >1 Repo-Individuals in CLUSTER 1, N={len(data_by_interaction.query('cluster_labels == 1'))}"
            )
            plt.show()
            plot_file = Path(
                self.write_location,
                f"{file_name}_cluster1_{self.current_date_info}",  # << NOTE: hardcoded cluster name
            )
            plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
            self.logger.info(f"Plot saved out to file {plot_file}.")
            plt.close()

            # if n_clusters was 3, would add separate support for that here...

        else:  # if not plotting separately by clusters:
            data_by_interaction = (
                from_memberships(  # format data to upsetplot requirements
                    data.which_interactions.apply(
                        lambda x: [x.strip() for x in x.split(",")]
                    ),
                    data=data,
                )
            )

            upset = UpSet(
                data_by_interaction,
                show_counts="{:,}",
                sort_by="degree",
                facecolor=colours[
                    0
                ],  # use first colour in colours as single colour option
                orientation="horizontal",
                min_subset_size=2,
            )
            upset.plot()
            plt.suptitle(
                f"Interaction-Combinations made by >1 Repo-Individuals,  N={len(data_by_interaction)}"
            )
            plt.show()

            # build path + filename
            plot_file = Path(
                self.write_location, f"{file_name}_{self.current_date_info}"
            )

            plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
            self.logger.info(f"Plot saved out to file {plot_file}.")

            plt.close()
