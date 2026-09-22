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

# import pandas.api.types as ptypes
from githubanalysis.setup_classes import LocationSetup
import utilities.get_default_logger as loggit
from utilities.simple_read_repos_from_file import Repo_Reader
from utilities.glob_making_matching import Globber
import utilities.subset_by_date as subset_by_date
from githubanalysis.processing.summarise_interactions_per_repo_individual import (
    summarise_interactions_per_repo_individual,
)
from githubanalysis.processing.join_interactions_types_data import join_all_interactions
from githubanalysis.processing.read_interactions_files import read_interactions

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
        self.logger.debug(f"{reviews_interactions.columns = }")
        self.logger.info(
            f"NAs counted in review_author_gh_username col: {reviews_interactions['review_author_gh_username'].isna().sum()}"
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
        self.logger.debug(f"{reviews_interactions.columns = }")
        self.logger.info(
            f"NAs counted in gh_username col: {reviews_interactions['gh_username'].isna().sum()}"
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
            f"NAs counted in gh_username col: {reviews_interactions['gh_username'].isna().sum()}"
        )
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
        self.logger.info(
            f"NAs counted in author_username col: {interactions_df_commits['author_username'].isna().sum()}"
        )
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
        self.logger.info(
            f"NAs counted in gh_username col: {interactions_df_commits['gh_username'].isna().sum()}"
        )
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

        self.logger.info(
            f"NAs counted in issue_author_username col: {rawissuesdf['issue_author_username'].isna().sum()}"
        )
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
        self.logger.info(
            f"NAs counted in gh_username col: {issuesdf['gh_username'].isna().sum()}"
        )
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
        self.logger.info(
            f"NAs counted in gh_username col: {interactions_df_issues['gh_username'].isna().sum()}"
        )
        return interactions_df_issues

    def interactions_data_workflow(
        self,
        repo_list: list[str],
        issues_interactions_file: Path,
        commits_interactions_file: Path,
        reviews_interactions_file: Path,
        cutoff_date: pd.Timestamp,
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

        assert isinstance(cutoff_date, pd.Timestamp), (
            f"cutoff_date is not of correct timestamp type: {type(cutoff_date)}"
        )
        self.logger.info("Reading in INTERACTION-PER-ROW data now...")

        start_time = datetime.datetime.now()
        self.logger.info(f"processing {len(repo_list)} repos' worth of issues data")

        self.logger.info("attempting to read ISSUES data from file")
        # read issues data in from previously created file and subset to relevant repos:
        issues_interactions = read_interactions(
            interactions_file=issues_interactions_file,
            repo_list=repo_list,
            logger=self.logger,
        )

        self.logger.info(
            "THIS IS WHERE ISSUES INTERACTION PROCESSING SHOULD PROPERLY HAPPEN, BUT IT'S GENERIC??"
            # this code is assuming issues interaction processing was done previously in a different script, probably issues_workflow?
            # self.get_issues_PRs_interactions(rawissuesdf=issues_interactions)
        )

        assert "datetime_day" in issues_interactions.columns, (
            f"issues_interactions df from file {issues_interactions_file} is missing column 'datetime_day'; columns are: {issues_interactions.columns}."
        )
        self.logger.info(
            f"Subsetting ISSUES interactions to within research cutoff dates (earliest to {cutoff_date})."
        )
        issues_interactions = subset_by_date.subset_by_dates(
            df=issues_interactions,
            datestamp_column="datetime_day",
            # from_datestamp, not supplied, therefore 'earliest' used.
            to_datestamp=cutoff_date.date(),
            logger=self.logger,
        )

        self.logger.info("attempting to read COMMITS data from file")
        # read commits data in from previously created file and subset to relevant repos:
        commits_interactions = read_interactions(
            interactions_file=commits_interactions_file,
            repo_list=repo_list,
            logger=self.logger,
        )

        self.logger.info(
            "THIS IS WHERE COMMITS INTERACTION PROCESSING SHOULD PROPERLY HAPPEN, BUT IT'S GENERIC??"
        )

        assert "datetime_day" in commits_interactions.columns, (
            f"commits_interactions df from file {commits_interactions_file} is missing column 'datetime_day'; columns are: {commits_interactions.columns}."
        )
        self.logger.info(
            f"Subsetting COMMITS interactions to within research cutoff dates (earliest to {cutoff_date})."
        )
        commits_interactions = subset_by_date.subset_by_dates(
            df=commits_interactions,
            datestamp_column="datetime_day",
            # from_datestamp, not supplied, therefore 'earliest' used.
            to_datestamp=cutoff_date.date(),
            logger=self.logger,
        )

        self.logger.info("attempting to read REVIEWS data from file")
        # read in and subset the large collated reviews data file to the specified repos only
        reviews_interactions = read_interactions(
            interactions_file=reviews_interactions_file,
            repo_list=repo_list,
            logger=self.logger,
        )
        assert "author_review_date" in reviews_interactions.columns, (
            f"reviews_interactions df from file {reviews_interactions_file} is missing column 'author_review_date'; columns are: {reviews_interactions.columns}."
        )
        self.logger.info(
            f"Subsetting REVIEWS interactions to within research cutoff dates (earliest to {cutoff_date})."
        )
        reviews_interactions = subset_by_date.subset_by_dates(
            df=reviews_interactions,
            datestamp_column="author_review_date",
            # from_datestamp, not supplied, therefore 'earliest' used.
            to_datestamp=cutoff_date.date(),
            logger=self.logger,
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
        # assert "?????" in discussions_interactions.columns, (
        #     f"discussions_interactions df from file {discussions_interactions_file} is missing column '?????'; columns are: {discussions_interactions.columns}."
        # )
        # subset discussions to within specific research cutoff dates.
        # discussions_interactions = subset_by_date.subset_by_dates(
        #     df=discussions_interactions,
        #     datestamp_column="?????",
        #     # from_datestamp, not supplied, therefore 'earliest' used.
        #     to_datestamp=cutoff_date.date(),
        #     logger=self.logger,
        # )

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
            all_interactions_data = join_all_interactions(
                commits_interactions,
                issues_interactions,
                reviews_interactions,
                # discussions_interactions,
                logger=self.logger,
                current_date_info=self.current_date_info,
                data_location=self.data_location,
            )
            self.logger.info(
                f"all_interactions_data df has shape {all_interactions_data.shape}; df is **still** INTERACTION-PER-ROW FORMAT"
            )
            # all_interactions_data will now have columns:
            # ['repo_name', 'gh_username', 'datetime_day', 'contribution', 'interaction_type']
            # interactions will now be:
        except Exception as e:
            self.logger.error(
                f"Unexpected error during JOINING of interactions {e}, traceback:\n{traceback.format_exc()}"
            )
            raise

        self.logger.info(
            "\n Attempting calculations of joined interaction-per-row data; \n summarising to return ROW-PER-REPO-INDIVIDUAL format df... \n"
        )
        try:
            all_interactions_data = summarise_interactions_per_repo_individual(
                all_types_interactions=all_interactions_data,
                logger=self.logger,
                current_date_info=self.current_date_info,
                data_location=self.data_location,
            )
            self.logger.info(
                "!! `all_interactions_data` df is now in ROW-PER-REPO-INDIVIDUAL format !!"
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
        )  # should this be done in summarise_interactions_per_repo_individual() instead??

        self.logger.info(
            f"Dataset of combined interactions info contains {all_interactions_data.repo_name.nunique()} unique repo_names."
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
                f"Saved ROW-PER-REPO-INDIVIDUAL-FORMAT format all_interactions_data df for {n_repos_all_interactions_data} repos with {len(all_interactions_data)} devs to file: {filestr}"
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
    -r data/merged_reviews_data_all_types_x2981repos_x5881353reviews_x8578reviewfiles_2026-09-21.csv

    (45 sec to run)
    """
    """
    SET1: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f sample_45pc_subsample_repo_names_list_2025-05-12_x1284.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x2981repos_x5881353reviews_x8578reviewfiles_2026-09-21.csv
    
    (?? sec to run)
    """
    """
    SET2: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f set2_sample_55pc_subsample_repo_names_list_2026-02-05_x1697.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x2981repos_x5881353reviews_x8578reviewfiles_2026-09-21.csv

    (?? sec to run)
    """
    """
    SET1 + SET2: Run from commandline as this: 
    $ time python githubanalysis/processing/prep_timestamps.py 
    -f study-sample-repo-names_2025-05-01_x2981.txt
    -c data/commits-interactions_x5852853_x2403-repos_2025-05-10.csv 
    -i data/issues_interactions_x3380102_2025-04-18.csv 
    -r data/merged_reviews_data_all_types_x2981repos_x5881353reviews_x8578reviewfiles_2026-09-21.csv

    (?? sec to run)
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
        f"Running data timestamps pre-analysis preparation methods on commits, issues and reviews interactions files for {len(repo_list)} repositories' data."
    )

    prepdatatimes = PrepDataTimes(
        in_notebook=False,
        logger=logger,
    )

    issues_interactions_file = Path(issues_interactions_file)
    commits_interactions_file = Path(commits_interactions_file)
    reviews_interactions_file = Path(reviews_interactions_file)

    try:
        all_interactions_data = (
            prepdatatimes.interactions_data_workflow(  # <- start here :)
                repo_list=repo_list,
                issues_interactions_file=issues_interactions_file,
                commits_interactions_file=commits_interactions_file,
                reviews_interactions_file=reviews_interactions_file,
                # discussions_interactions_file=discussions_interactions_file,
                cutoff_date=pd.Timestamp(
                    "2024-11-21"
                ),  # HARDCODING THIS FOR REPLICATION
            )
        )
    except Exception as e:
        logger.error(
            f"__main__ running interactions_data_workflow() on {filepath}: Encountered insurmountable error; error {e}"
        )
        logger.error(f"Unexpected error, traceback:\n{traceback.format_exc()}")
        sys.exit(1)
