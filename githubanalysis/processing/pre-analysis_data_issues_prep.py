"""Collate ISSUES datafiles, generate dataframes ready for analysis."""

from pathlib import Path
import datetime
import os
import re
import pandas as pd
import logging
import numpy as np
from ast import literal_eval

import utilities.get_default_logger as loggit


class PrepDataIssues:
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
                log_name="logs/pre-analysis_data_issues_prep.txt",
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

    def process_issues(
        self,
        read_location: str | Path,
        write_location: str | Path,
    ) -> pd.DataFrame | None:
        """
        (Follows format of pre-analysis_data_commits_prep.py)

        Pull in processed-issues_* files from read_location folder (default: data/)
        Read in issues data per file (equivalent to per-repo).
        Create data aggregations per dev per repo; gather hattori/vasilescu commit cats data summaries
        Join dfs together to get aggregated issues info per dev and aggregated h/v cats data
        Reshuffle various df slices and joins to get good output formats
        Collate devs issues data; Write out devs issues data to csv
        Return devs issues data

        ### NOTE:
        # known issue where: n_of_issues_creators can be NaN if the gh_username is assigned to an issue, but has not created any issues in the repo
        """
        start_time = datetime.datetime.now()

        repolist = [
            f
            for f in os.listdir(read_location)
            if re.match(r"(processed-issues_).*(.csv)", f)
        ]
        logger.info("{repolist}")

        multirepo = pd.DataFrame()
        multirepo_assigns = pd.DataFrame()

        print(f"Currently processing {len(repolist)} repos' worth of issues")
        print("---")

        for repofile in repolist:
            logger.debug(f"{repofile}")
            tmplocat = f"{read_location}{repofile}"
            repo = pd.read_csv(tmplocat)

            tmpname = repo["repo_name"][0]
            n_issues_pr_repo = len(repo)
            logger.debug(f"Number of issues for repo {tmpname} is: {n_issues_pr_repo}")

            tmp_nonempty_fields = {
                "repo_name": tmpname,
                "n_issues_total": len(repo),
                "assignees_list_usernames": (
                    repo["assignees_list_usernames"] != "[]"
                ).sum(),
            }
            tmpdf_nonempty_fields = pd.DataFrame(tmp_nonempty_fields, index=[0])

            exploded_devs = repo
            exploded_devs["assigned_devs"] = repo["assignees_list_usernames"].apply(
                literal_eval
            )
            exploded_devs = exploded_devs.explode(column="assigned_devs")

            exploded_devs["assigned_devs"] = exploded_devs["assigned_devs"].fillna(
                "unassigned"
            )
            tmp_assigns = pd.DataFrame(
                exploded_devs.groupby(["assigned_devs"], as_index=False).nunique()
            )  # as_index=False allows joins
            tmp_assigns["repo_name"] = tmpname

            assignees = tmp_assigns.drop(
                tmp_assigns[tmp_assigns.assigned_devs == "unassigned"].index
            )

            number_devs_assigned = assignees["assigned_devs"].nunique()
            number_issues_assigned_exploded = assignees["Unnamed: 0"].sum()
            total_unique_assigned_issues_ids = len(
                exploded_devs[
                    exploded_devs["assigned_devs"] != "unassigned"
                ].index.unique()
            )  # unique number of issues assigned to anybody(s)
            assignees = assignees.rename(columns={"Unnamed: 0": "n_issues_assigned"})

            assignees["pc_issues_assigned_of_assigned"] = (
                assignees["n_issues_assigned"] / total_unique_assigned_issues_ids
            ) * 100
            assignees = assignees[
                [
                    "repo_name",
                    "assigned_devs",
                    "n_issues_assigned",
                    "pc_issues_assigned_of_assigned",
                ]
            ]

            logger.debug(f"{number_devs_assigned}")
            logger.debug(f"{number_issues_assigned_exploded}")

            tmpdf = pd.DataFrame(
                {
                    "repo_name": tmpname,
                    "issue_author_username": list(
                        repo.groupby("issue_author_username").size().keys()
                    ),
                    "n_issues": list(repo.groupby("issue_author_username").size()),
                    "pc_repo_issues": (repo.groupby("issue_author_username").size())
                    / len(repo)
                    * 100,
                }
            )
            print(
                f"repo {tmpname} has {len(tmpdf)} people creating {n_issues_pr_repo} issues."
            )

            print(
                f"repo {tmpname} has {number_devs_assigned} devs assigned to {tmpdf_nonempty_fields['n_issues_total'][0]} unique issues, of which {total_unique_assigned_issues_ids} issues are assigned to one or more dev."
            )

            tmpdf["n_of_issues_creators"] = len(tmpdf)
            logger.debug(f"Number of issue creators for repo {tmpdf} is: {len(tmpdf)}")

            multirepo = pd.concat([multirepo, tmpdf], axis=0, ignore_index=True)
            multirepo_assigns = pd.concat(
                [multirepo_assigns, assignees], axis=0, ignore_index=True
            )
            logger.debug("----")
            # end of loop

        # join issues data and assignment data to give single richer df
        devs_issues_data = pd.merge(
            left=multirepo,
            right=multirepo_assigns,
            how="outer",
            left_on=["issue_author_username", "repo_name"],
            right_on=["assigned_devs", "repo_name"],
            # validate="one_to_one",
            indicator=True,
        )
        devs_issues_data["n_issues_assigned"] = devs_issues_data[
            "n_issues_assigned"
        ].fillna(value=0)
        devs_issues_data["pc_issues_assigned_of_assigned"] = devs_issues_data[
            "pc_issues_assigned_of_assigned"
        ].fillna(value=0)
        devs_issues_data["n_issues"] = devs_issues_data["n_issues"].fillna(value=0)
        devs_issues_data["pc_repo_issues"] = devs_issues_data["pc_repo_issues"].fillna(
            value=0
        )
        devs_issues_data["assigned_devs"] = devs_issues_data["assigned_devs"].fillna(
            value="unassigned"
        )
        devs_issues_data["issue_author_username"] = devs_issues_data[
            "issue_author_username"
        ].fillna(value="None")

        # create authoratative ghusername field for issues df:
        devs_issues_data["issue_username"] = np.where(
            devs_issues_data["issue_author_username"] != "None",
            devs_issues_data["issue_author_username"],
            devs_issues_data["assigned_devs"],
        )

        # write out issues data with informative filename
        filestr = f"{self.write_location}issues-data-per-dev_x{devs_issues_data['repo_name'].nunique()}-repos_{self.current_date_info}.csv"
        devs_issues_data.to_csv(path_or_buf=filestr, header=True, index=False)

        end_time = datetime.datetime.now()

        logger.info(
            f"Run time for {len(repolist)} repos with {len(devs_issues_data)} devs cumulatively: {end_time - start_time}"
        )

        logger.info(
            f"Saved devs_issues_data df for {len(repolist)} repos with {len(devs_issues_data)} devs to file: {filestr}"
        )
        return devs_issues_data


if __name__ == "__main__":
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/pre-analysis_data_issues_preps_logs.txt",
        in_notebook=False,
    )

    prepdataissues = PrepDataIssues(in_notebook=False, logger=logger)

    prepdataissues.process_issues(read_location="data/", write_location="data/")
