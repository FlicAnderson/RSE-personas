"""Collate PR Code Review (PRCR) datafiles, generate dataframes ready for analysis and get timestamp and interaction types info for Pull Request Code Reviews (PRCR)."""

from pathlib import Path
import pandas as pd
import datetime
from githubanalysis.setup_classes import DatasetSetup

GH_API_AUTHOR_ASSOCIATION = [  # via https://docs.github.com/en/rest/issues/issue-dependencies?apiVersion=2022-11-28 Response Schema > "author_association"
    "COLLABORATOR",
    "CONTRIBUTOR",
    "FIRST_TIMER",
    "FIRST_TIME_CONTRIBUTOR",
    "MANNEQUIN",
    "MEMBER",
    "NONE",
    "OWNER",
]


class PrepDataPRReviews(DatasetSetup):
    def _log_name(self) -> str:
        return "prep_PR_reviews"

    def subset_by_dates(
        self,
        df: pd.DataFrame,
        datestamp_column=str,
        from_datestamp: datetime.datetime = datetime.datetime.min,  # default to earliest possible year - not sensible, but doesn't change behaviour :C
        to_datestamp: datetime.datetime = datetime.datetime.today(),  # defaults to today, which is the latest possible date, no behaviour changed.
    ):
        """
        There should be a function that subsets the reviews'
        interactions to between specific date/timestamps in a specific column
        to assist with future calculations and analysis.

        Assumes UTC timezone as this is the default GH timezone.
        """
        return df[
            (df[datestamp_column] > from_datestamp)
            & (df[datestamp_column] < to_datestamp)
        ]

    def calculate_RC_PRCR(self, reviews_df: pd.DataFrame) -> pd.DataFrame:
        """
        When given a dataframe of many repos' worth of PR CR (pull request code review)
        interactions all concatenated together, calculate what proportion of the
        total number of reviews present for a repo_name each repo-individual
        (unique repo_name + gh_username combo) is responsible for authoring.
        Return dataframe of per-repo-individual-data.
        """
        # isolate N of PR review interactions per repo via groupby:
        per_repo_info = (
            reviews_df.groupby(by=["repo_name"])
            .size()
            .reset_index(
                name="N_repo_reviews",
            )
        )
        # isolate repo-individuals' number of reviews:
        per_repo_individual_info = (
            reviews_df.groupby(by=["repo_name", "review_author_gh_username"])
            .size()
            .reset_index(
                name="N_reviews",
            )
        )

        # merge repo review-totals onto the per-repo-individuals' number of authored reviews, to create new df
        new_df = per_repo_individual_info.merge(per_repo_info).reset_index(drop=True)
        # calculate RC (repository contribution) of each repo-individual for PR CR (pull request code reviews)
        new_df["RC_PRCR"] = (new_df.N_reviews / new_df.N_repo_reviews) * 100
        return new_df

    def add_repo_association_info(self, reviews_df: pd.DataFrame) -> pd.DataFrame:
        """
        When passed reviews_df (many repos' worth of pull request code review
        interactions all concatenated together), pull out the repo_association information;
        return new ***per-repo-individual-df*** with new column "review_author_repo_association":
        a list of unique attached repo-associations that contributor has associated
        with their reviews for that repo.
        """
        self.logger.info(
            f"There are {reviews_df.review_author_repo_association.nunique()} review_author_repo_association values present in this dataset ({self.dataset_name})."
        )
        self.logger.info(
            f"The distribution of repo-individuals' repo-association types in this ({self.dataset_name}) is: \n {reviews_df.review_author_repo_association.value_counts(dropna=False)} \n {reviews_df.review_author_repo_association.value_counts(dropna=False, normalize=True)} \n"
        )
        return (
            reviews_df.groupby(["repo_name", "review_author_gh_username"])[
                "review_author_repo_association"
            ]
            .unique()
            .reset_index()
        )

    def calc_RC_PRCR_as_association_type(
        self, reviews_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        This function essentiallly pivots the data to calculate the raw N
        and percentage RC values of PR code review interactions (PRCRs)
        per repo-individual during each REPO-ASSOCIATION they held while
        contributing (contributing their reviews, not overall within the
        repos).
        This is hoped to provide a bit more detail to the data.

        After a bit of info, the GH API repsonse schema (apiVersion=2025-11-28)
        suggests that these are the possible options ("COLLABORATOR",
        "CONTRIBUTOR", "FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR", "MANNEQUIN",
        "MEMBER", "NONE", "OWNER")
        """
        self.logger.info(
            "attempting to calculate raw N and RC values of reviews for repo-individuals PER AUTHOR_ASSOCIATION type (e.g. MEMBER, OWNER, NONE etc)."
        )
        # isolate N of PR review interactions per repo via groupby:
        per_repo_info = (
            reviews_df.groupby(by=["repo_name"])
            .size()
            .reset_index(
                name="N_repo_reviews",
            )
        )

        # groupby repo-individuals AND their (potentially multiple) REPO-ASSOCIATIONs
        repo_individ_assoc = (
            reviews_df.groupby(
                [
                    "repo_name",
                    "review_author_gh_username",
                    "review_author_repo_association",
                ]
            )
            .size()
            .reset_index(
                name="N_reviews_per_assoc",
            )
        )
        # Then pull out the number of reviews PER repo-individual PER their repo-associations
        repo_individ_assoc = (
            repo_individ_assoc.set_index(
                keys=["repo_name", "review_author_gh_username"]
            )
            .pivot(
                columns="review_author_repo_association",
                values="N_reviews_per_assoc",
            )
            .add_prefix("N_reviews_as_")
            .reset_index(drop=False)
        )

        # merge repo review-totals onto the per-repo-individuals' per-repo-association number of authored reviews, to create new df
        assoc_df = repo_individ_assoc.merge(per_repo_info).reset_index(drop=True)

        # calculate RC (repository contribution) of each repo-individual for PR CRs across each REPO-AUTHOR-ASSOCIATION type
        assoc_df["RC_reviews_as_COLLABORATOR"] = (
            assoc_df.N_reviews_as_COLLABORATOR / assoc_df.N_repo_reviews
        ) * 100
        assoc_df["RC_reviews_as_CONTRIBUTOR"] = (
            assoc_df.N_reviews_as_CONTRIBUTOR / assoc_df.N_repo_reviews
        ) * 100
        assoc_df["RC_reviews_as_MEMBER"] = (
            assoc_df.N_reviews_as_MEMBER / assoc_df.N_repo_reviews
        ) * 100
        assoc_df["RC_reviews_as_NONE"] = (
            assoc_df.N_reviews_as_NONE / assoc_df.N_repo_reviews
        ) * 100
        assoc_df["RC_reviews_as_OWNER"] = (
            assoc_df.N_reviews_as_OWNER / assoc_df.N_repo_reviews
        ) * 100

        # try this calculation also for the other theoretical AUTHOR_ASSOCIATION types listed in the GH API docs
        # IF they exist in this data:
        if "N_reviews_as_FIRST_TIMER" in assoc_df.columns:
            assoc_df["RC_reviews_as_FIRST_TIMER"] = (
                assoc_df.N_reviews_as_FIRST_TIMER / assoc_df.N_repo_reviews
            ) * 100
        if "N_reviews_as_FIRST_TIME_CONTRIBUTOR" in assoc_df.columns:
            assoc_df["RC_reviews_as_FIRST_TIME_CONTRIBUTOR"] = (
                assoc_df.N_reviews_as_FIRST_TIME_CONTRIBUTOR / assoc_df.N_repo_reviews
            ) * 100
        if "N_reviews_as_MANNEQUIN" in assoc_df.columns:
            assoc_df["RC_reviews_as_MANNEQUIN"] = (
                assoc_df.N_reviews_as_MANNEQUIN / assoc_df.N_repo_reviews
            ) * 100
        self.logger.info(f"Returning assoc_df dataframe with shape: {assoc_df.shape}")
        return assoc_df

    def process_PRCRs(
        self,
        sample_reviews_file_to_process: Path,
        # subset_repos_file: Path, # ideally add this feature in subsequently
        out_file_name: str,
    ):
        """
        Pull in collated reviews for all repos as SINGLE file generated by PRCR Workflow (sample_reviews_file_to_process).
        Collate repo-individuals' PR code reviews data; Write out repo-individuals' reviews data to csv
        Return repo-individuals'(devs) reviews data in data-per-dev format.
        """

        # load the df:
        self.logger.info(
            f"Attempting to load file {sample_reviews_file_to_process}; this may take some seconds if the file is multiple gigabytes"
        )
        reviews_data_file = sample_reviews_file_to_process
        reviews_df = pd.read_csv(
            Path(reviews_data_file), header=0, low_memory=False, dtype=object
        )
        self.logger.info(f"reviews_df has shape {reviews_df.shape}")

        self.logger.info(
            f"There are {reviews_df.repo_name.nunique()} unique repo names in this PRCR / REVIEWS data set"
        )

        self.logger.info(
            f"There are {reviews_df.review_author_gh_username.nunique()} unique gh-usernames in this PRCR / REVIEWS data set"
        )  # 26146
        self.logger.info(
            f"There are {reviews_df.review_author_gh_id.nunique()} unique gh-username IDs in this PRCR / REVIEWS data set"
        )  # 27616

        self.logger.info(
            f"There are {len(reviews_df)} PR CR interactions in this PRCR / REVIEWS dataset"
        )
        self.logger.info(
            f"There are {reviews_df.review_type.nunique()} unique review types in this PRCR / REVIEWS data set"
        )  # 3
        self.logger.info(
            f"These {reviews_df.review_type.nunique()} unique review types are distrubuted like this: \n {reviews_df.review_type.value_counts(dropna=False)} \n {reviews_df.review_type.value_counts(dropna=False, normalize=True)} \n"
        )

        # calculate N of repo-individuals in the dataset:
        self.logger.info(
            f"There are {len(reviews_df.groupby(by=['repo_name', 'review_author_gh_username']).size())} repo-individuals in this dataset in total"
        )

        # create per-repo-individual(dev) df with RC PRCR!:
        per_repo_individual_data = self.calculate_RC_PRCR(reviews_df=reviews_df)
        # report stats on average RC_PRCR values across repos, in general, (and maybe by repo-association??)

        # add repo-association info:
        per_repo_individual_data = per_repo_individual_data.merge(
            self.add_repo_association_info(
                reviews_df=reviews_df
            )  # returns df of repo_name, username, and list of repo-associations for that contributor across their reviews
        )
        self.logger.info(
            f"There are {sum(per_repo_individual_data['review_author_repo_association'].apply(lambda x: len(x)) != 1)} repo-individuals with MORE THAN ONE REPO_ASSOCIATION listed"
        )

        # calculate RC PRCR BY REPO-ASSOCIATION!
        per_repo_individual_data_with_reviews_assocs = per_repo_individual_data.merge(
            self.calc_RC_PRCR_as_association_type(reviews_df=reviews_df)
        )

        return per_repo_individual_data_with_reviews_assocs
