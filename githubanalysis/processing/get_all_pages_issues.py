"""Get all data from all pages of issues for a GitHub repo."""

import os
import json
import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries


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


class IssueGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(
        self,
        repo_name: str,
        in_notebook: bool,
        config_path: str,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
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

        self.logger.info(f"API shows repo {repo_name} has issues_enabled.")

        json_response = api_response.json()
        assert isinstance(
            json_response, dict
        ), f"WARNING: result of api_response.json() in check_repo_has_issues() is NOT a dict as expected: type is {api_response.json()}."

        if len(json_response) > 0:
            assert isinstance(json_response.get("has_issues"), bool)

            n_open_isses = json_response.get("open_issues_count")
            assert (
                n_open_isses is not None
            ), f"The value for repo {repo_name} 'open_issues_count' is None; this is not ideal."
            assert isinstance(
                n_open_isses, int
            ), f"The value for repo {repo_name} 'open_issues_count' is not an integer, instead it is {type(n_open_isses)}."

            if json_response.get("has_issues") and n_open_isses > 0:
                return True  # this is what we're hoping for: has issues, and more than zero of them.
        else:
            self.logger.error(
                f"Repository {repo_name} does NOT have issues enabled OR there are NO issues created despite being enabled. Raising NoIssuesError."
            )
        raise NoIssuesError

    def _singlepage_issues_grabber(
        self,
        repos_api_url: str,
        repo_name: str,
        state: str,
        pulls: bool,
        per_pg: str | int,
    ) -> list[dict]:
        issues_url = make_url(
            repos_api_url=repos_api_url,
            repo_name=repo_name,
            state=state,
            pulls=pulls,
            per_pg=per_pg,
            page=1,
        )
        self.logger.debug(
            f"Trying to pull issue information from repo {repo_name} with query {issues_url}."
        )
        api_reponse = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=issues_url, headers=self.headers),
                repo_name=repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        assert api_reponse.ok, f"API response is {api_reponse}."

        all_issues = api_reponse.json()
        return all_issues  # THIS IS JSON OUTPUT CURRENTLY

    def _multipage_issues_grabber(
        self,
        issue_links: dict,
        repos_api_url: str,
        repo_name: str,
        state: str,
        pulls: bool,
        per_pg: str | int,
    ) -> list[dict]:
        issue_links_last = issue_links["last"]["url"].split("&page=")[1]
        pages_issues = int(issue_links_last)

        all_issues = []
        pg_range = range(1, (pages_issues + 1))

        for i in pg_range:
            self.logger.info(
                f">> Running issues grab for repo {repo_name}, on page {i} of {pages_issues}."
            )
            page = i
            issues_url = make_url(
                repos_api_url=repos_api_url,
                repo_name=repo_name,
                state=state,
                pulls=pulls,
                per_pg=per_pg,
                page=page,
            )
            self.logger.info(f"API is checking url: {issues_url}")

            # this is the important part: run API call with retries and sleeps if necessary to avoid rate limit issues
            api_response = run_with_retries(
                lambda: raise_if_response_error(
                    api_response=self.s.get(url=issues_url, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                self.logger,
            )

            assert api_response.ok, f"API response is: {api_response}"
            self.logger.info(f"API response is: {api_response}")

            headers_out = api_response.headers
            self.logger.debug(
                f"API request headers limit/remaining: {headers_out}/{headers_out.get('x-ratelimit-remaining')}"
            )

            json_pg = api_response.json()
            all_issues.extend(json_pg)

            self.logger.debug(
                f"Total number of issues grabbed is {len(all_issues)} in {pages_issues} page(s)."
            )

        return all_issues

    def get_all_pages_issues(
        self,
        repo_name: str,
        out_filename="all-issues",
        write_out_location="data/",
    ):
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

        # create empty df to store issues data
        all_issues = {}

        # count open issue tickets
        try:
            page = 1  # try first page only
            repos_api_url = "https://api.github.com/repos/"

            issues_url = make_url(
                repos_api_url=repos_api_url,
                repo_name=repo_name,
                state="all",  # alternatives: "open" (default) | "closed"
                pulls=True,
                per_pg=100,  # default is 30 on GH API
                page=page,
            )
            self.logger.debug(f"Issues URL being queried is: {issues_url}.")

            api_response = self.s.get(url=issues_url, headers=self.headers)

            assert (
                api_response.status_code != 401
            ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {issues_url} is {api_response}"
            # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

            issue_links = api_response.links

            if "last" in issue_links:
                all_issues = self._multipage_issues_grabber(
                    issue_links,
                    repos_api_url,
                    repo_name,
                    state="all",
                    pulls=True,
                    per_pg=100,
                )
            else:
                all_issues = self._singlepage_issues_grabber(
                    repos_api_url,
                    repo_name,
                    state="all",
                    pulls=True,
                    per_pg=100,
                )
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

        return all_issues
