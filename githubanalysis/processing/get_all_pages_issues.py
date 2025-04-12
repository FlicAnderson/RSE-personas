"""Get all data from all pages of issues for a GitHub repo."""

import os
import json
import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
import traceback
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries

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


class IssueGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(
        self,
        repo_name: str,
        in_notebook: bool,
        config_path: str,
        logger: None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/get_all_pages_issues_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.s = requests.Session()
        retries = Retry(
            total=10,
            connect=5,
            read=3,
            backoff_factor=1,
            status_forcelist=[202, 502, 503, 504],
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retries))
        self.gh_token = ghauth.setup_github_auth(config_path=config_path)
        self.headers = {"Authorization": "token " + self.gh_token}
        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits
        self.sanitised_repo_name = repo_name.replace("/", "-")

    def check_repo_has_issues(self, repo_name: str) -> bool:
        repos_api_url = "https://api.github.com/repos/"
        check_issue_url = f"{repos_api_url}{repo_name}"
        api_response = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=check_issue_url, headers=self.headers),
                repo_name=repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        assert api_response.ok, f"API response is: {api_response}"

        self.logger.debug(f"API shows repo {repo_name} has issues_enabled.")

        json_response = api_response.json()
        assert isinstance(
            json_response, dict
        ), f"WARNING: result of api_response.json() in check_repo_has_issues() is NOT a dict as expected: type is {api_response.json()}."

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
        write_out_location="data/",
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

        if self.in_notebook:
            write_out = f"../../{write_out_location}{out_filename}_{self.sanitised_repo_name}"  # look further up for correct path
        else:
            write_out = f"{write_out_location}{out_filename}_{self.sanitised_repo_name}"

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
