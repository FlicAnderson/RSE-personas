"""Generate UpSet Plot from Clustered Post-Analysis Data."""

from pathlib import Path
import datetime
import logging
import pandas as pd
from matplotlib import pyplot as plt
import utilities.get_default_logger as loggit
from upsetplot import UpSet, from_memberships

#  ruff: noqa: F841


class UpsetPlotter:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path
    read_location: Path
    image_write_location: Path

    def __init__(
        self,
        image_write_location: Path,
        dataset_name: str,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/plot_upsetplot_logs.txt",
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
        self.image_write_location = (
            Path("images/" if not in_notebook else "../../images/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.image_write_location.mkdir()

    def upset_plot(
        self,
        cluster: int | None,
        data: pd.DataFrame,
        show_min: float = 0.005,
        show_counts: bool = False,
        sort_combos_by: str = "cardinality",
        data_set_name: str = "dataset",  # manual naming, goes into title of plots
        file_name: str = "upset_plot_",
        save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
    ):
        assert (
            isinstance(cluster, int) or cluster is None
        ), f"give valid input for 'cluster': should be a number or None. You supplied {cluster}."
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

        # colours = list(sns.color_palette("colorblind").as_hex())

        data_by_interaction = from_memberships(  # format data to upsetplot requirements
            data.which_interactions.apply(lambda x: [x.strip() for x in x.split(",")]),
            data=data,
        )
        assert isinstance(
            data_by_interaction, pd.DataFrame
        ), "data_by_interaction needs to be a dataframe, check this was generated correctly."

        if cluster is not None:
            cluster_query = f"cluster_labels == {cluster}"
            data = data_by_interaction.query("@cluster_query", engine="python")
            # plot_colour = colours[cluster]
            cluster_name = f"cluster{cluster}"
        else:  # if no clusters supplied:
            data = data_by_interaction
            # plot_colour = "auto"
            cluster_name = data_set_name

        smallest_n_to_show = round(len(data) * show_min)

        self.logger.info(
            f"Attempting to plot cluster {cluster_name} and showing as far as {show_min}%, which is {smallest_n_to_show} repo-individuals from the data"  # {plot_colour}."
        )

        if show_counts:
            format = "{:,}"
        else:
            format = ""

        upset = UpSet(
            data=data,
            show_counts=format,
            sort_by=sort_combos_by,
            # facecolor=plot_colour,
            orientation="horizontal",
            min_subset_size=smallest_n_to_show,
        )
        upset.plot()
        plt.suptitle(
            f"{data_set_name} Interaction-Combinations (showing >{smallest_n_to_show} ({show_min}%) Repo-Individuals),  N={len(data)}"
        )
        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{cluster_name}_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")

    def plot_upset_plot_interaction_combinations(
        self,
        data: pd.DataFrame | Path,
        # colours: list | dict = sns.color_palette("colorblind"),
        separate_by_clusters: bool = False,
        show_min: float = 0.005,
        show_counts: bool = False,
        sort_combos_by: str = "cardinality",
        data_set_name: str = "dataset",
        file_name: str = "upset_plot_",
        save_type: str = "pdf",  # one of: ['png', 'pdf', 'svg']
        # min_repo_individs_per_combo: int = 2,
        # show_counts_per_combo: boolean = True,
        # show_pc: boolean = False,
    ):
        """
        This generates UpSet plots from GH interaction data from a dataframe or csv file.
        Data must be in a per-repo-individual format, and cluster labels must be in column titled "cluster_labels".

        """
        assert isinstance(
            data, (pd.DataFrame, Path)
        ), "Data is not of type pandas dataframe or Path; check your inputs."
        if isinstance(data, Path):
            self.logger.info(f"data is a path: {data}")
            data = pd.read_csv(filepath_or_buffer=data, header=0)
            assert isinstance(data, pd.DataFrame), "data could not be read in properly."
            self.logger.info(f"data is df, with shape: {data.shape}.")
        # if colours is a list and separate_by_clusters is true, does len(colours) match nunique('cluster_labels')?

        assert isinstance(
            data, pd.DataFrame
        ), "data should be dataframe format by now, check why this isn't correct"

        if separate_by_clusters:
            assert (
                "cluster_labels" in data.columns
            ), "df has no column 'cluster_labels - please check this is present in the data."
            n_clusters = data.cluster_labels.nunique()
            self.logger.info(
                f"Plotting upset plot for {data_set_name}, separating by {n_clusters} clusters from data labels."
            )

            for cluster in range(0, n_clusters - 1, 1):
                # range: start at 0 because this is how they're named by clustering
                # end on n_clusters - 1 because we're starting at 0 and off-by-one; increases by 1
                self.upset_plot(
                    cluster=cluster,
                    data=data,
                    show_min=show_min,
                    data_set_name=data_set_name,
                    show_counts=show_counts,
                    file_name=f"{file_name}_cluster-{cluster}_",
                )
            self.logger.info(
                f"Completed UpSet plotting for {n_clusters} clusters from data labels."
            )
        else:
            self.logger.info(
                f"Plotting upset plot for {data_set_name} without separating by clusters"
            )
            self.upset_plot(
                cluster=None,
                data=data,
                show_min=show_min,
                show_counts=show_counts,
                sort_combos_by="cardinality",
                data_set_name=data_set_name,
                file_name=file_name,
                save_type="pdf",  # one of: ['png', 'pdf', 'svg']
            )
            self.logger.info("Completed UpSet plotting.")
