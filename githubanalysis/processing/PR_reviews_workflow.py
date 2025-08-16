"""Workflow for running commits processing and analysis code for 1 repo."""

import logging
import pandas as pd
from pathlib import Path
import re
import os


from githubanalysis.setup_classes import LocationSetup
import utilities.get_default_logger as loggit
from githubanalysis.processing.reformat_PR_reviews import ReviewsFormatter
# from githubanalysis.processing.get_all_PR_code_reviews import GetCodeReviews


class RunPRReviews(LocationSetup):
    # repo_name: str | None

    def _log_name(self) -> str:
        return "reviews_workflow_logs"

    def __init__(
        self,
        config_path: str,
        in_notebook: bool,
        logger: None | logging.Logger = None,
        out_filename: str = "processed-PR-reviews",
    ) -> None:
        super().__init__(in_notebook=in_notebook, logger=logger)
        self.config_path = config_path
        self.repo_name = None
        self.out_filename = out_filename

    # def run_get_reviews(self, ):
    ## this would use code from get_all_PR_code_reviews.py to run on certain list of repo_names, done in main.

    def process_format_PR_reviews(
        self,
        reviews_json_file: Path,
        writeout: bool = True,
        out_filename="processed-PR-reviews",
    ):
        """
        Process and format PR_reviews (ie output of
        get_all_PR_code_reviews() for a repo) into a dataframe.
        """
        self.logger.info(f"Processing PR reviews data from file {reviews_json_file}")
        reformat_PR_reviews = ReviewsFormatter(
            in_notebook=self.in_notebook,
        )
        reformatted_PR_reviews = reformat_PR_reviews.reformat_PR_reviews_object(
            PR_reviews_json_file=reviews_json_file,
        )
        self.logger.info(
            f"did reformat PR_reviews, created df of shape {reformatted_PR_reviews.shape} for repo {reformat_PR_reviews.repo_name}."
        )

        self.repo_name = reformat_PR_reviews.repo_name

        if writeout:
            reformat_PR_reviews.save_formatted_PR_reviews(out_filename=out_filename)
            self.logger.info("saved out reformat PR_reviews")

        return reformat_PR_reviews.reformatted_PR_reviews

    def format_many_repo_PR_reviews(
        self,
    ):
        """
        Look in the initialised data location (default: data/) and
        pull out all files matching out_filename prefix (default: "processed-PR-reviews_"),
        then run process_format_PR_reviews() on them.
        """

        review_files = [
            f
            for f in os.listdir(self.data_location)
            if re.match(rf"({re.escape(self.out_filename)}).*(.csv)", f, re.IGNORECASE)
        ]  # this is a list comprehension, just split over 3 lines ^
        self.logger.info("{repolist}")

        print(
            f"Currently processing {len(review_files)} repos' worth of PR Reviews data"
        )

        reviews_data = pd.DataFrame()

        # JOIN THE DF CONTENT OF EACH REPO's PR REVIEWS INTO ONE MASSIVE DF

        for repofile in review_files:
            self.logger.info(f"Checking {repofile} for PR code reviews.")

            # for repofile in review_files:
            file = Path(self.data_location, repofile)
            if file.exists():
                self.logger.debug(f"Running on PR reviews file {file}.")
                # gather THIS repo's data
                reviews_data_next = self.process_format_PR_reviews(file)

                # join this data to overall dataset from many repos
                reviews_data = pd.concat([reviews_data, reviews_data_next])

                self.logger.info(f"Generated df of {len(reviews_data)} review data.")

                assert (
                    reviews_data is not None
                ), "reviews_data type is None; something went wrong!"

                filestr = f"merged_reviews_data_x{len(review_files)}-repos_{self.current_date_info}.csv"
                writeout_path = Path(self.data_location, filestr)

                try:
                    # WRITE OUT THIS SUPER IMPORTANT DATA TO FILE!
                    reviews_data.to_csv(
                        path_or_buf=writeout_path, header=True, index=False
                    )
                    self.logger.info(
                        f"Saved reviews_data df for {len(review_files)} repos with {len(reviews_data)} devs to file: {filestr}"
                    )

                    return reviews_data

                except Exception as e:
                    self.logger.error(
                        f"Error in attempting to write output file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
                    )
                    raise

            else:
                raise RuntimeError(
                    f"Error handling PR reviews data from file {file} via {repofile}."
                )


if __name__ == "__main__":
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/PR_reviews_workflow_logs.txt",
        in_notebook=False,
    )

    logger.info("Running PR review data formatting.")

    runprreviews = RunPRReviews(
        in_notebook=False,
        config_path="githubanalysis/config.cfg",
        logger=logger,
        out_filename="processed-PR-reviews",
    )

    try:
        runprreviews.format_many_repo_PR_reviews()
    except Exception as e:
        logger.error(
            f"Encountered review-formatting workflow-borking error trying to read and process PR reviews files; error {e}"
        )
        exit(1)
