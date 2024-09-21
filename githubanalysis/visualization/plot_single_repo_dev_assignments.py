"""Function to plot developer assignments as a side-by-side countplot/barplot for 1 named repo only"""

import sys
import pandas as pd
import matplotlib
import seaborn.objects as so
import datetime
from datetime import datetime
import logging

import utilities.get_default_logger as loggit


class DevCatPlotter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/plot_single_repo_dev_assignments_logs.txt",
            )
        else:
            self.logger = logger

    def plot_single_repo_dev_assignments(
        self,
        repo_name,
        devs_assignments_file="devs-assignments",
        write_out_format="png",
        read_in_location="data/",
        out_filename="plot-devs-assignments",
        write_out_location="images/",
    ):
        self.logger.debug("System arguments: {sys.argv[1:]}")

        if len(sys.argv) >= 2:
            repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
            devs_assignments_file = sys.argv[2]
            write_out_format = sys.argv[3]
            read_in_location = sys.argv[4]
            out_filename = sys.argv[5]
            write_out_location = sys.argv[6]

        else:
            repo_name = repo_name
            devs_assignments_file = devs_assignments_file
            write_out_format = write_out_format
            read_in_location = read_in_location
            out_filename = out_filename
            write_out_location = write_out_location

        # write out info setup
        current_date_info = datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        write_out = f"{write_out_location}{out_filename}_{sanitised_repo_name}"
        write_out_extra_info = f"{write_out}_{current_date_info}.{write_out_format}"

        dev_assignments_filepath = f"{read_in_location}{devs_assignments_file}.csv"
        # read in data to plot
        try:
            dev_assignments = pd.read_csv(dev_assignments_filepath, header=0)
        except Exception as e_readin:
            self.logger.error(
                f"Exception while trying to read in dev_assignments file {dev_assignments_filepath} for repo {repo_name}: {e_readin}"
            )

        # plotting themes/colours setup
        cat_order = ["both", "issues_only", "PRs_only", "neither"]
        cat_palette = {
            "both": "#2ca02c",
            "issues_only": "#1f77b4",
            "PRs_only": "#ff7f0e",
            "neither": "#d62728",
        }
        palette_list = list(cat_palette.values())

        f = matplotlib.figure.Figure(figsize=(10, 5))
        sf1, sf2 = f.subfigures(1, 2)
        sf1.suptitle(
            f"Repo {repo_name}; N devs = {len(dev_assignments.dev_name.index)}"
        )
        (
            so.Plot(data=dev_assignments, x="assignment", color="assignment")
            .add(so.Bars(width=0.95, alpha=1), so.Count(), legend=False)
            .scale(
                x=so.Nominal(order=cat_order),
                color=so.Nominal(palette_list, order=cat_order),
                legend=False,
            )
            .label(
                y="Number of Devs",
                x="Assignment Category",
                title="Assignment Type Distribution Amongst Devs",
                legend=None,
            )
            .theme({"axes.facecolor": "w"})
            .on(sf1)
            .plot()
        )
        (
            so.Plot(
                data=dev_assignments,
                x="assignment",
                y="contributions",
                color="assignment",
            )
            .theme(
                {
                    "axes.facecolor": "w",
                    "grid.color": "grey",
                    "grid.alpha": 0.5,
                    "axes.axisbelow": True,
                }
            )
            .add(so.Bar(width=0.93, alpha=1), so.Agg("mean"), legend=False)
            .scale(
                x=so.Nominal(order=cat_order),
                alpha=1,
                color=so.Nominal(palette_list, order=cat_order),
                legend=False,
            )
            .add(so.Range(color="black", alpha=0.6), so.Est(errorbar="se"), legend=None)
            .label(
                y="Commit Contributions",
                x="Assignment Category",
                title="Mean Dev Commit Contributions (+ standard error)",
            )
            .on(sf2)
            .plot()
        )

        f.savefig(fname=write_out_extra_info, format=write_out_format)
        self.logger.info(
            f"Plot of developer assignment for repo {repo_name} written out to {write_out_format} file at {write_out_extra_info}."
        )

    # this bit


if __name__ == "__main__":
    """
    plot developer assignment category data for a single specific GH repo. 
    """

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/plot_single_repo_dev_assignments_logs.txt",
    )

    devs_plotter = DevCatPlotter(logger)

    if len(sys.argv) >= 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
        devs_assignments_file = sys.argv[2]
        write_out_format = sys.argv[3]
        read_in_location = sys.argv[4]
        out_filename = sys.argv[5]
        write_out_location = sys.argv[6]

    try:
        devs_plotter.plot_single_repo_dev_assignments(
            repo_name=repo_name,
            devs_assignments_file=devs_assignments_file,
            write_out_format=write_out_format,
            read_in_location=read_in_location,
            out_filename=out_filename,
            write_out_location=write_out_location,
        )
    except Exception as e:
        logger.error(
            f"Exception while running plot_single_repo_dev_assignments() on repo {repo_name} for file {devs_assignments_file}: {e}"
        )
