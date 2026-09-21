"""
Get per-repo-individual summary data (including RC: repository contribution %s)
info for commits, issues (and PRs), and review interactions data.

Write out this important info as: "merged-interactions-data-per-dev_xNrepos_xNrepoIndivds_YYYY-MM-DD.csv"

NOTE: THIS SCRIPT DOES >>not<< HANDLE ASSIGNMENT TO ISSUES.
This is partly because 'being assigned' is not an interaction of that
repo-individual, but instead (often) by someone else.

That is done in prep_issues.py, and fed into analyse_data.py via prep_combine.py.
"""

import argparse
import traceback
from logging import Logger
from pathlib import Path
import datetime
import sys
import csv
from ast import literal_eval
import pandas as pd
import pandas.api.types as ptypes
from githubanalysis.setup_classes import LocationSetup
import utilities.get_default_logger as loggit
from utilities.simple_read_repos_from_file import Repo_Reader
from utilities.glob_making_matching import Globber

pd.options.mode.copy_on_write = True


class PrepDataTimes(LocationSetup):
    def _log_name(self) -> str:
        return "prep_timestamps"

    def __init__(
        self,
        in_notebook: bool,
        logger: None | Logger = None,
    ) -> None:
        super().__init__(in_notebook, logger)
        self.globber = Globber(in_notebook=self.in_notebook, logger=self.logger)

    pd.options.mode.copy_on_write = True

    # def get_discussions_interactions(self, discussions_interactions_file:Path) -> pd.DataFrame:
    #     pass # TODO: write this for discussions_interactions

    def get_reviews_interactions(
        self,
        reviews_interactions: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        This function takes the reviews_interactions df
        (stacked per-interaction review data, NOT a per-repo-individual summary of review interactions)
        and:
         - adds "contribution" column (sets each value to "review")
         - adds "interaction type" column (sets each value to "code_reviewed")
         - creates additional column "datetime_day" which allows for 'unique interaction days' calculation subsequently
        Returns the processed df with columns:
        [ repo_name, gh_username, datetime_day, contribution, interaction_type ]
        """
        self.logger.info(
            f"Generated collated df of {len(reviews_interactions)} reviews interactions."
        )
        # rename columns and drop irrelevants to match formats in commits_interactions and issues_interactions
        reviews_interactions = reviews_interactions.rename(
            columns={
                "review_author_gh_username": "gh_username",
                "author_review_date": "datetime",
            },
            inplace=False,
            errors="raise",
        )

        # split subsequent_author_review_date as new interaction?
        self.logger.info(
            f"There are {reviews_interactions.subsequent_author_review_date.isna().sum()} empty fields for subsequent_author_review_date."
        )  # for Set1 this is ~800K
        self.logger.info(
            f"There are {reviews_interactions.subsequent_author_review_date.notna().sum()} NON-empty fields for subsequent_author_review_date."
        )  # for Set1 this is ~1.7M
        # TODO: this is a LOT of subsequent interactions which could be pulled out as a separate interaction event
        self.logger.debug(reviews_interactions.columns)

        # remove unwanted columns:
        reviews_interactions = reviews_interactions[
            [
                "repo_name",
                "gh_username",
                "datetime",
                "subsequent_author_review_date",  # re-allow this if pulling subsequent reviews into their own interactions
                # "review_author_gh_id",  # ideally would want to keep this in and handle gh_id instead of gh_username but no time to implement that
                "review_state",  # re-allow if pulling this as a type of review interaction
            ]
        ]

        # add column: contribution
        reviews_interactions.loc[:, "contribution"] = "review"
        # add column: "interaction_type"
        reviews_interactions.loc[:, "interaction_type"] = "code_reviewed"

        # pull out only date (YYYY-MM-DD) info to allow 'unique DAYs' to be obtained
        reviews_interactions.loc[:, "datetime_day"] = (
            reviews_interactions.datetime.apply(lambda x: pd.Timestamp(x).date())
        )

        # TODO ? write this reviews_interactions df out to .csv in this interactions format?

        reviews_interactions = reviews_interactions[  # keep only these cols:
            [
                "repo_name",
                "gh_username",
                "datetime_day",
                "contribution",
                "interaction_type",
            ]
        ]
        self.logger.info(
            f"Returning processed reviews_interactions df of shape: {reviews_interactions.shape}"
        )
        return reviews_interactions

    def get_commit_interactions(self, commitsdf: pd.DataFrame) -> pd.DataFrame:
        """
        This function takes the commitsdf df
        (stacked per-interaction commits data, NOT a per-repo-individual summary of commits)
        and:
         - adds "contribution" column (sets each value to "commit")
         - adds "interaction type" column (sets each value to "commit_created")
         - creates additional column "datetime_day" which allows for 'unique interaction days' calculation subsequently
        Returns the processed df with columns:
        [ repo_name, gh_username, datetime_day, contribution, interaction_type ]
        """
        pd.options.mode.copy_on_write = True
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

        interactions_df_commits = interactions_df_commits[  # keep only these cols:
            [
                "repo_name",
                "gh_username",
                "datetime_day",
                "contribution",
                "interaction_type",
            ]
        ]

        return interactions_df_commits

    def get_issues_PRs_interactions(self, rawissuesdf: pd.DataFrame) -> pd.DataFrame:
        """
        Processes ISSUE OR PR data!
        Take multi-repo interaction-per-line processed_issues data df;
        pulls in timestamp data for each issue and pull request;

        Transforms and reshapes dataset;
         - gathers data on whether issue interaction is 'creation' (opening) or 'closure' (closed)
         - adds "contribution" column (sets each value to "issue" OR "pull request")
         - adds "interaction type" column (sets each value to "issue_created" or "issue_closed" or "pull_request_created" or "pull_request_closed")
         - creates additional column "datetime_day" which allows for 'unique interaction days' calculation subsequently

        Returns the processed df with columns:
        [ repo_name, gh_username, datetime_day, contribution, interaction_type ]

        """
        pd.options.mode.copy_on_write = True

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
            lambda row: (
                row["closer"]
                if pd.notna(row["closer"]) and row["interaction"] == "closed_at"
                else row["gh_username"]
            ),
            axis=1,
        )

        # drop non-required columns
        interactions_df_issues = issuesdf[
            [
                "repo_name",
                "gh_username",
                "datetime_day",
                "contribution",
                "interaction_type",
            ]
        ]

        return interactions_df_issues

    def join_all_interactions(
        self,
        commits_interactions: pd.DataFrame,
        issues_interactions: pd.DataFrame,
        reviews_interactions: pd.DataFrame,
        # discussions_interactions: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Function combines issues (+ PRs) and commits and reviews
        interactions and abridged timestamp data; returns df of this.

        Returned df is interaction-per-line with many lines per repo-individual and includes multiple repos.

        Returned df has columns:
        ['repo_name', 'gh_username', 'datetime_day', 'contribution', 'interaction_type']
        """
        pd.options.mode.copy_on_write = True

        self.logger.debug(issues_interactions.info())
        self.logger.debug(commits_interactions.info())
        self.logger.debug(reviews_interactions.info())
        # self.logger.debug(discussions_interactions.info())

        self.logger.debug(issues_interactions.columns)
        self.logger.debug(commits_interactions.columns)
        self.logger.debug(reviews_interactions.columns)
        # self.logger.debug(discussions_interactions.columns)

        # assert "datetime_day" in discussions_interactions.columns, (
        #     "The datetime_day column is missing from discussions_interactions df; please fix, rename and retry"
        # )  # in case I forget to address this earlier.

        filestr_iss = f"issues_interactions_x{len(issues_interactions)}interactions_x{issues_interactions.groupby(by=['repo_name']).ngroups}repos_x{issues_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{self.current_date_info}.csv"
        writeout_path_iss = Path(self.data_location, filestr_iss)
        issues_interactions.to_csv(writeout_path_iss, header=True, index=False)

        filestr_cmt = f"commits_interactions_x{len(commits_interactions)}interactions_x{commits_interactions.groupby(by=['repo_name']).ngroups}repos_x{commits_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{self.current_date_info}.csv"
        writeout_path_cmt = Path(self.data_location, filestr_cmt)
        commits_interactions.to_csv(writeout_path_cmt, header=True, index=False)

        filestr_rvw = f"review_interactions_x{len(reviews_interactions)}interactions_x{reviews_interactions.groupby(by=['repo_name']).ngroups}repos_x{reviews_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{self.current_date_info}.csv"
        writeout_path_rvw = Path(self.data_location, filestr_rvw)
        reviews_interactions.to_csv(writeout_path_rvw, header=True, index=False)

        # filestr_dsc = f"discussions_interactions_x{len(discussions_interactions)}interactions_x{discussions_interactions.groupby(by=['repo_name']).ngroups}repos_x{reviews_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{self.current_date_info}.csv"
        # writeout_path_dsc = Path(self.data_location, filestr_dsc)
        # discussions_interactions.to_csv(writeout_path_dsc, header=True, index=False)

        self.logger.debug(
            f"wrote out commits, issues and reviews interactions dfs to separate csv files: {writeout_path_cmt} and {writeout_path_iss} and {writeout_path_rvw}."
        )  # TODO: add discussion to this when implementing

        # JOIN ISSUES AND COMMITS AND REVIEWS DATA TOGETHER HERE:
        self.logger.info("Attempting THE JOIN: issues + commits + reviews...")
        try:
            all_types_interactions = pd.concat(
                # CONCAT rather than merge, because the columns match exactly, and we're aiming for a LONG df of stacked interactions
                objs=[issues_interactions, commits_interactions, reviews_interactions],
                join="outer",  # outer join returns ALL rows, matching where possible, applying NaNs if not; KEEPS non-shared columns (V. IMP!)
            )
            writeout_path_tmp = Path(
                self.data_location,
                f"tmp_interactions_merge_{self.current_date_info}.csv",
            )
            all_types_interactions.to_csv(writeout_path_tmp, header=True, index=False)
            self.logger.info(
                f"Intermediate output of JOIN written out to {writeout_path_tmp}"
            )
        except Exception as e:
            self.logger.error(
                f"Problem running data analysis workflow: {e}; arguments were: {args}."
            )
            self.logger.error(
                f"Unexpected error with THE JOIN (issues + commits + reviews) via concat(), traceback:\n{traceback.format_exc()}"
            )
            raise

        self.logger.info("Attempting join: issues + commits + reviews...")

        self.logger.debug(
            "joined issues and commits and reviews interactions"
        )  # TODO: add discussions df to this when implementing
        return all_types_interactions

    def calculate_all_interactions(
        self, all_types_interactions: pd.DataFrame
    ) -> pd.DataFrame:
        """
        MAIN INTERACTIONS CALCULATION AND SUMMARISING FUNCTION!

        This takes df of 'stacked' interactions data: all_types_interactions
        (interaction-per-line, multi lines per repo-individuial, multi repos)

        then:
         - drops rows with missing data (e.g. where gh_username value is missing as cannot calculate with missing repo-individuals ; missing repo_name; missing datetime_day' etc)
         - debugging / logging checks and reporting of Ns of rows deducted for missing data, date data types, etc
         - pre-calculation write-out as: combined_interactions_data_x....csv
         - create 'status_df': line-per-repo-individual summary df to hold calc'd data
         and in status_df:
         - calculation FOR EACH REPO-INDIVIDUAL: difference between earliest interaction date and latest interaction date in dataset; add to status_df as 'interaction_period_days'
         - calculation of number (count) of interactions PER INTERACTION TYPE PER REPO-INDIVIDUAL (e.g. commits 5, issue_creation 4, code_reviewed 2, etc); added to status_df
         - calculation of "interaction_days" (unique different days of interactions contributed of all sorts) PER REPO-INDIVIDUAL, added to status_df;
         - set any non-filled values in status_df to 0 as no interactions of those types were recorded
         - calculates net (raw N, and %) difference in issues (e.g. N created minus N closed and pc(%) created minus % closed)
         - (same as net difference in issues, but for pull requests)
         - calc total N of interactions of all sorts as "sum_n_interactions"
         - calc average N of interactions per interaction day as "mean_n_interactions_per_interaction_day" (= sum_N_interactions / N of interaction days)
         - generate "which_interactions": join strings of interaction_type together for all present interactions by repo_individual
         - calc "breadth_interactions" (Unique Interaction Types; N of different interaction types present for repo-individual)
         - calcs repo-individual's RC (% Repository Contribution) values for each CONTRIBUTION TYPE:
             - PR creation ("pc_pull_request_created")
             - PR closure ("pc_pull_request_closed")
             - commit creation ("pc_commit_created")
             - issue creation ("pc_issue_created")
             - issue closure ("pc_issue_closed")
             - reviews created ("pc_reviews_created")
            TODO: ??? ASSIGNMENT SHOULD GO HERE!!! ???
         - calcs repo-individual's RC (% Repository Contribution) of META INFO:
             - total number of interactions of ALL TYPES as "pc_sum_n_interactions"
             - calcs RC of all repository's unique interaction days as "pc_interaction_days"

        THEN returns status_df: a line-per-repo-individual summary df
        of each repo-individuals' contributions of all types!

        status_df has columns:
        [
            "repo_name",
            "gh_username",
            "code_reviewed",
            "commit_created",
            "issue_closed",
            "issue_created",
            "pull_request_closed",
            "pull_request_created",
            "interaction_days",
            "interaction_period_days",
            "created-closed_issues",
            "pc_created-closed_issues",
            "sum_n_interactions",
            "mean_n_interactions_per_interaction_day",
            "which_interactions",
            "breadth_interactions",
            "pc_pull_request_created",
            "pc_pull_request_closed",
            "pc_commit_created",
            "pc_issue_created",
            "pc_issue_closed",
            "pc_reviews_created",
            "pc_sum_n_interactions",
            "pc_interaction_days",
        ]
        """
        # # remove rows where gh_username is NaN/NA
        all_types_interactions = all_types_interactions.dropna(
            subset="gh_username", axis=0
        )
        self.logger.debug("removed missing GH_username rows")

        self.logger.debug(
            all_types_interactions.groupby(["repo_name", "gh_username"])["datetime_day"]
        )

        self.logger.debug(
            type(
                all_types_interactions.groupby(["repo_name", "gh_username"])[
                    "datetime_day"
                ]
            )
        )
        # Gather MISSING data counts:
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

        # reasonably important writeout: combined issues + commits + reviews with missing data handled.
        writeout_combined = Path(
            self.data_location,
            f"combined_interactions_data_x{all_types_interactions.groupby('repo_name').ngroups}repos_x{all_types_interactions.groupby(['repo_name', 'gh_username']).ngroups}repo-indivds_{self.current_date_info}.csv",
        )
        self.logger.info(f"Writing out combined interactions as: {writeout_combined}.")
        all_types_interactions.to_csv(
            writeout_combined,
            header=True,
            index=False,
        )
        self.logger.debug(f"wrote out combined interactions file {writeout_combined}.")
        self.logger.info(
            "Now attempting calculation of timediffs to help calculate interaction_period."
        )
        try:
            all_types_interactions["datetime_day"] = pd.to_datetime(
                all_types_interactions["datetime_day"],
                # utc = False: this is the default, "inputs will not be coerced to UTC. Timezone-naive inputs will remain naive, while timezone-aware ones will keep their time offsets." Think this is best because we only have DAY not times as well
            )

            assert ptypes.is_datetime64_any_dtype(
                all_types_interactions["datetime_day"]
            ), "The column datetime_day is NOT a date type! This is BAD"

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
                f"Unexpected error during TIMEDIFF calculations, ({e}) traceback:\n{traceback.format_exc()}"
            )
            self.logger.error(
                f"error {e}: \n value_counts of types for datetime_day are: \n {all_types_interactions['datetime_day'].apply(lambda x: str(type(x))).value_counts(dropna=False)} \n"
            )
            self.logger.error(f"tmp_errors is: {tmp_errors}")
            tmp_errors.to_csv(
                Path(
                    self.data_location,
                    f"error_rows_interactions_data_{self.current_date_info}.csv",
                )
            )

            raise

        self.logger.debug(
            "completed timediff calculation: datetime_day max - datetime_day min by groups"
        )
        timediff = timediff.apply(
            lambda x: x + datetime.timedelta(days=1)
        )  # add 1 day so the time difference is inclusive of both first and last days (ie no zeroes!)
        timediff = timediff.apply(lambda x: x.days).reset_index()
        timediff = timediff.rename(columns={"datetime_day": "interaction_period_days"})
        self.logger.debug("rename timediff column as interaction_period_days")

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

        # to avoid unexpected behaviour, pre-drop rows where keys are null value:
        self.logger.info(
            f"Shape BEFORE dropping rows with missing values for repo_name or gh_username from status_df: {status_df.shape}"
        )
        status_df = status_df.dropna(subset=["repo_name", "gh_username"])
        self.logger.info(
            f"Shape AFTER dropping rows with missing values for repo_name or gh_username from status_df: {status_df.shape}"
        )

        self.logger.info(
            f"Shape BEFORE dropping rows with missing values for repo_name or gh_username from timediff: {timediff.shape}"
        )
        timediff = timediff.dropna(subset=["repo_name", "gh_username"])
        self.logger.info(
            f"Shape AFTER dropping rows with missing values for repo_name or gh_username from timediff: {timediff.shape}"
        )

        # join on 'interaction_period_days' column from timediff
        self.logger.info(
            f"INNER join status_df and timediff on repo-individuals to obtain 'interaction_period_days' column from timediff; shape of status_df:{status_df.shape} shape of timediff: {timediff.shape}."
        )
        assert len(status_df) == len(timediff), (
            f"ERROR: lengths of statusdf and timediff are DIFFERENT, but this is not what we'd expect! status_df: {len(status_df)}, timediff: {len(timediff)}"
        )
        status_df = pd.merge(
            status_df,
            timediff,
            how="inner",  # JOIN TYPE: INNER: we assert both dfs are the same length so keys should match precisely.
            on=["repo_name", "gh_username"],
        )
        self.logger.info(f"AFTER joining timediff and status_df: {status_df.shape}.")

        for col in [
            "commit_created",
            "issue_closed",
            "issue_created",
            "pull_request_created",
            "pull_request_closed",
            "code_reviewed",
            # "discussion_added",
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
            + status_df["pull_request_closed"]
            + status_df["code_reviewed"]
            # + status_df["discussion_added"]
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

        status_df["pc_pull_request_closed"] = (
            status_df["pull_request_closed"]
            / status_df.groupby("repo_name")["pull_request_closed"].transform("sum")
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

        # RC (repo-contribution) of PR code reviews (PRCR):
        status_df["pc_reviews_created"] = (
            status_df["code_reviewed"]
            / status_df.groupby("repo_name")["code_reviewed"].transform("sum")
            * 100
        )

        # # RC (repo-contribution) of Issue Ticket Discussions (ITD):
        # status_df["pc_discussions"] = (
        #     status_df["discussion_added"]
        #     / status_df.groupby("repo_name")["discussion_added"].transform("sum")
        #     * 100
        # )

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

        self.logger.info(
            f"status_df being returned by calculate_all_interactions() has shape {status_df.shape} and columns: {status_df.columns}"
        )
        self.logger.info(
            f"status_df has {status_df.groupby(by=['repo_name', 'gh_username']).ngroups} repo-individuals from {status_df.groupby(by=['repo_name']).ngroups} repos."
        )
        return status_df

    def read_interactions(
        self, interactions_file: Path, repo_list: list[str]
    ) -> pd.DataFrame:
        """
        READS in .csv file of interactions of specific type (commits | issues (inc PRs) | code reviews)
        then SUBSETS these to discard any rows from repos NOT in the repo_list;
        returns the remaining in-list repos' interactions data of this type.
        """
        # READ IN DATA as df
        self.logger.info(
            f"Attempting to read in: {interactions_file}; this could take some SECONDS if it's a large file"
        )
        try:
            interactions_df = pd.read_csv(
                filepath_or_buffer=interactions_file,
                header=0,
                low_memory=False,
                dtype=object,
            )
            assert not interactions_df.empty, (
                "Read-in interactions df is empty but should not be."
            )
            assert interactions_df is not None, (
                "interactions_df is None, this is bad. Check the file {interactions_file}"
            )
            self.logger.debug(
                f"Columns for interactions_df are: {interactions_df.columns}"
            )
        except:
            self.logger.error(
                f"Problem loading in interactions from file {interactions_file}"
            )
            raise RuntimeError(
                f"interactions read in not working somehow for: {interactions_file}"
            )

        # subset df from file into the following repos' data only:
        # repo_name column value in repo_list e.g. df[df['A'].isin([3, 6])]
        self.logger.info(
            f"Length of interactions_df BEFORE subsetting to only repos in repo_list is: {len(interactions_df)}"
        )
        self.logger.info(
            f"Number of unique repos in interactions_df BEFORE subsetting is: {interactions_df.repo_name.nunique()}"
        )
        interactions_df = interactions_df[  # SUBSET DF TO ONLY THOSE ROWS WHERE REPO_NAME IN REPO_LIST
            interactions_df["repo_name"].isin(repo_list)
        ]
        self.logger.info(
            f"Length of interactions_df AFTER subsetting is: {len(interactions_df)}"
        )
        self.logger.info(
            f"Number of unique repos in interactions_df AFTER subsetting is: {interactions_df.repo_name.nunique()}"
        )
        return interactions_df

    def interactions_data_workflow(
        self,
        repo_list: list[str],
        issues_interactions_file: Path,
        commits_interactions_file: Path,
        reviews_interactions_file: Path,
        # discussions_interactions_file: Path | str,
    ) -> pd.DataFrame | None:
        """
        Reads in processed data via read_interactions() from commits,
        issue tickets and pull request code review interactions-per-line
        files created in *_workflow.py scripts, gathers timestamp information
        and processes it, then combines all into single dataframe for analysis.

        Processing done includes:
         - READ each file (commits, issue tickets, PR Code Reviews, ... ) in read_interactions()
         - JOIN dfs via concat 'outer' to create TALL df in join_all_interactions()
         - fill any missing data with 0s as interactions NOT present
         - write out joined (vertically stacked) data df as file "merged-interactions-data-per-dev... .csv"
         - log various stats

        Return `all_interactions_data`:
        a df of line-per-interactions data for multiple repo-individuals
        across multiple repos, with ALL included interaction types in single df.
        """
        pd.options.mode.copy_on_write = True

        start_time = datetime.datetime.now()
        self.logger.info(f"processing {len(repo_list)} repos' worth of issues data")

        self.logger.info("attempting to read ISSUES data from file")
        # read issues data in from previously created file and subset to relevant repos:
        issues_interactions = self.read_interactions(
            interactions_file=issues_interactions_file, repo_list=repo_list
        )

        self.logger.info("attempting to read COMMITS data from file")
        # read commits data in from previously created file and subset to relevant repos:
        commits_interactions = self.read_interactions(
            interactions_file=commits_interactions_file, repo_list=repo_list
        )

        self.logger.info("attempting to read REVIEWS data from file")
        # read in and subset the large collated reviews data file to the specified repos only
        reviews_interactions = self.read_interactions(
            interactions_file=reviews_interactions_file, repo_list=repo_list
        )
        self.logger.info(
            "column name renames, sorting interaction types, pull datetime data from df"
        )
        # do column name renames, adding interaction types, pull out datetime info etc
        reviews_interactions = self.get_reviews_interactions(
            reviews_interactions=reviews_interactions
        )

        # # TODO: DISCUSSIONS INTERACTION HANDLING HERE:
        # self.logger.info("attempting to read DISCUSSIONS data from file")
        # discussions_interactions = self.get_discussions_interactions(discussions_interactions_file = discussions_interactions_file)

        assert not commits_interactions.empty, (
            "commits_interactions type is empty; something went wrong!"
        )
        assert not issues_interactions.empty, (
            "issues_interactions type is empty; something went wrong!"
        )
        assert not reviews_interactions.empty, (
            "reviews_interactions is empty, something went wrong!"
        )
        # assert not discussions_interactions.empty, (
        #     "discussions_interactions is empty, something went wrong!"
        # )
        self.logger.info("Attempting joins of interaction data...")
        try:
            all_interactions_data = self.join_all_interactions(
                commits_interactions,
                issues_interactions,
                reviews_interactions,
                # discussions_interactions,
            )
            self.logger.info(
                f"all_interactions_data df has shape {all_interactions_data.shape}"
            )
            # all_interactions_data will now have columns:
            # ['repo_name', 'gh_username', 'datetime_day', 'contribution', 'interaction_type']
            # interactions will now be:
        except Exception as e:
            self.logger.error(
                f"Unexpected error during JOINING of interactions {e}, traceback:\n{traceback.format_exc()}"
            )
            raise

        self.logger.info("Attempting calculations of interaction data...")
        try:
            all_interactions_data = self.calculate_all_interactions(
                all_types_interactions=all_interactions_data
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error during CALCULATIONS of interactions {e}, traceback:\n{traceback.format_exc()}"
            )
            raise

        # replace misisng data with zeroes:
        # this shows NO interactions if we don't have any entries for
        # that repo-individ from any of the API endpoints
        all_interactions_data.fillna(
            value=0, inplace=True
        )  # should this be done in calculate_all_interactions() instead??

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
        n_repo_indivds = int(
            all_interactions_data.groupby(["repo_name", "gh_username"]).ngroups
        )
        filestr = f"merged-interactions-data-per-dev_x{n_repos_all_interactions_data}repos_x{n_repo_indivds}repoIndivds_{self.current_date_info}.csv"
        writeout_path = Path(self.data_location, filestr)

        try:
            # WRITE OUT THIS SUPER IMPORTANT DATA TO FILE!
            all_interactions_data.to_csv(
                path_or_buf=writeout_path,
                index=False,
                header=True,
                na_rep="",
                mode="w",
                quoting=csv.QUOTE_ALL,  # for safety of data: forces everything to string shapes....
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
                f"Error in attempting to write output file to {writeout_path}; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
            )
            self.logger.error(f"Unexpected error, traceback:\n{traceback.format_exc()}")
            raise


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--filepath-for-repos-list",
    metavar="PATH",
    help="Path to file containing list of repo_names separated by newlines e.g. 'code_review_subset_2026-07-26_x17.txt' (Inside file: No commas! No quotes! Internal slash ok ie FlicAnderson/coding-smart)",
    type=str,
)
parser.add_argument(
    "-c",
    "--filepath-for-commits-interactions",
    metavar="PATH",
    help="Path to file containing Commit interactions e.g. data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv ",
    type=str,
)
parser.add_argument(
    "-i",
    "--filepath-for-issues-interactions",
    metavar="PATH",
    help="Path to file containing Issues (and PR) interactions e.g. data/issues_interactions_x3380102_2025-04-18.csv ",
    type=str,
)
parser.add_argument(
    "-r",
    "--filepath-for-reviews-interactions",
    metavar="PATH",
    help="Path to file containing PR Code Reviews interactions e.g. data/merged_reviews_data_all_types_x1284repos_x2593270reviews_x3810reviewfiles_2026-07-16.csv ",
    type=str,
)
# parser.add_argument(
#     "-d",
#     "--filepath-for-discussions-interactions",
#     metavar="PATH",
#     help="Path to file containing issue ticket Discussions interactions e.g. ",
#     type=str,
# )


if __name__ == "__main__":
    """
    This script will run at commandline with 4 flagged files as arguments. 

    Files for: commits interactions (-c), issues and pull request interactions (-i), and code review interactions (-r) 
    are READ and SUBSET against a file listing repositories to INCLUDE (-f), therefore any data rows for repos NOT included in file -f are excluded. 

    There are then calculations made generating summary information for the interactions contributed by each "repo-individual": 
    a repo-individual is the combined grouping of a unique repository name and a gh-username, and is used as the 'grouping index' for all calculations. 

    Calculations give details of interactions of each studied/included type made by each repo-individual. 

    These are returned as all_interactions_data df 
    (per-repo-individual contributions data as raw Ns and RC values of each interaction types, 
    NOT INCLUDING ASSIGNMENT TO ISSUES (yet))
    all_interactions_data is WRITTEN OUT as: "merged-interactions-data-per-dev_xNrepos_xNrepoIndivds_YYYY-MM-DD.csv"
    
    Example output for Set1: "data/merged-interactions-data-per-dev_x1284repos_x119492repoIndivds_2026-09-18.csv"

    """
    args = parser.parse_args()
    filepath: str | None = args.filepath_for_repos_list
    commits_interactions_file: str | Path = args.filepath_for_commits_interactions
    issues_interactions_file: str | Path = args.filepath_for_issues_interactions
    reviews_interactions_file: str | Path = args.filepath_for_reviews_interactions
    # discussions_interactions_file: Path = args.filepath_for_discussions_interactions

    """
    TEST REPOS: Run from commandline as this: 
    # NOTE: DO NOT RUN THIS LOCALLY!!!! (insufficient memory, will break your terminal.)
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f code_review_subset_2026-07-26_x17.txt 
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x1284repos_x2593270reviews_x3810reviewfiles_2026-07-16.csv
    """
    """
    SET1: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f sample_45pc_subsample_repo_names_list_2025-05-12_x1284.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x1284repos_x2593270reviews_x3810reviewfiles_2026-07-16.csv
    """
    """
    SET2: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f set2_sample_55pc_subsample_repo_names_list_2026-02-05_x1697.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x1697repos_x3288083reviews_x4768reviewfiles_2026-07-27.csv
    """
    """
    SET1 + SET2: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f study-sample-repo-names_2025-05-01_x2981.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r TODO: Not yet run.
    """

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/prep_timestamps_logs.txt",
        in_notebook=False,
    )

    logger.info(f"\n Proceeding to prep_timestamps.py with commandline inputs: {args}")

    assert filepath is not None, (
        "missing filepath for repo_names to process data for; this should be a .txt file such as 'data/code_review_subset_2025-05-30_x16.txt'. "
    )

    reporeader = Repo_Reader(
        in_notebook=False,
        logger=logger,
    )
    logger.info(f"reading repo names from file: {filepath}")
    repo_list = reporeader.get_repos(repo_list_file_name=filepath)

    logger.info(
        f"Running data timestamps pre-analysis preparation methods on processed- commits and issues files for {len(repo_list)} repositories' data."
    )

    prepdatatimes = PrepDataTimes(
        in_notebook=False,
        logger=logger,
    )

    issues_interactions_file = Path(issues_interactions_file)
    commits_interactions_file = Path(commits_interactions_file)
    reviews_interactions_file = Path(reviews_interactions_file)

    try:
        all_interactions_data = prepdatatimes.interactions_data_workflow(
            repo_list=repo_list,
            issues_interactions_file=issues_interactions_file,
            commits_interactions_file=commits_interactions_file,
            reviews_interactions_file=reviews_interactions_file,
            # discussions_interactions_file=discussions_interactions_file,
        )
    except Exception as e:
        logger.error(
            f"__main__ running interactions_data_workflow() on {filepath}: Encountered insurmountable error; error {e}"
        )
        logger.error(f"Unexpected error, traceback:\n{traceback.format_exc()}")
        sys.exit(1)
