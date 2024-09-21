"""Plot contributor commit stats data from GitHub repo."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from pandas.errors import EmptyDataError


def plot_repo_contributor_commits_stats(
    repo_data_df,
    repo_name,
    save_out=True,
    save_name="contributor_commits_totals_plot",
    save_type="png",
    save_out_location="images/",
    verbose=True,
):
    """
    Plot commits contribution totals from a GitHub repository, data should be dataframe obtained by get_contributor_commits_stats().
    :param repo_data_df: data to plot
    :type: pd.DataFrame
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param save_out: save plot object to file? Default=True
    :type: bool
    :param save_name: filename prefix to save plot object as. Default='contributor_commits_totals_plot'
    :type: str
    :param save_type: file type to save plot as ('pdf' or 'png') . Default='png'
    :type: str
    :param save_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param verbose: return status info. Default: True
    :type: bool
    :return plot: contributor commits totals data barplot.
    :type: ?plot?
    """

    # verify input is df and not empty
    if not isinstance(repo_data_df, pd.DataFrame):
        raise TypeError("Ensure input data is pd.DataFrame format.")
    if repo_data_df.empty is True:
        raise EmptyDataError("There is no data in dataframe repo_data_df.")

    # check df has required columns for plotting
    if "total" not in repo_data_df.columns:
        raise ValueError("Dataframe does not contain required column 'total'.")
    if "contributor_author" not in repo_data_df.columns:
        raise ValueError(
            "Dataframe does not contain required column 'contributor_author'."
        )

    # check repo_name and try and pull it out of df if not supplied.
    if repo_name is None:
        if repo_data_df.repo_name.nunique() == 1:
            repo_name = repo_data_df.repo_name[0]  # use first repo_name value
        elif repo_data_df.repo_name.nunique() > 1:
            repo_name = "multiple repos"
            print("Multiple repositories included in dataset")
        else:
            raise ValueError("Cannot obtain repo_name from dataset `repo_data_df`")
    else:
        repo_name = repo_name  # from function arguments.

    if save_out:
        # check there's a save_name if saving out the plot.
        if save_name is None:  # this shouldn't occur hopefully as there's a default.
            raise ValueError("save_name must be supplied for plot filename.")
        if not isinstance(save_name, str):
            raise ValueError("save_name must be a string.")

        # which file format to save as?
        if save_type not in ("png", "pdf"):
            raise ValueError('save_type must be one of "png" (default) or "pdf".')

        # verify save_out_location is valid
        save_path = Path(save_out_location)
        if save_path.exists() is False:
            raise OSError("Read-in file does not exist at path:", save_path)

    # get some overall stats (sum total, 25% of commits):
    all_commits = repo_data_df["total"].sum()
    contrib25pc = all_commits * 0.25

    # actual plotting:
    sns.set_theme()
    sns.set_palette("colorblind")

    ax = sns.barplot(
        data=repo_data_df, x="contributor_author", y="total", color="black"
    )
    ax.axhline(y=contrib25pc, linestyle="--", alpha=0.5)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="left", fontsize=7)
    plt.tight_layout()

    if save_out:
        # create filename to use from repo_name
        save_out_filename = f'{save_name}__{repo_name.replace("/", "_")}'

        # build path + filename + file extension string
        plot_file = f"{save_out_location}{save_out_filename}.{save_type}"

        plt.savefig(plot_file, bbox_inches="tight")

        plt.close()

    else:
        plt.show()
        plt.close()
