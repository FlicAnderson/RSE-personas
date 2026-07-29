"""This script is investigating relationships between high-interactivity RSE Personas and PR Code Review Interactions."""

import pandas as pd
from pathlib import Path
import datetime
from dataclasses import dataclass


import utilities.get_default_logger as loggit


@dataclass
class Datafiles:
    reviews_file_set1 = "merged_reviews_data_all_types_x1284repos_x2593270reviews_x3810reviewfiles_2026-07-17.csv"
    personas_file_set1 = (
        "sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv"
    )
    interactns_file_set1 = (
        "merged-interactions-data-per-dev_x1284repos_x119492_2026-07-27.csv"
    )
    high_interactivity_repo_individuals_file_set1 = "analysis_run_sample_45pc_cluster1_2025-05-13/sample_45pc_cluster1_personas_named_dataset_2025-05-30.csv"
    combined_data_set1_w_revs = "per-repo-individual-existing-and-reviews-data_x2868repos_x244143repo-individs_2026-07-27.csv"


if __name__ == "__main__":
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/high_interactivity_x_PRCR.txt",
        in_notebook=False,
    )
    datafiles = Datafiles()
    current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")
    print(current_date_info)

    data_location = "data/"

    # interactions_file = Path(data_location, datafiles.interactns_file_set1)

    # interactns_df = pd.read_csv(
    #     interactions_file,
    #     header=0,
    #     usecols=["repo_name", "gh_username", "pc_reviews_created"],
    # )
    # interactns_df

    # 700 club:

    high_interactivity_devs = pd.read_csv(
        Path(data_location, datafiles.high_interactivity_repo_individuals_file_set1),
        header=0,
        dtype="object",
        usecols=[
            "repo_name",
            "gh_username",
            "RSE_persona",
        ],
    )
    filter_list = [
        "low-process_closer",
        "low-coding_closer",
        "active_contributor",
    ]

    personas_in_df = high_interactivity_devs["RSE_persona"].unique()

    for persona in personas_in_df:
        assert persona in filter_list, (
            "Error, this persona is not expected in Set1 A1B1 dataset (high interactivity personas)"
        )

    # subset combined_data_set1_w_revs:
    combined_data = pd.read_csv(
        Path(data_location, datafiles.combined_data_set1_w_revs),
        header=0,
        dtype="object",
        low_memory=False,
        # import ALL columns
    )

    high_data = pd.merge(
        high_interactivity_devs,
        combined_data,
        how="left",
        on=["repo_name", "gh_username"],
    )

    filestr = f"per-repo-individual-existing-and-reviews-data_x{high_data.repo_name.nunique()}repos_x{high_data.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_2026-07-29.csv"
    writeout_path = Path(data_location, filestr)

    try:
        high_data.to_csv(
            path_or_buf=writeout_path,
            header=True,
            index=False,
        )
    except Exception as e:
        print(
            f"Error in attempting to write combined data-per-dev file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
        )
        raise
