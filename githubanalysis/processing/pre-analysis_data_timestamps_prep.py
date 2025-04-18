"""Get timestamp and interaction types info for issues AND commits datasets."""

from pathlib import Path
import datetime
import os
import re
from ast import literal_eval
import pandas as pd
import logging


import utilities.get_default_logger as loggit

pd.options.mode.copy_on_write = True


class PrepDataTimes:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path
    read_location: Path

    pd.options.mode.copy_on_write = True

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
        self.write_location = Path("data/" if not in_notebook else "../../data/")

    def get_commit_interactions(self, datafile: str | Path) -> pd.DataFrame:
        """
        Function to read processed_commits data file for 1 repo;
        pulls in timestamp data for each commit, labelling interaction type;
        transforms and reshapes dataset;
        returns df of commits including datetime_day, contribution, and
        interaction_type information.
        """
        pd.options.mode.copy_on_write = True

        commitsdf = pd.read_csv(datafile, index_col=0, lineterminator="\n")

        # remove unwanted columns:
        commitsdf = commitsdf[
            [
                "repo_name",
                "author_username",
                "author_fullname",
                "comitter_username",
                "commit_sha",
                "author_commit_date",
                "commit_message",
            ]
        ]

        # deal with issue data (NOT pull request) only:
        interactions_df_commits = commitsdf

        # rename columns, including commits usernames field to 'gh_username' to allow concats without stress.
        interactions_df_commits.rename(
            columns={"author_username": "gh_username"}, inplace=True
        )
        interactions_df_commits.rename(
            columns={"author_commit_date": "datetime"}, inplace=True
        )
        interactions_df_commits.loc[:, "interaction_type"] = "commit_created"
        interactions_df_commits["contribution"] = "commit"

        # pull out only date (YYYY-MM-DD) info to allow 'unique DAYs' to be obtained
        interactions_df_commits.loc[:, "datetime_day"] = (
            interactions_df_commits.datetime.apply(lambda x: pd.Timestamp(x).date())
        )

        interactions_df_commits = interactions_df_commits[
            [
                "repo_name",
                "gh_username",
                "datetime_day",
                "contribution",
                "interaction_type",
            ]
        ]

        return interactions_df_commits

    def get_issues_PRs_interactions(self, datafile: str | Path) -> pd.DataFrame:
        """
        Function to read processed_issues data file for 1 repo;
        pulls in timestamp data for each issue and pull request;
        transforms and reshapes dataset;
        returns df of issues including datetime_day, contribution, and
        interaction_type information.
        """
        pd.options.mode.copy_on_write = True

        rawissuesdf = pd.read_csv(datafile, index_col=0, lineterminator="\n")
        assert (
            len(rawissuesdf) != 0
        ), f"File does not contain a dataframe; check input file {datafile}"

        # remove unwanted columns ahead of data melt / reshape:
        rawissuesdf = rawissuesdf[
            [
                "repo_name",
                "issue_author_username",
                "author_association",
                "issue_number",
                "issue_state",
                "created_at",
                "closed_at",
                "closed_by",
                "pull_request",
            ]
        ]

        # create open issues df set; copy datetime info into new column, create interaction column to mimic melt() on closed issues

        if not (open_issues_df := rawissuesdf.query("issue_state == 'open'")).empty:
            open_issues_df.loc[:, "datetime"] = rawissuesdf.query(
                "issue_state == 'open'"
            )[["created_at"]]
            open_issues_df.loc[:, "interaction"] = "created_at"
            open_issues = [open_issues_df]
        else:
            open_issues = []

        issuesdf = pd.concat(  # rejoin open and closed issues but treated differently
            open_issues  # don't melt open issues as we only want 1 'interaction' for them
            + [
                rawissuesdf.query(
                    "issue_state == 'closed'"
                ).melt(  # create duplicate issue_number entries by splitting 'closed' into created_at and closed_at
                    id_vars=[
                        "repo_name",
                        "issue_author_username",
                        "issue_number",
                        "issue_state",
                        "closed_by",
                        "pull_request",
                    ],
                    value_vars=["created_at", "closed_at"],
                    var_name="interaction",
                    value_name="datetime",
                )
            ]
        ).drop(
            columns=["created_at", "closed_at", "author_association"], errors="ignore"
        )

        issuesdf.loc[:, "contribution"] = "issue"
        issuesdf.loc[issuesdf["pull_request"].notna(), "contribution"] = (
            "pull_request"  # D:
        )

        # pull out only date (YYYY-MM-DD) info to allow 'unique DAYs' to be obtained
        issuesdf.loc[:, "datetime_day"] = issuesdf.datetime.apply(
            lambda x: pd.Timestamp(x).date()
        )

        # combine contribution_type and interaction, editing text to create clearer result:
        issuesdf.loc[:, "interaction_type"] = (
            issuesdf[["contribution", "interaction"]].agg("_".join, axis=1)
        ).str.replace("_at", "")

        # rename users for better joins/consistency
        issuesdf = issuesdf.rename(columns={"issue_author_username": "gh_username"})

        # pull out the closed_by info:
        issuesdf["closer"] = issuesdf["closed_by"].apply(
            lambda row: row if pd.isna(row) else literal_eval(row)["login"]
        )

        # update gh_username based on closer data if issue is closed
        issuesdf.loc[:, "gh_username"] = issuesdf.apply(
            lambda row: row["closer"]
            if pd.notna(row["closer"]) and row["interaction"] == "closed_at"
            else row["gh_username"],
            axis=1,
        )

        # drop non-required columns
        interactions_df_commits = issuesdf[
            [
                "repo_name",
                "gh_username",
                "datetime_day",
                "contribution",
                "interaction_type",
            ]
        ]

        return interactions_df_commits

    def join_and_calculate_all_interactions(
        self, commits_interactions: pd.DataFrame, issues_interactions: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Function combines issues and commits interactions and timestamp data
        returns df of this, including various calculated values of interaction data.
        """
        pd.options.mode.copy_on_write = True

        self.logger.debug(issues_interactions.info())
        self.logger.debug(commits_interactions.info())

        self.logger.debug(issues_interactions.columns)
        self.logger.debug(commits_interactions.columns)

        filestr_iss = f"issues_interactions_x{len(issues_interactions)}_{self.current_date_info}.csv"
        writeout_path_iss = Path(self.write_location, filestr_iss)

        issues_interactions.to_csv(writeout_path_iss, header=True, index=False)

        filestr_cmt = f"commits_interactions_x{len(commits_interactions)}_{self.current_date_info}.csv"
        writeout_path_cmt = Path(self.write_location, filestr_cmt)

        commits_interactions.to_csv(writeout_path_cmt, header=True, index=False)
        self.logger.debug(
            f"wrote out commits and issues intercations dfs to separate csv files: {writeout_path_cmt} and {writeout_path_iss}"
        )

        # JOIN ISSUES AND COMMITS DATA TOGETHER HERE:
        all_types_interactions = pd.concat(
            [issues_interactions, commits_interactions],
            join="outer",
        )
        self.logger.debug("joined issues and commits interactions")
        # # remove rows where gh_username is NaN/NA
        all_types_interactions = all_types_interactions.dropna(
            subset="gh_username", axis=0
        )
        self.logger.debug("removed missing GH_username rows")

        print(all_types_interactions["datetime_day"])
        print(all_types_interactions["datetime_day"])

        self.logger.debug(
            all_types_interactions.groupby(["repo_name", "gh_username"])["datetime_day"]
        )

        print(
            all_types_interactions.groupby(["repo_name", "gh_username"])["datetime_day"]
        )

        self.logger.debug(
            type(
                all_types_interactions.groupby(["repo_name", "gh_username"])[
                    "datetime_day"
                ]
            )
        )
        n_all_before = len(all_types_interactions)
        n_gh_users = all_types_interactions["gh_username"].isna().sum()
        n_repos = all_types_interactions["repo_name"].isna().sum()
        n_missing_date = all_types_interactions["datetime_day"].isna().sum()

        self.logger.info(
            f"Filtering out rows including {n_gh_users + n_repos + n_missing_date} missing data elements: {n_repos} rows missing repo_names; {n_missing_date} rows missing date_time days."
        )

        # remove missing repo_name data, and rows with missing gh_usernames
        # AND with missing datetime_day values (NaT)
        all_types_interactions = all_types_interactions.dropna(
            subset=["gh_username", "repo_name", "datetime_day"]
        )
        n_after_drop = len(all_types_interactions)

        self.logger.info(
            f"Filtering out {n_all_before - n_after_drop} rows with missing data out of {n_all_before} rows in total."
        )
        self.logger.info(f"{n_after_drop} rows remaining.")

        all_types_interactions.to_csv(
            Path(self.write_location, "combined_interactions_data")
        )

        try:
            # pull out the number of days timediff between 1st and latest interactions
            timediff = (
                all_types_interactions.groupby(["repo_name", "gh_username"])[
                    "datetime_day"
                ].max()
                - all_types_interactions.groupby(["repo_name", "gh_username"])[
                    "datetime_day"
                ].min()
            )

        except Exception as e:
            tmp_errors = all_types_interactions["datetime_day"].isna()
            tmp_errors = all_types_interactions[tmp_errors]

            self.logger.error(
                f"error {e}: value_counts of types for datetime_day are: {all_types_interactions['datetime_day'].apply(lambda x: str(type(x))).value_counts(dropna=False)}"
            )
            self.logger.error(f"tmp_errors is: {tmp_errors}")
            tmp_errors.to_csv(Path(self.write_location, "error-rows_interactions_data"))

            raise

        self.logger.debug(
            "completed timediff calculation: datetime_day max - datetime_day min by groups"
        )
        timediff = timediff.apply(
            lambda x: x + datetime.timedelta(days=1)
        )  # add 1 day so the time difference is inclusive of both first and last days (ie no zeroes!)
        timediff = timediff.apply(lambda x: x.days).reset_index()
        timediff = timediff.rename(columns={"datetime_day": "interaction_period_days"})
        self.logger.debug("rename timediff as interaction_period_days")

        # pull interaction_types into separate columns, and add counts of each category into them
        status_df = (
            all_types_interactions.groupby(
                ["repo_name", "gh_username", "interaction_type"]
            )
            .agg(n_interactions=pd.NamedAgg(column="repo_name", aggfunc="count"))
            .pivot_table(
                values="n_interactions",
                index=["repo_name", "gh_username"],
                columns="interaction_type",
                fill_value=0,
            )
            .reset_index()
        )

        # count unique interaction_days per user:
        status_df["interaction_days"] = (
            all_types_interactions.groupby(by=["repo_name", "gh_username"])[
                ["datetime_day"]
            ]
            .nunique()
            .reset_index()["datetime_day"]
        )

        # join on 'interaction_period_days' column from timediff
        status_df = pd.merge(
            status_df, timediff, how="inner", on=["repo_name", "gh_username"]
        )

        for col in [
            "commit_created",
            "issue_closed",
            "issue_created",
            "pull_request_created",
        ]:
            if col not in status_df.columns:
                status_df.loc[:, col] = 0

        # create ratio of created:closed issues per user:
        status_df["created-closed_issues"] = (
            status_df["issue_created"] - status_df["issue_closed"]
        )

        # should not result in a divide by zero issue because no issues datafile exists if no issues in repo
        # (hopefully)
        status_df["pc_created-closed_issues"] = (
            status_df["issue_created"]
            / status_df.groupby("repo_name")["issue_created"].transform("sum")
        ) - (
            status_df["issue_closed"]
            / status_df.groupby("repo_name")["issue_closed"].transform("sum")
        ) * 100

        # calculate number of different interactions by each user:
        status_df["sum_n_interactions"] = (
            status_df["commit_created"]
            + status_df["issue_closed"]
            + status_df["issue_created"]
            + status_df["pull_request_created"]
        )

        # mean_n_interactions_per_interaction_days: sum of interactions ()all types) divide by number of unique interaction days
        status_df["mean_n_interactions_per_interaction_day"] = (
            status_df["sum_n_interactions"] / status_df["interaction_days"]
        )

        # gather text labels for which interactions were done by users:
        status_df["which_interactions"] = (
            all_types_interactions.groupby(by=["repo_name", "gh_username"])[
                ["interaction_type"]
            ]
            .agg(lambda x: ", ".join(list(map(str, set(x)))))
            .reset_index()["interaction_type"]
        )

        # get breadth of unique interactions :
        status_df["breadth_interactions"] = status_df.which_interactions.apply(
            lambda x: len(x.split())
        )

        # per-repo pc(pull_requests):
        status_df["pc_pull_request_created"] = (
            status_df["pull_request_created"]
            / status_df.groupby("repo_name")["pull_request_created"].transform("sum")
            * 100
        )

        # per-repo sum(commits):
        status_df["pc_commit_created"] = (
            status_df["commit_created"]
            / status_df.groupby("repo_name")["commit_created"].transform("sum")
            * 100
        )

        # per-repo pc(opened issues):
        status_df["pc_issue_created"] = (
            status_df["issue_created"]
            / status_df.groupby("repo_name")["issue_created"].transform("sum")
            * 100
        )

        # per-repo pc(closed issues):
        status_df["pc_issue_closed"] = (
            status_df["issue_closed"]
            / status_df.groupby("repo_name")["issue_closed"].transform("sum")
            * 100
        )

        # per-repo pc(closed issues):
        status_df["pc_issue_closed"] = (
            status_df["issue_closed"]
            / status_df.groupby("repo_name")["issue_closed"].transform("sum")
            * 100
        )

        # per-repo pc of total sum of n interactions:
        status_df["pc_sum_n_interactions"] = (
            status_df["sum_n_interactions"]
            / status_df.groupby("repo_name")["sum_n_interactions"].transform("sum")
            * 100
        )

        # per-repo pc of repo interaction_days:
        status_df["pc_interaction_days"] = (
            status_df["interaction_days"]
            / status_df.groupby("repo_name")["interaction_days"].transform("sum")
            * 100
        )

        return status_df

    _COMMITS_PATTERN = re.compile(
        r"^processed-commits_(.*)[0-9]{4}-[0-9]{2}-[0-9]{2}\.csv$"
    )
    _ISSUES_PATTERN = re.compile(
        r"^processed-issues_(.*)[0-9]{4}-[0-9]{2}-[0-9]{2}\.csv$"
    )

    def interactions_data_workflow(
        self,
        read_location: str | Path,
        write_location: str | Path,
    ) -> pd.DataFrame | None:
        """
        Reads in processed data from commits and issue tickets
        gathers timestamp information and processes it, then combines all
        into single dataframe for analysis.
        """
        pd.options.mode.copy_on_write = True

        start_time = datetime.datetime.now()

        # commit_matches = list(
        #     filter(
        #         lambda x: x is not None,
        #         (re.match(self._COMMITS_PATTERN, f) for f in os.listdir(read_location)),
        #     )
        # )

        issues_files_repolist = [
            f for f in os.listdir(read_location) if re.match(self._ISSUES_PATTERN, f)
        ]

        # for i in commit_matches:
        #     assert i
        #     name = i.group(1)

        # get all the processed-commits files from the folder:
        commits_files_repolist = [
            f
            for f in os.listdir(read_location)
            if re.match(r"(processed-commits_).*(\.csv)", f)
        ]
        # same for issues files:
        issues_files_repolist = [
            f
            for f in os.listdir(read_location)
            if re.match(r"(processed-issues_).*(\.csv)", f)
        ]

        self.logger.info(
            f"Working on {len(commits_files_repolist)} files for commits and {len(issues_files_repolist)} issues data files"
        )

        commits_interactions = pd.DataFrame()
        issues_interactions = pd.DataFrame()

        for file in commits_files_repolist:
            file = Path(read_location, file)
            if file.exists():
                self.logger.debug(f"Running get_commit_interactions on file {file}.")
                commits_interactions_next = self.get_commit_interactions(file)
                commits_interactions = pd.concat(
                    [commits_interactions, commits_interactions_next]
                )

        self.logger.info(
            f"Generated df of {len(commits_interactions)} commits interactions."
        )

        for file in issues_files_repolist:
            file = Path(read_location, file)
            if file.exists():
                self.logger.debug(
                    f"Running get_issues_PRs_interactions on file {file}."
                )
                issues_interactions_next = self.get_issues_PRs_interactions(file)
                issues_interactions = pd.concat(
                    [issues_interactions, issues_interactions_next]
                )

        self.logger.info(
            f"Generated df of {len(issues_interactions)} issues interactions."
        )

        assert (
            commits_interactions is not None
        ), "commits_interactions type is None; something went wrong!"
        assert (
            issues_interactions is not None
        ), "issues_interactions type is None; something went wrong!"

        try:
            all_interactions_data = self.join_and_calculate_all_interactions(
                commits_interactions, issues_interactions
            )

            # replace misisng data with zeroes:
            # this shows NO interactions if we don't have any entries for
            # that repo-individ from any of the API endpoints
            all_interactions_data.fillna(value=0, inplace=True)

            self.logger.info(
                f"Dataset of combined issues and commits interactions info contains {all_interactions_data.repo_name.nunique()} unique repo_names."
            )
            self.logger.info(
                f"... and contains {all_interactions_data.gh_username.nunique()} unique GH_usernames."
            )
            self.logger.info(
                f"... BUT the interactions info contains {all_interactions_data.groupby(['repo_name', 'gh_username']).ngroups} unique repo-individuals."
            )

            n_repos_all_interactions_data = int(
                all_interactions_data.groupby("repo_name").ngroups
            )
            filestr = f"merged-interactions-data-per-dev_x{n_repos_all_interactions_data}-repos_{self.current_date_info}.csv"
            writeout_path = Path(write_location, filestr)

            try:
                # WRITE OUT THIS SUPER IMPORTANT DATA TO FILE!
                all_interactions_data.to_csv(
                    path_or_buf=writeout_path, header=True, index=False
                )

                self.logger.info(f"Merged dataset file written out to {writeout_path}")

                end_time = datetime.datetime.now()

                self.logger.info(
                    f"Run time for {n_repos_all_interactions_data} repos with {len(all_interactions_data)} devs cumulatively: {end_time - start_time}"
                )

                self.logger.info(
                    f"Saved devs_commits_data df for {n_repos_all_interactions_data} repos with {len(all_interactions_data)} devs to file: {filestr}"
                )

                return all_interactions_data  # RETURN MERGED DATASET

            except Exception as e:
                self.logger.error(
                    f"Error in attempting to write output file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
                )
                raise

        except Exception as e:
            self.logger.error(
                f"Attempting to run join_and_calculate_all_interactions(commits_interactions, issues_interactions) went wrong, with error {e}"
            )
            raise


if __name__ == "__main__":
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/pre-analysis_data_times_preps_logs.txt",
        in_notebook=False,
    )

    logger.info(
        "Running data timestamps pre-analysis preparation methods on processed- commits and issues files."
    )

    prepdatatimes = PrepDataTimes(in_notebook=False, logger=logger)

    times_data = prepdatatimes.interactions_data_workflow(
        read_location="data/",
        write_location="data/",
    )
