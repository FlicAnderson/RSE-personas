"""Function to retrieve all commits across ALL branches for a given GitHub repository and remove duplicates."""

import os
import requests
from requests.adapters import HTTPAdapter, Retry
import logging
import pandas as pd
import datetime
import json
import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth

import githubanalysis.processing.get_branches as branchgetter
# import githubanalysis.processing.deduplicate_commits as dedupcommits


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

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: logging.Logger = None,
    ) -> None:
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
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits
        self.sanitised_repo_name = repo_name.replace("/", "-")

    def __del__(self):
        self.s.close()

    def _singlepage_commit_grabber(
        self, repos_api_url: str, repo_name: str, branch: str, per_pg: str
    ) -> list[dict]:
        commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page=1)

        self.logger.info(
            f">> Running commit grab for repo {repo_name}, on branch {branch}, in page 1 of 1."
        )

        # logger.debug(f"getting json via request url {commits_url}.")
        api_response = self.s.get(url=commits_url, headers=self.headers)

        all_commits = api_response.json()

        return all_commits

    def _multipage_commit_grabber(
        self,
        commit_links: dict,
        repos_api_url: str,
        repo_name: str,
        branch: str,
        per_pg: str,
    ) -> list[dict]:
        commit_links_last = commit_links["last"]["url"].split("&page=")[1]
        pages_commits = int(commit_links_last)

        all_commits = pd.DataFrame()
        all_commits = []
        pg_range = range(1, (pages_commits + 1))
        for i in pg_range:
            self.logger.info(
                f">> Running commit grab for repo {repo_name}, on branch {branch}, in page {i} of {pages_commits}."
            )
            page = i
            commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page)
            api_response = self.s.get(url=commits_url, headers=self.headers)

            self.logger.info(f"API response is: {api_response}")
            self.logger.info(f"API is checking url: {commits_url}")

            json_pg = api_response.json()
            all_commits.extend(json_pg)

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
        :return: `unique_commits_all_branches` pd.DataFrame for repo `repo_name`.
        :type: DataFrame

        Example:

        # setting up logger
        logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='../../logs/get_all_branches_commits_NOTEBOOK_logs.txt')

        # set example repo_name
        repo_name = 'JeschkeLab/DeerLab'

        # set up the class details for running inside jupyter notebook
        allbranchescommitsgetter = AllBranchesCommitsGetter(repo_name = repo_name, in_notebook=True, config_path='../../githubanalysis/config.cfg', logger=logger)

        # run function
        all_branches_commits = allbranchescommitsgetter.get_all_branches_commits(repo_name=repo_name)
        len(all_branches_commits) # 5679
        """

        self.logger.debug(
            f"Getting commits for repo {repo_name}, running within notebook is {self.in_notebook}."
        )

        if self.in_notebook:
            write_out = f"../../{write_out_location}{out_filename}_{self.sanitised_repo_name}"  # look further up for correct path
        else:
            write_out = f"{write_out_location}{out_filename}_{self.sanitised_repo_name}"

        # write_out_extra_info = f"{write_out}_{self.current_date_info}.csv"
        write_out_extra_info_json = f"{write_out}_{self.current_date_info}.json"

        branches_info = branchgetter.get_branches(repo_name, self.config_path, per_pg)


        all_branches = {}
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

                commit_links = api_response.links

                if "last" in commit_links:
                    all_commits = self._multipage_commit_grabber(
                        commit_links, repos_api_url, repo_name, branch, per_pg
                    )
                else:
                    all_commits = self._singlepage_commit_grabber(
                        repos_api_url, repo_name, branch, per_pg
                    )
                
                all_branches[branch] = all_commits

                # self.logger.info(
                #     f"There are {len(all_branches_commits)} after getting commits from branch {branch}."
                # )
            


            except Exception as e:
                self.logger.error(f"Error: {e}")
                raise

        with open(write_out_extra_info_json, "w") as json_file:
            json.dump(all_branches, json_file)

        # self.logger.info(
        #     f"Repo {repo_name} has {len(all_branches_commits)} commits total after getting commits from ALL {len(branches_info)} BRANCHES."
        # )

        # # save out dataframe of ALL BRANCHES commits
        # all_branches_commits.to_json(
        #     path_or_buf=write_out_extra_info_json,
        #     orient="records",
        #     date_format="iso",
        #     lines=True,
        # )
        if not os.path.exists(write_out_extra_info_json):
            self.logger.error(
                f"JSON file does NOT exist at path: {os.path.exists(write_out_extra_info_json)}"
            )

        self.logger.info(
            f"Commits data written out to file for repo {repo_name} {write_out_extra_info_json}."
        )

        # drop non-unique commit hashes
        # unique_commits_all_branches = dedupcommits.deduplicate_commits(
        #     all_branches_commits
        # )

        # write_out_extra_info_dedup = (
        #     f"{write_out}_{self.current_date_info}_deduplicated.csv"
        # )
        # write the deduplicated set of commits out to csv
        # unique_commits_all_branches.to_csv(
        #     write_out_extra_info_dedup,
        #     mode="w",
        #     index=True,
        #     header=not os.path.exists(write_out_extra_info_dedup),
        # )
        # self.logger.info(
        #     f"{len(unique_commits_all_branches)} UNIQUE (deduplicated) commits data written out for all branches of {repo_name} at {write_out_extra_info_dedup}."
        # )

        # return unique_commits_all_branches

        return all_branches
