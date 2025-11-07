"""Get issue ticket discussion data if present for repos; save out to files."""

import logging
import json
from typing import Any

# import argparse
from pathlib import Path
import pandas as pd

# from githubanalysis.processing.get_all_PR_code_reviews import (
#     simple_read_repos_from_file,
#     GetCodeReviews,
# )
from githubanalysis.processing.issues_workflow import RunIssues
from githubanalysis.processing.get_all_pages_issues import is_this_single_page
from githubanalysis.setup_classes import RESTRequestSetup
from utilities.check_gh_reponse import (
    raise_if_response_error,
    run_with_retries,
    RepoNotFoundError,
)


"""
Requires issue ticket numbers information, which may already have been gathered. 
- Search for relevant issue ticket data file 
  - load info if exists, 
  - if not exists then run issue ticket gathering for the repo with discussions included?  
- ?handle PR-ticket discussions separately through 'get_all_PR_code_reviews.py' (TODO) 
- handle non-PR-ticket discussions (written to file, not yet processed)
"""


class Discussions(
    RESTRequestSetup,
):
    def _log_name(self) -> str:
        return "split_issue_tickets_PRs"

    sanitised_repo_name: str
    repo_name: str

    def __init__(
        self,
        repo_name: str,
        config_path: str,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(config_path, in_notebook, logger)
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name

    def make_discussions_query_url(
        self,
        page: int | None,
        per_pg: int | str = 100,
    ):
        repos_api_url = "https://api.github.com/repos/"
        if page is None:
            return f"{repos_api_url}{self.repo_name}/issues/comments?per_page={per_pg}"  # ISSUES API BUT GIVES PR DISCUSSIONS TOO
        else:
            return f"{repos_api_url}{self.repo_name}/issues/comments?per_page={per_pg}&page={page}"

    def get_remaining_pgs(
        self,
        next_pg: str | None,
    ):
        # use pagination to get 'next page' url for query
        all_subsequent_pages_response = []
        while (
            next_pg is not None
        ):  # IMPORTANT: while loop runs until no next_pg url link.
            self.logger.info(f"getting json via request url {next_pg}.")
            # try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=next_pg, headers=self.headers),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            self.logger.debug(api_response)
            assert api_response is not None and api_response.status_code == 200, (
                f"api response isn't ok somehow, {api_response}"
            )

            # get next page of json content for sub-reviews for this main review
            all_subsequent_pages_response.extend(api_response.json())

            # next_pg is the iterator condition for the while loop handling pagination! Do not remove this unless refactoring completely!
            next_pg = api_response.links.get(
                "next", {}
            ).get(
                "url"
            )  # THIS IS IMPORTANT! This is a while loop which runs until next_pg is NONE.
        return all_subsequent_pages_response

    def get_all_pages(self, query) -> list[dict[str, Any]] | None:
        json_pgs = []  # create accumulator
        # run first request
        self.logger.debug(f"Running get_all_pages() FIRST PAGE for query: {query}")
        # run the query
        try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=query, headers=self.headers),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            self.logger.debug(
                f"FIRST PAGE API response {api_response} for query: {query}"
            )
        except RepoNotFoundError as e:
            self.logger.error(
                f"Encountered repo-getting-workflow-borking error in repo {self.repo_name}; Repo DOES NOT EXIST or is private: {e}"
            )
            return None  # skip this repo.

        json_pgs.extend(api_response.json())  # add first page to accumulator

        if not is_this_single_page(api_response.links):
            subsequent_pg_json = self.get_remaining_pgs(
                next_pg=api_response.links["next"]["url"]
            )  # get ALL subsequent pages and return accumulation of those
            json_pgs.extend(subsequent_pg_json)  # join all subsequent to first pg

        self.logger.info(f"There are {len(json_pgs)} items across all pages.")
        return json_pgs

    def get_issues_content(self) -> pd.DataFrame | None:
        """
        If processed-issues_{repo_name}_{current_date_info}*.csv exists...
          - use this file.
        If it doesn't exist:
          - need to run 'runissues = RunIssues(repo_name = repo_name, ...)' then 'runissues.run_all_issues()'
            via 'from githubanalysis.processing.issues_workflow import RunIssues' import
            to create the processed-issues_*.csv

        NOTE: Checks for processed-issues content with TODAY's DATE and loads that
        (date behaviour is determined by comparing against get_issues.current_date_info)

        TODO: improvement would be to use 'most recent' version.
        """

        print(f"Attempting to find issues content for repo: {self.repo_name}")

        runissues = RunIssues(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
        )

        return runissues.run_all_issues()

    def split_issues_by_PR_status(self):  #  -> pd.DataFrame, pd.DataFrame:
        # either access processed-issues file with today's date if exists,
        # OR get issues data for repo with API calls and return processed df
        processed_issues = self.get_issues_content()

        if processed_issues is None or processed_issues.empty:
            raise pd.errors.EmptyDataError(
                "Frame is None or pd.DataFrame is empty; perhaps no issues?"
            )
        assert isinstance(processed_issues, pd.DataFrame), (
            "WARNING: processed_issues is NOT in dataframe format after running get_issues_content(); check types for errors"
        )

        PR_issues = processed_issues[processed_issues["pull_request"].notna()]
        non_PR_issues = processed_issues[processed_issues["pull_request"].isna()]

        # sense-check:
        # set of PRs and non-PRs should not overlap (ie no intersection)
        # and PRs plus non-PRs should be same length as processed_issues
        assert len(
            set(PR_issues["issue_number"]).union(set(non_PR_issues["issue_number"]))
        ) == len(processed_issues)
        assert (
            len(
                set(PR_issues["issue_number"]).intersection(
                    set(non_PR_issues["issue_number"])
                )
            )
            == 0
        )

        return PR_issues, non_PR_issues

    def get_all_discussions(
        self,
        out_json_file: str = "all-discussions",
    ) -> (
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
        | None
    ):
        """
        Create query to obtain `issues/comments` GH API endpoint DISCUSSIONS items; HOWEVER!!!
        NOTE: this includes discussions ON PRs ALSO.
        Here, we use non_PR_issues df as source of issue ticket numbers to verify ISSUE comments against,
        and PR_issues as a source of PR numbers to verify PR comments against

        RETURNING: PATH object with location of file containing json format discussions content.
        """
        # make first page of query for discussions at repo
        discussions_qry = self.make_discussions_query_url(per_pg=100, page=None)

        if (
            discussions_json := self.get_all_pages(query=discussions_qry)
        ) is None:  # walrus operator: assigning things in an expression
            return

        out_filename = out_json_file
        filestr = (
            f"{out_filename}_{self.sanitised_repo_name}_{self.current_date_info}.json"
        )
        writeout_path = Path(self.data_location, filestr)

        with open(
            writeout_path, "w"
        ) as json_file:  # Write out discussion data json Now
            json.dump(discussions_json, json_file)

        # read json back in...
        # doing this gets it into a pandas format ...
        # WHY? (can't use json str directly into pandas.read_json() as it's deprecated since v2.1.0)
        # https://pandas.pydata.org/docs/reference/api/pandas.read_json.html
        # (maybe possible as it says path_or_buf can be "a valid JSON str",
        # but it says "Passing json literal strings is deprecated" so I'm avoiding this,
        # but I may have misinterpreted?)

        # get issues info:
        try:
            PR_issues, non_PR_issues = self.split_issues_by_PR_status()
        except pd.errors.EmptyDataError as e_empty:
            self.logger.error(
                f"Repo {self.repo_name} has no issues to query. {e_empty}"
            )
            return None  # skip empty repos too

        discussions_df = pd.read_json(writeout_path)
        self.logger.info(
            f"There are {len(discussions_df)} discussions for repo {self.repo_name}."
        )

        discussions_df["issue_id_number"] = discussions_df["issue_url"].apply(
            lambda x: int(x.rsplit("/", 1)[1])
        )
        discussions_df["discussion_author_gh_username"] = discussions_df["user"].map(
            lambda x: x.get("login", None)
        )

        non_PR_issue_discussions = discussions_df[
            discussions_df["issue_id_number"].isin(non_PR_issues["issue_number"])
        ]
        PR_issue_discussions = discussions_df[
            ~discussions_df["issue_id_number"].isin(non_PR_issues["issue_number"])
        ]  # the tilde is the inversion of the result!

        self.logger.info(
            f"There are {len(non_PR_issue_discussions)} non-PR type issue ticket discussions for repo {self.repo_name}."
        )
        self.logger.info(
            f"There are {len(PR_issue_discussions)} PR type issue ticket discussions for repo {self.repo_name}."
        )

        assert len(non_PR_issue_discussions) + len(PR_issue_discussions) == len(
            discussions_df
        )  # ensure they still match and nothing's dropped somehow

        # TODO: discussions reformatting would go here,
        # e.g. getting gh_username out.

        # write out all discussions to CSV this time (json prev)
        discussion_filestr = (
            f"{out_filename}_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        )
        discussion_writeout_path = Path(self.data_location, discussion_filestr)
        discussions_df.to_csv(
            path_or_buf=discussion_writeout_path,
            header=True,
            index=False,
        )

        # write out non_PR_issue_discussions csv
        non_PR_discussions_filest = f"non-PR-issue-discussions_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        PR_discussions_filestr = f"PR-issue-discussions_{self.sanitised_repo_name}_{self.current_date_info}.csv"

        npr_path = Path(self.data_location, non_PR_discussions_filest)
        pr_path = Path(self.data_location, PR_discussions_filestr)

        non_PR_issue_discussions.to_csv(  # These are ready to process and incorporate to data analysis
            path_or_buf=npr_path,
            header=True,
            index=False,
        )

        # write out PR_issue_discussions csv
        PR_issue_discussions.to_csv(
            path_or_buf=pr_path,
            header=True,
            index=False,
        )

        # pass on (return) PR_issues to do other PR CR????
        return (
            discussions_df,
            PR_issues,
            non_PR_issues,
            non_PR_issue_discussions,
            PR_issue_discussions,
        )  # ???
