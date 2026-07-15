"""Reformat raw PR reviews json data from files into pd.DataFrames"""

import pandas as pd
import re
from pathlib import Path
import logging
from githubanalysis.setup_classes import LocationSetup
from ast import literal_eval


class ReviewsFormatter(LocationSetup):
    def _log_name(self) -> str:
        return "PR_reviews_reformatter_logs"

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(
            in_notebook=in_notebook,
            logger=logger,
        )
        self.reformatted_PR_reviews = None
        self.repo_name = None
        self.sanitised_repo_name = None

    # def reformat_PR_nums_object(self, ):
    ## THIS WOULD FORMAT THE PR NUMBERS DETAILS CONTENT JSON INTO PD.DF; TO DO LATER
    #     pass
    def reformat_PR_reviews_object(
        self, reviews_type: str, PR_reviews_file: Path
    ) -> pd.DataFrame | None:
        """
        Function reads in json file for reviews_types "sub" or "main" of
        one repo's PR reviews data and pulls out relevant data into pd.DF.
        Does NOT save out the DF.

        If reviews_type is "discussions", function instead handles the
        .csv files of PR-related 'discussions' (ie. technically 'issue comments'
        as they're via the /issues/comments GH API endpoint).

        If the file is empty, return none ASAP.

        NOTE:
        These issue comments (labelled "PR discussions" here) are treated
        as PR Code Review interactions within this codebase as they are
        visible on the PR thread within the GH UI, and comments engage
        with their specific PR.
        This project chooses to assign these as equivalent 'PR Code Review
        interactions' by following developers' intentions here rather than
        GH's arbitrary API schemas.
        """

        assert reviews_type in [
            "sub",
            "main",
            "discussions",
        ], (
            f"'reviews_type' must be one of 'sub' or 'main' or 'discussions' for correct handling but reviews_type is {reviews_type}"
        )

        df_needs_these_colums_main = [
            "repo_name",  # not currently present at read-in of json, added subsequently in this script.
            "PR_review_id",  # the main-review ID
            "reviewed_PR_number",  # PR number which the code review item relates to
            "review_PR_url",  # url for the PR this review item
            "review_item_url",  # url for this review item
            "review_author_gh_username",  # GH username for user who left this review interaction
            "review_author_gh_id",  # ID of the GH user who left this review interaction
            "review_author_repo_association",  # relationship of reviewer to the repo (e.g. OWNER, COLLABORATOR, MEMBER ...)
            "author_review_date",  # date review was created
            "review_state",  # one of: APPROVED / COMMENTED / CHANGES_REQUESTED
            "review_body",  # content of the main review interaction
            "commit_id",  # latest code commit / version commented on (I believe)
            "review_type",  # "main" or "sub" or "discussions": NOTE: this difference derived from how GH API handles interactions around code review of PRs; Flic treating as equivalent 'code review interactions' for analysis.
            "API_links",  # nested dictionary of links to related items (useful for tracing connections); keeping for safety but unlikely to use this as-is, could remove in future tbh
        ]
        df_needs_these_colums_sub = [
            "repo_name",  # not currently present at read-in of json, added subsequently in this script.
            "PR_review_id",  # NOTE: this is the SUB-REVIEW's ID, not the main review (see main_PR_review_id)
            "reviewed_PR_number",  # PR number which the code review item relates to
            "review_PR_url",  #  url for the PR this review item
            "review_item_url",  # url for this (sub)review item comment/item
            "review_author_gh_username",  # GH username for user who left this review interaction
            "review_author_gh_id",  # ID of the GH user who left this review interaction
            "review_author_repo_association",  # relationship of reviewer to the repo (e.g. OWNER, COLLABORATOR, MEMBER ...)
            # "review_state", # no 'state' for subreviews
            "review_body",  # content of this sub-review interaction
            "commit_id",  # latest code commit / version commented on (I believe)
            "main_PR_review_id",  # main PR CR this is a subreview to
            "author_review_date",  # using subreview created date, as there's no submitted_at for subreviews.
            "subsequent_author_review_date",  # subreview updated (? future feat: consider counting this as a separate review interaction, esp if some time has passed? ?)
            "reply_to_subreview_id",  # if this is a reply to a subreview, point to ID of it
            "review_type",  # "main" or "sub" or "discussions": NOTE: this difference derived from how GH API handles interactions around code review of PRs; Flic treating as equivalent 'code review interactions' for analysis.
            "API_links",  # nested dictionary of links to related items (useful for tracing connections); keeping for safety but unlikely to use this as-is, could remove in future tbh
        ]
        df_needs_these_columns_discussions = [
            "repo_name",  # not currently present at read-in of json, added subsequently in this script.
            "PR_review_id",  # the main-review ID
            "reviewed_PR_number",  # PR number which the code review item relates to
            "review_PR_url",  # url for the PR this review item
            "review_item_url",  # url for this discussion review item comment/item
            "review_author_gh_username",  # GH username for user who left this review interaction
            "review_author_gh_id",  # ID of the GH user who left this review interaction
            "review_author_repo_association",  # relationship of reviewer to the repo (e.g. OWNER, COLLABORATOR, MEMBER ...)
            "author_review_date",  # date review was created
            "subsequent_author_review_date",  # date review was last revised
            "review_type",  # "main" or "sub" or "discussions": NOTE: this difference derived from how GH API handles interactions around code review of PRs; Flic treating as equivalent 'code review interactions' for analysis.
            "review_state",  # one of: APPROVED / COMMENTED / CHANGES_REQUESTED
            "review_body",  # content of the main review interaction
            # "commit_id",  # latest code commit / version commented on # NOT IN DISCUSSIONS
        ]

        if reviews_type != "discussions":
            rough_df = pd.read_json(
                PR_reviews_file,
                dtype=object,  # type:ignore
            )  # load in JSON from the file
        else:  # it'll be discussions, so...
            rough_df = pd.read_csv(
                PR_reviews_file,
                header=0,
                low_memory=False,  # load from CSV file
                dtype=object,
            )
        if rough_df.empty:
            raise RuntimeError(f"File '{PR_reviews_file}' is empty of content")

        assert not rough_df.empty, (
            f"dataframe generated by loading file {PR_reviews_file} is empty..."
        )

        if reviews_type == "discussions":
            rough_df = rough_df.rename(
                columns={
                    "id": "PR_review_id",  # ID of this code review discussion item
                    "issue_id_number": "reviewed_PR_number",  # PR number the review relates to
                    "issue_url": "review_PR_url",  # PR url this review relates to
                    "html_url": "review_item_url",  # review item html url (as opp to API url)
                    "discussion_author_gh_username": "review_author_gh_username",  # GH username for user who left this review interaction
                    "author_association": "review_author_repo_association",  # relationship of reviewer to the repo (e.g. OWNER, COLLABORATOR, MEMBER ...)
                    "created_at": "author_review_date",
                    "updated_at": "subsequent_author_review_date",
                    "body": "review_body",  # content of the review discussion interaction
                    # review_author_gh_id ID of the GH user who left this review interaction # NOT IN DISCUSSIONS :c
                    # "commit_id",  # latest code commit / version commented on # NOT IN DISCUSSIONS
                },
                errors="raise",
                inplace=False,
            )
            rough_df["review_type"] = (
                "discussions"  # create column filled with text 'discussion'
            )
            # handle getting user ID number here
            rough_df["review_author_gh_id"] = rough_df.user.apply(
                lambda x: literal_eval(x)["id"]
            )

        elif reviews_type == "main":
            rough_df = rough_df.rename(
                columns={
                    "id": "PR_review_id",
                    "user": "review_author_gh_username",
                    "body": "review_body",
                    "state": "review_state",
                    "pull_request_url": "review_PR_url",
                    "author_association": "review_author_repo_association",
                    "submitted_at": "author_review_date",
                    "commit_id": "commit_id",
                    "_links": "API_links",
                    "html_url": "review_item_url",
                },
                errors="raise",
                inplace=False,
            )
            rough_df["review_type"] = "main"  # create column filled with text 'main'

        elif reviews_type == "sub":
            rough_df = rough_df.rename(
                columns={
                    "id": "PR_review_id",  # in this case, the ID is the sub-review ID
                    "user": "review_author_gh_username",
                    "body": "review_body",
                    "html_url": "review_item_url",
                    "pull_request_review_id": "main_PR_review_id",
                    "pull_request_url": "review_PR_url",
                    "author_association": "review_author_repo_association",
                    "created_at": "author_review_date",
                    "updated_at": "subsequent_author_review_date",
                    "in_reply_to_id": "reply_to_subreview_id",
                    "path": "file_reviewed",
                    "_links": "API_links",
                },
                errors="raise",
                inplace=False,
            )
            rough_df["review_type"] = (
                "subreview"  # create column filled with text 'subreview'
            )
        else:
            self.logger.error(
                "Encountered review-formatting function error trying to handle reviews_type for PR reviews file"
            )
            raise RuntimeError(
                f"Unknown reviews_type: {reviews_type}"
            )  # handle this error! oughtn't occur due to the assert at the start tho

        # add repo_name,
        rough_df["repo_name"] = rough_df.review_PR_url.map(
            lambda x: re.split(
                r"(\w+\/\w+)", x.replace("https://api.github.com/repos/", "")
            )[1]
        )
        self.repo_name = rough_df["repo_name"][0]
        self.sanitised_repo_name = self.repo_name.replace("/", "-")

        if reviews_type == "main" or reviews_type == "sub":
            #  reformat user column to pull out login, pull PR number off PR_url,
            rough_df["reviewed_PR_number"] = rough_df.review_PR_url.map(
                lambda x: x.rsplit("/", 1)[1]
            )
            rough_df["review_author_gh_id"] = rough_df.review_author_gh_username.map(
                lambda x: x.get(
                    "id", None
                )  # this needs to go above the username abbreviation to grab ID info before it's removed
            )
            rough_df["review_author_gh_username"] = (
                rough_df.review_author_gh_username.map(lambda x: x.get("login", None))
            )
        # discussions was handled differently above

        if reviews_type == "main":
            # match columns to df_needs_these_columns
            rough_df.drop(  # drop columns not in list method via: https://stackoverflow.com/a/56891565
                columns=[
                    col for col in rough_df if col not in df_needs_these_colums_main
                ],
                inplace=True,
            )
            assert len(set(df_needs_these_colums_main) & set(rough_df.columns)) == len(
                set(df_needs_these_colums_main)
            ), (
                f"Dataframe columns do not match expected list for PR reviews for {PR_reviews_file}; current columns: {rough_df.columns}; expected columns: {df_needs_these_colums_main}."
            )
        elif reviews_type == "sub":
            # # removes scientific notation of floats applied to this col due to NaNs aaro missing values...
            # rough_df["reply_to_subreview_id"] = (
            #     rough_df["reply_to_subreview_id"]
            #     .apply(
            #         "{:.0f}".format  # fix number displaying as scientific numbers
            #     )
            #     .replace(
            #         {
            #             str("nan"): ""
            #         }  # replace unwanted weird 'nan'-str with empty string
            #     )
            # )
            # drop columns not in list...
            rough_df.drop(  # drop columns not in list method via: https://stackoverflow.com/a/56891565
                columns=[
                    col for col in rough_df if col not in df_needs_these_colums_sub
                ],
                inplace=True,
            )
            # match columns to df_needs_these_columns
            assert len(set(df_needs_these_colums_sub) & set(rough_df.columns)) == len(
                set(df_needs_these_colums_sub)
            ), (
                f"Dataframe columns do not match expected list for PR reviews for {PR_reviews_file}; current columns: {rough_df.columns}; expected columns: {df_needs_these_colums_sub}."
            )
        elif reviews_type == "discussions":
            rough_df.drop(  # drop columns not in list method via: https://stackoverflow.com/a/56891565
                columns=[
                    col
                    for col in rough_df
                    if col not in df_needs_these_columns_discussions
                ],
                inplace=True,
            )
        else:
            self.logger.error(
                "Encountered review-formatting function error trying to handle reviews_type for PR reviews file"
            )
            raise RuntimeError(
                f"Unknown reviews_type: {reviews_type}"
            )  # handle this error! oughtn't occur due to the assert at the start tho
        self.reformatted_PR_reviews = rough_df  # save processed df to reformatted_PR_reviews in class for reuse elsewhere

        return self.reformatted_PR_reviews

    # def reformat_PR_reviews_from_file(self, PR_reviews_file: str):
    #     """
    #     Reformat raw PR review data from json file into pd.DataFrame appropes format.
    #     """

    #     with open(PR_reviews_file, "r") as raw_PR_reviews_file:
    #         raw_reviews = json.load(raw_PR_reviews_file)

    #     return self.reformat_PR_reviews_object(raw_reviews)

    def save_formatted_PR_reviews(
        self, reviews_type: str, out_filename="processed-PR-reviews"
    ):
        """
        Saves the reformatted PR reviews data !!stored in self.reformatted_PR_reviews`!!
        during running of reformat_PR_reviews_object() out to csv file.
        """
        assert reviews_type in ["sub", "main", "discussions"], (
            "'reviews_type' must be one of 'sub' or 'main' or 'discussions' for correct handling."
        )

        write_out = f"{self.data_location / out_filename}_{reviews_type}_{self.sanitised_repo_name}_{self.current_date_info}.csv"

        if self.reformatted_PR_reviews is not None:
            self.reformatted_PR_reviews.to_csv(
                path_or_buf=write_out, mode="w", index=False, header=True
            )
            self.logger.info(
                f"wrote out dataframe of {reviews_type} PR reviews to file {write_out} for repo {self.repo_name}"
            )
        else:
            raise RuntimeError(
                f"Error: Failed saving reformatted {reviews_type} PR Reviews data out to {write_out}. Run reformat_PR_reviews*() function."
            )
