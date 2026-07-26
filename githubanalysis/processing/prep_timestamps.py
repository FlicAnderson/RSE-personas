"""Get timestamp and interaction types info for issues AND commits datasets."""

import argparse
import traceback
from logging import Logger
from pathlib import Path
import datetime
import sys
import os
import csv
import re
from ast import literal_eval
import pandas as pd
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
        Function to read processed_commits data file for 1 repo;
        pulls in timestamp data for each commit, labelling interaction type;
        transforms and reshapes dataset;
        returns df of commits including datetime_day, contribution, and
        interaction_type information.
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
        Take multi-repo processed_issues data df;
        pulls in timestamp data for each issue and pull request;
        transforms and reshapes dataset;
        returns df of issues including datetime_day, contribution, and
        interaction_type information.
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

    def join_and_calculate_all_interactions(
        self,
        commits_interactions: pd.DataFrame,
        issues_interactions: pd.DataFrame,
        reviews_interactions: pd.DataFrame,
        # discussions_interactions: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Function combines issues and commits interactions and timestamp data
        returns df of this, including various calculated values of interaction data.
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
        all_types_interactions = issues_interactions.merge(
            right=commits_interactions,
            how="outer",  # outer join returning ALL rows, matching where possible, applying NaNs if not
            left_on=["repo_name", "gh_username"],
            right_on=["repo_name", "gh_username"],
            indicator=False,
        )
        all_types_interactions = all_types_interactions.merge(
            right=reviews_interactions,
            how="outer",  # outer join returning ALL rows, matching where possible, applying NaNs if not
            left_on=["repo_name", "gh_username"],
            right_on=["repo_name", "gh_username"],
            indicator=False,
        )
        # TODO: add discussions df to this when implementing

        self.logger.debug(
            "joined issues and commits and reviews interactions"
        )  # TODO: add discussions df to this when implementing
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

        all_types_interactions.to_csv(
            Path(
                self.data_location,
                f"combined_interactions_data_x{all_types_interactions.groupby('repo_name').ngroups}repos_x{all_types_interactions.groupby(['repo_name', 'gh_username']).ngroups}repo-indivds_{self.current_date_info}.csv",
            ),
            header=True,
            index=False,
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
            self.logger.error(f"Unexpected error, traceback:\n{traceback.format_exc()}")
            self.logger.error(
                f"error {e}: value_counts of types for datetime_day are: {all_types_interactions['datetime_day'].apply(lambda x: str(type(x))).value_counts(dropna=False)}"
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
            f"status_df being returned by join_and_calculate_all_interactions() has shape {status_df.shape} and columns: {status_df.columns}"
        )
        return status_df

    def read_interactions(
        self, interactions_file: Path, repo_list: list[str]
    ) -> pd.DataFrame:
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
            f"Length of interactions_df BEFORE subsetting is: {len(interactions_df)}"
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
        Reads in processed data from commits and issue tickets
        gathers timestamp information and processes it, then combines all
        into single dataframe for analysis.
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

        try:
            all_interactions_data = self.join_and_calculate_all_interactions(
                commits_interactions,
                issues_interactions,
                reviews_interactions,
                # discussions_interactions,
            )
            self.logger.info(
                f"all_interactions_data df has shape {all_interactions_data.shape}"
            )

        except Exception as e:
            self.logger.error(
                f"Unexpected error {e}, traceback:\n{traceback.format_exc()}"
            )
            raise

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
        n_repo_indivds = int(
            all_interactions_data.groupby(["repo_name", "gh_username"]).ngroups
        )
        filestr = f"merged-interactions-data-per-dev_x{n_repos_all_interactions_data}repos_x{n_repo_indivds}_{self.current_date_info}.csv"
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
    args = parser.parse_args()
    filepath: str | None = args.filepath_for_repos_list
    commits_interactions_file: str | Path = args.filepath_for_commits_interactions
    issues_interactions_file: str | Path = args.filepath_for_issues_interactions
    reviews_interactions_file: str | Path = args.filepath_for_reviews_interactions
    # discussions_interactions_file: Path = args.filepath_for_discussions_interactions

    """
    Run from commandline as this: 
    $ python githubanalysis/processing/prep_timestamps.py 
    -f code_review_subset_2026-07-26_x17.txt 
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x1284repos_x2593270reviews_x3810reviewfiles_2026-07-16.csv
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
        times_data = prepdatatimes.interactions_data_workflow(
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
