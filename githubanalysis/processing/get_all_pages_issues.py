"""Get all data from all pages of issues for a GitHub repo."""

import os
import json
import traceback
import logging
from githubanalysis.setup_classes import RESTRequestSetup
from utilities.check_gh_reponse import (
    raise_if_response_error,
    run_with_retries,
    RepoNotFoundError,
)

REPOS_API_URL = "https://api.github.com/repos/"


class NoIssuesError(RuntimeError):
    pass


def make_url(
    repos_api_url: str,
    repo_name: str,
    state: str,
    pulls: bool,
    per_pg: int | str,
    page: int | str,
):
    return f"{repos_api_url}{repo_name}/issues?state={state}&pulls={pulls}&per_page={per_pg}&page={page}"


def is_this_single_page(issue_links: dict) -> bool:
    if issue_links == {}:
        return True
    next_val = issue_links.get("next")
    if next_val is None:
        return True
    rel = next_val.get("rel")
    if rel is None or not isinstance(rel, str):
        raise RuntimeError(f"No 'rel' key in {issue_links}")
    if rel == "next":
        return False
    else:
        raise RuntimeError(f"unexpected 'rel' value: {rel}")


class IssueGetter(RESTRequestSetup):
    def _log_name(self) -> str:
        return "get_all_pages_issues_logs"

    def __init__(
        self,
        repo_name: str,
        in_notebook: bool,
        config_path: str,
        logger: logging.Logger | None,
    ) -> None:
        super().__init__(
            config_path=config_path, in_notebook=in_notebook, logger=logger
        )
        self.sanitised_repo_name = repo_name.replace("/", "-")

    def check_repo_has_issues(self, repo_name: str) -> bool:
        repos_api_url = "https://api.github.com/repos/"
        check_issue_url = f"{repos_api_url}{repo_name}"
        try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=check_issue_url, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
        except RepoNotFoundError as e:
            print(
                f"Encountered error for repo {repo_name}; Repo DOES NOT EXIST or is private: {e}"
            )
            return False  # skip this repo.

        assert api_response.ok, f"API response is: {api_response}"

        self.logger.debug(f"API shows repo {repo_name} has issues_enabled.")

        json_response = api_response.json()
        assert isinstance(json_response, dict), (
            f"WARNING: result of api_response.json() in check_repo_has_issues() is NOT a dict as expected: type is {api_response.json()}."
        )

        if len(json_response) > 0:
            assert isinstance(json_response.get("has_issues"), bool)

            if json_response.get("has_issues"):
                return True  # this is what we're hoping for: has issues, and more than zero of them.
        else:
            self.logger.error(
                f"Repository {repo_name} does NOT have issues enabled OR there are NO issues created despite being enabled. Raising NoIssuesError."
            )
        raise NoIssuesError(
            f"Repository {repo_name} does NOT have issues enabled OR there are NO issues created despite being enabled."
        )

    def _page_issues_grabber(
        self,
        repos_api_url: str,
        repo_name: str,
    ) -> list[dict]:
        page = 1

        issues_url = make_url(
            repos_api_url=repos_api_url,
            repo_name=repo_name,
            state="all",  # alternatives: "open" (default) | "closed"
            pulls=True,
            per_pg=100,  # default is 30 on GH API
            page=page,
        )

        all_issues = []
        api_response = None

        while page < 50000:  # stupidly large number just in case we never escape
            self.logger.info(
                f">> Running issue grab for repo {repo_name}, in page {page}."
            )

            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=issues_url, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )

            assert api_response.ok, f"API response is: {api_response}"
            self.logger.info(f"API response is: {api_response}")

            headers_out = api_response.headers
            self.logger.debug(
                f"API request headers limit/remaining: {headers_out}/{headers_out.get('x-ratelimit-remaining')}"
            )

            json_pg = api_response.json()  # get crucial json
            if not json_pg:  # check emptiness of result.
                self.logger.debug("Result of api_response.json() is empty list.")
                self.logger.error(
                    f"Result of API request is an empty json. Error - cannot currently handle this result nicely. Traceback: {traceback.format_exc()}"
                )

            # this should be the important aggregator bit...
            all_issues.extend(json_pg)
            self.logger.info(f"all_issues length is now {len(all_issues)}")

            self.logger.debug(f"Total number of issues grabbed is {len(all_issues)}.")

            # expect None if there is no next. .get() doesn't fail if out of scope:
            response_next = api_response.links.get("next")

            # if this is a single-page repo, it runs once then returns out.
            if response_next is not None:
                issues_url = response_next[
                    "url"
                ]  # square brackets means we get an error not silent None
            else:  #
                return all_issues  # returning something breaks the while loop

            page += 1
        raise RuntimeError(
            f"This (multi-page) issue-getting exceeded {page} pages; API repsonse links was: {api_response.links if api_response else None}"
        )

    def get_all_pages_issues(
        self,
        repo_name: str,
        out_filename="all-issues",
    ) -> list:
        """
        Obtains all fields of data from all pages for a given github repo `repo_name`.
        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param out_filename: filename suffix indicating issues content (Default: 'issues')
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :returns: `all_issues` pd.DataFrame containing 30 fields per issue for given repo `repo_name`.
        :rtype: Dict
        """

        # assert isinstance(repo_name, str), "Ensure repository name in string format (e.g. 'repo-owner/repo-name')"  # move this to outer function to ensure inputs to here are correct

        self.logger.info(f"Repo name is {repo_name}. Getting issues.")
        write_out = f"{self.data_location / out_filename}_{self.sanitised_repo_name}"

        write_out_extra_info_json = f"{write_out}_{self.current_date_info}.json"

        # create empty dict to store issues data
        all_issues = {}

        # count open issue tickets
        try:
            self.logger.info("issue_links: multipage function used.")
            all_issues = self._page_issues_grabber(
                REPOS_API_URL,
                repo_name,
            )
            self.logger.debug(f"Type of all_issues is: {type(all_issues)}")

        except Exception as e:
            self.logger.error(
                f"Error in getting issues for repo name {repo_name}: {e}."
            )
            raise

        self.logger.info(
            f"{len(all_issues)} issues returned from repo {repo_name} at {write_out_extra_info_json}."
        )

        with open(write_out_extra_info_json, "w") as json_file:
            json.dump(all_issues, json_file)

        if not os.path.exists(write_out_extra_info_json):
            self.logger.error(
                f"JSON file was not written out correctly and does NOT exist at path: {os.path.exists(write_out_extra_info_json)}"
            )

        # self.logger.debug(f"Type of all_issues is: {type(all_issues)}")

        return all_issues
