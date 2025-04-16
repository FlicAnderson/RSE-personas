"""Combine prepared issues and commits datasets."""

from pathlib import Path
import argparse
import datetime
import numpy as np
import pandas as pd
import logging

import utilities.get_default_logger as loggit


class PrepDataCombined:
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
                log_name="logs/pre-analysis_data_combined_prep.txt",
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
        self.write_location = Path("data/" if not in_notebook else "../../data/")

    def process_multi_origin_data(
        self,
        commits_data_file: str | Path,
        issues_data_file: str | Path,
        read_location: str | Path,
        write_location: str | Path,
    ) -> pd.DataFrame | None:
        """
        Combines per-dev (per repo-individual) data from commits and issue tickets
        into single dataframe for analysis.

        Outputs: returns omnirepo, generates output csv file.

        Example Run: python githubanalysis/processing/pre-analysis_data_combined_prep.py -c commits-data-per-dev_x2320-repos_2025-04-15.csv -i issues-data-per-dev_x2829-repos_x237715-repo-individuals_2025-04-15.csv
        """

        commits_data_file = Path(read_location, commits_data_file)
        issues_data_file = Path(read_location, issues_data_file)
        self.logger.info(f"Commits data file: {commits_data_file}")
        self.logger.info(f"Issues data file: {issues_data_file}")

        # print(f"Commits data file: {commits_data_file}")
        # print(f"Issues data file: {issues_data_file}")

        start_time = datetime.datetime.now()

        commits_multirepo = pd.read_csv(commits_data_file)
        self.logger.info(f"length of commits df is {len(commits_multirepo)}")

        issues_multirepo = pd.read_csv(issues_data_file)
        self.logger.info(f"length of issues df is {len(issues_multirepo)}")

        commits_multirepo = commits_multirepo.drop_duplicates(
            keep="first", ignore_index=True
        )
        issues_multirepo = issues_multirepo.drop_duplicates(
            keep="first", ignore_index=True
        )

        omnirepo = pd.merge(
            left=commits_multirepo,
            right=issues_multirepo,
            how="outer",
            left_on=["author_username", "repo_name"],
            right_on=["issue_username", "repo_name"],
            # validate="one_to_one",
            suffixes=("_commits", "_issues"),
            indicator="commiss_merge",
        )
        self.logger.info(f"Merged dataset has length: {len(omnirepo)}.")

        # fill missing values where necesary
        omnirepo["n_commits"] = omnirepo["n_commits"].fillna(value=0)
        omnirepo["n_issues"] = omnirepo["n_issues"].fillna(value=0)
        omnirepo["pc_repo_commits"] = omnirepo["pc_repo_commits"].fillna(value=0)
        omnirepo["pc_repo_issues"] = omnirepo["pc_repo_issues"].fillna(value=0)
        omnirepo["pc_issues_assigned_of_assigned"] = omnirepo[
            "pc_issues_assigned_of_assigned"
        ].fillna(value=0)
        omnirepo["n_issues_assigned"] = omnirepo["n_issues_assigned"].fillna(value=0)
        omnirepo["author_username"] = omnirepo["author_username"].fillna(value="None")
        omnirepo["issue_author_username"] = omnirepo["issue_author_username"].fillna(
            value="None"
        )
        omnirepo["assigned_devs"] = omnirepo["assigned_devs"].fillna(value="unassigned")

        # create authoratative ghusername field for issues df:
        omnirepo["gh_username"] = np.where(
            omnirepo["author_username"] == "None",
            omnirepo["issue_username"],
            omnirepo["author_username"],
        )

        # create human-readable dataset source column:
        d = {"left_only": "Only Commits", "right_only": "Only Issues", "both": "Both"}
        omnirepo["_dataset_source"] = omnirepo["commiss_merge"].map(d)

        n_repos_omnirepo = int(omnirepo.groupby("repo_name").ngroups)

        filestr = f"merged-data-per-dev_x{omnirepo['repo_name'].nunique()}-repos_{self.current_date_info}.csv"
        writeout_path = Path(write_location, filestr)

        try:
            omnirepo.to_csv(path_or_buf=writeout_path, header=True, index=False)
            self.logger.info(f"Merged dataset file written out to {writeout_path}")

            end_time = datetime.datetime.now()

            self.logger.info(
                f"Run time for {n_repos_omnirepo} repos with {len(omnirepo)} devs cumulatively: {end_time - start_time}"
            )

            self.logger.info(
                f"Saved devs_commits_data df for {n_repos_omnirepo} repos with {len(omnirepo)} devs to file: {filestr}"
            )

            return omnirepo  # RETURN MERGED DATASET

        except Exception as e:
            self.logger.error(
                f"Error in attempting to write output file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
            )


parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--commits-data-per-dev-file",
    metavar="COMMITS_DATA_PER_DEV_FILE",
    help="Path to .csv file containing commits data (line per repo-individual), eg 'commits-data-per-dev_x5828-repos_2025-02-15.csv'.",
    type=str,
)
parser.add_argument(
    "-i",
    "--issues-data-per-dev-file",
    metavar="ISSUES_DATA_PER_DEV_FILE",
    help="Path to .csv file containing issues data (line per repo-individual), eg 'issues-data-per-dev_x1716-repos_2024-12-11.csv'.",
    type=str,
)


if __name__ == "__main__":
    args = parser.parse_args()
    commits_data: str = args.commits_data_per_dev_file
    issues_data: str = args.issues_data_per_dev_file

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/pre-analysis_data_combined_preps_logs.txt",
        in_notebook=False,
    )

    if ((commits_data is not None) + (issues_data is not None)) != 2:
        logger.error(
            "Exactly two arguments allowed; please avoid your current whole deal and supply commits and issues per-dev data files."
        )
        exit(1)

    logger.info(f"Args: {args}")
    print(args)

    logger.info(
        f"Running data combination pre-analysis preparation methods on commits data file {commits_data} and issues file {issues_data}."
    )

    prepdatacombined = PrepDataCombined(in_notebook=False, logger=logger)

    combined_data = prepdatacombined.process_multi_origin_data(
        commits_data_file=commits_data,
        issues_data_file=issues_data,
        read_location="data/",
        write_location="data/",
    )
