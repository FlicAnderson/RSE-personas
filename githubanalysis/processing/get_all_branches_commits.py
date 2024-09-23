"""Function to retrieve all commits across ALL branches for a given GitHub repository and remove duplicates."""

import requests
from requests.adapters import HTTPAdapter, Retry
import logging
import pandas as pd
import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth

import githubanalysis.processing.get_branches as branchgetter


def _normalise_default_branch_name(branch):
    if branch == "default":
        return "main"
    return branch


def make_url(repos_api_url: str, repo_name: str, branch: str, per_pg: str, page: str):
    if branch == "main":
        return f"{repos_api_url}{repo_name}/commits?per_page={per_pg}&page={page}"  # don't use branch in query, obtains GH default branch.
    else:
        return f"{repos_api_url}{repo_name}/commits?sha={branch}&per_page={per_pg}&page={page}"


class AllBranchesCommitsGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(self, config_path: str, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_all_branches_commits_logs.txt",
            )
        else:
            self.logger = logger

        self.s = requests.Session()
        retries = Retry(
            total=10,
            connect=5,
            read=3,
            backoff_factor=1.5,
            status_forcelist=[202, 502, 503, 504],
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retries))
        self.gh_token = ghauth.setup_github_auth(config_path=config_path)
        self.headers = {"Authorization": "token " + self.gh_token}
        self.config_path = config_path

    def __del__(self):
        self.s.close()

    def _singlepage_commit_grabber(
        self, repos_api_url: str, repo_name: str, branch: str, per_pg: str
    ):
        commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page=1)

        # logger.debug(f"getting json via request url {commits_url}.")
        api_response = self.s.get(url=commits_url, headers=self.headers)

        json_pg = api_response.json()

        all_commits = pd.DataFrame.from_dict(json_pg)
        all_commits["branchname"] = branch
        return all_commits

    def _multipage_commit_grabber(
        self,
        commit_links: dict,
        repos_api_url: str,
        repo_name: str,
        branch: str,
        per_pg: str,
    ):
        commit_links_last = commit_links["last"]["url"].split("&page=")[1]
        pages_commits = int(commit_links_last)

        all_commits = pd.DataFrame()

        pg_range = range(1, (pages_commits + 1))
        for i in pg_range:
            print(
                f">> Running commit grab for repo {repo_name}, on branch {branch}, in page {i} of {pages_commits}."
            )
            page = i
            commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page)
            api_response = self.s.get(url=commits_url, headers=self.headers)

            print(api_response)
            print(commits_url)

            json_pg = api_response.json()

            all_commits = pd.concat([all_commits, pd.DataFrame.from_dict(json_pg)])
            all_commits["branchname"] = branch
        return all_commits

    def get_all_branches_commits(
        self,
        repo_name,
        per_pg=100,
        out_filename="all-branches-commits",
        write_out_location="data/",
    ):
        """
        Obtain all commits data from all API request pages for ALL BRANCHES of a given GitHub repo `repo_name`.
        cf: get_all_pages_commits( ) which only returns main branch commits.

        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
        :type: int
        :param out_filename: filename suffix indicating commits content (Default: 'all-commits')
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :return: `all_branches_commits` pd.DataFrame for repo `repo_name`.
        :type: DataFrame
        """
        all_branches_commits = pd.DataFrame()

        branches_info = branchgetter.get_branches(repo_name, self.config_path, per_pg)

        for branch in branches_info.branch_sha:
            branch = _normalise_default_branch_name(branch)
            try:
                page = 1  # try first page only
                repos_api_url = "https://api.github.com/repos/"
                commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page)

                # important bit: API request with auth headers
                api_response = self.s.get(url=commits_url, headers=self.headers)
                assert (
                    api_response.status_code != 401
                ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {commits_url} is {api_response}"
                # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

                if api_response.status_code != 200:
                    continue

                # logger.debug(f"Getting commits for repo {repo_name} for branch {branch}.")
                # self.logger.debug(f"{api_response}")

                commit_links = api_response.links

                if "last" in commit_links:
                    all_commits = self._multipage_commit_grabber(
                        commit_links, repos_api_url, repo_name, branch, per_pg
                    )
                else:
                    all_commits = self._singlepage_commit_grabber(
                        repos_api_url, repo_name, branch, per_pg
                    )

                all_branches_commits = pd.concat([all_branches_commits, all_commits])
                print(len(all_branches_commits))

            except Exception as e:
                print(f"Error: {e}")
                raise

        return all_branches_commits
