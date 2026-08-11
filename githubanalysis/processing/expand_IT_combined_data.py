"""Combine the pre-existing 6 Interaction Types merged data per dev file with 2 New Interaction Types: PR Code Reviews (PRCR) and Issue Ticket Discussions (ITD)!"""

from logging import Logger
from pathlib import Path
import sys
import argparse
import pandas as pd
import utilities.get_default_logger as loggit
import utilities.subset_by_date as subsetter
from githubanalysis.setup_classes import LocationSetup


class ExpandData(LocationSetup):
    def _log_name(self) -> str:
        return "expand_IT_combined_data_logs"

    def __init__(self, in_notebook: bool, logger: None | Logger = None) -> None:
        super().__init__(in_notebook, logger)

    def combine_existing_reviews_discussions(
        self,
        existing_data: str,
        reviews_data: str,
        # discussions_data: str,
    ):
        # check files exist
        assert existing_data is not None, f"existing data file missing: {existing_data}"
        assert reviews_data is not None, f"reviews data file missing: {reviews_data}"
        # assert discussions_data is not None, f"discussions data file missing: {discussions_data}"

        # load csv files
        self.logger.info(f"loading existing data file {existing_data}")
        existing_df = pd.read_csv(
            filepath_or_buffer=Path(existing_data),
            header=0,
            low_memory=False,
            dtype=object,
        )
        self.logger.info(f"loading reviews data file {reviews_data}")
        reviews_df = pd.read_csv(
            filepath_or_buffer=Path(reviews_data),
            header=0,
            low_memory=False,
            dtype=object,
        )

        #     discussions_df = pd.read_csv(
        #         filepath_or_buffer=Path(discussions_data),
        #         header=0,
        #         low_memory=False,
        #         dtype=object,
        #     )

        # SUBSET REVIEWS_DF BY TIME TO REMOVE ANY DATA SINCE cutoff date.
        self.logger.info(
            f"length of reviews data BEFORE research data collection cutoff date (2025-04-23) is: {len(reviews_df)}"
        )

        reviews_df["review_date_only"] = pd.to_datetime(
            reviews_df.author_review_date
        )  # change type from string to datetime

        assert "review_date_only" in reviews_df.columns, (
            "missing column 'review_date_only', this will be needed in a sec"
        )
        try:
            reviews_df = subsetter.subset_by_dates(
                df=reviews_df,
                datestamp_column="review_date_only",
                to_datestamp="2025-04-23",  # date of 'first' GH API data collection.
            )
        except Exception as e:
            self.logger.error(
                f"Something awful has happened while attempting to subset the reviews data to match the latest collection date within the initial collection period: {e}"
            )
            raise
        self.logger.info(
            f"length of reviews data AFTER research data collection cutoff date (2025-04-23) is: {len(reviews_df)}"
        )

        if not existing_df.empty and not reviews_df.empty:
            # merge existing and reviews and discussions dfs
            # first merge on REVIEWS (PRCR)
            try:
                per_individual_data = pd.merge(
                    existing_df,
                    reviews_df,
                    how="outer",  # outer join to avoid losing any in y not in x; prep_combined uses outer join between commits and issues dfs.
                    left_on=["repo_name", "gh_username"],
                    right_on=[
                        "repo_name",
                        "review_author_gh_username",
                    ],  # reviews-data-specific fieldname
                    indicator="origin",
                )
            except Exception as e:
                self.logger.error(
                    f"ERROR encountered in first merge between existing data df (shape: {existing_df.shape}) loaded from {existing_data}, and reviews data df (shape: {reviews_df.shape}) loaded from {reviews_data}: {e}"
                )
                raise

            # # second merge on DISCUSSIONS (ITD)
            # complete_per_individual_data = pd.merge(
            #     per_individual_data,
            #     discussions_df,
            #     how="outer", # outer join to avoid losing any in y not in x; prep_combined uses outer join between commits and issues dfs.
            #     left_on=["repo_name", "gh_username"],
            #     right_on=[
            #         "repo_name",
            #         "discussions_author_gh_username",
            #     ],  ### TODO: Confirm this fieldname with the discussions data
            #     indicator="origin",
            # )

            # save out as one file
            self.logger.info(
                f"Attempting to write out merged EXISTING and REVIEWS data df with shape: {per_individual_data.shape}"
            )

            filestr = f"per-repo-individual-existing-and-reviews-data_x{per_individual_data.repo_name.nunique()}repos_x{per_individual_data.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{self.current_date_info}.csv"
            writeout_path = Path(self.data_location, filestr)

            try:
                per_individual_data.to_csv(
                    path_or_buf=writeout_path,
                    header=True,
                    index=False,
                )
            except Exception as e:
                self.logger.error(
                    f"Error in attempting to write combined data-per-dev file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
                )
                raise


parser = argparse.ArgumentParser()
parser.add_argument(
    "-e",
    "--existing-data-per-dev-file",
    metavar="EXISTING_DATA_PER_DEV_FILE",
    help="Path to .csv file containing commits data (line per repo-individual), eg 'merged-data-per-dev_x2868-repos_2025-05-10.csv'.",
    type=str,
)
parser.add_argument(
    "-r",
    "--reviews-data-per-dev-file",
    metavar="REVIEWS_DATA_PER_DEV_FILE",
    help="Path to .csv file containing reviews (PRCR) data (line per repo-individual), eg 'reviews-data-per-dev_xN-repos_2026-07-DD.csv'.",
    type=str,
)
# parser.add_argument(
#     "-d",
#     "--discussions-data-per-dev-file",
#     metavar="DISCUSSIONS_DATA_PER_DEV_FILE",
#     help="Path to .csv file containing discussions (ITD) data (line per repo-individual), eg 'discussions-data-per-dev_xN-repos_2026-07-DD.csv'.",
#     type=str,
# )

if __name__ == "__main__":
    args = parser.parse_args()
    existing_data: str = args.existing_data_per_dev_file
    reviews_data: str = args.reviews_data_per_dev_file
    # discussions_data: str = args.discussions_data_per_dev_file

    """
    Run this script from commandline to combine existing merged issues and commits data file with new reviews and discussions data, all organised in the per-dev (ie line per repo-individual) format. 

    """

    # set up a logger?
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/expand_IT_combined_data_logs.txt",
        in_notebook=False,
    )

    expanddata = ExpandData(
        in_notebook=False,
        logger=logger,
    )
    logger.info(
        f"attempting to combine pre-existing interaction-types data file {existing_data} and reviews data file {reviews_data}"
    )
    try:
        expanddata.combine_existing_reviews_discussions(
            existing_data=existing_data, reviews_data=reviews_data
        )
        logger.info(
            "Expanding existing merged data with reviews interactions to create new file COMPLETED."
        )
    except Exception as e:
        logger.error(
            f"Error during __main__ running combine_existing_reviews_discussions() on existing data ({existing_data}), reviews_data ({reviews_data})",
            # f", and discussions_data ({discussions_data})",
            f" : Encountered review-formatting workflow-borking error; error {e}",
        )
        sys.exit(1)
