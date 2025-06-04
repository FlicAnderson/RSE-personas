"""Function to retrieve all commits across ALL branches for a given GitHub repository and remove duplicates."""

import os
import logging
import pandas as pd
import json
from githubanalysis.setup_classes import RESTRequestSetup
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries

from githubanalysis.processing.get_branches import BranchGetter
# import githubanalysis.processing.deduplicate_commits as dedupcommits


def make_url(
    repos_api_url: str,
    repo_name: str,
    branch: str,
    per_pg: int | str,
    page: int | str,
):
    if branch == "main":
        return f"{repos_api_url}{repo_name}/commits?per_page={per_pg}&page={page}"  # don't use branch in query, obtains GH default branch.
    else:
        return f"{repos_api_url}{repo_name}/commits?sha={branch}&per_page={per_pg}&page={page}"


def deduplicate_commits(all_branches_commits: dict[str, list]):
    shas = set()
    modified: dict[str, list] = {}
    for branch_name, commits in all_branches_commits.items():
        modified[branch_name] = []
        for commit in commits:
            sha = commit["sha"]
            if sha not in shas:
                shas.add(sha)
                modified[branch_name].append(commit)
    return modified


class AllBranchesCommitsGetter(RESTRequestSetup):
    def _log_name(self) -> str:
        return "get_all_branches_commits_logs"

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(
            config_path=config_path, in_notebook=in_notebook, logger=logger
        )
        self.sanitised_repo_name = repo_name.replace("/", "-")

    def _singlepage_commit_grabber(
        self,
        repos_api_url: str,
        repo_name: str,
        branch: str,
        per_pg: str | int,
    ) -> list[dict]:
        commits_url = make_url(repos_api_url, repo_name, branch, per_pg, page=1)

        self.logger.info(
            f">> Running commit grab for repo {repo_name}, on branch {branch}, in page 1 of 1."
        )

        self.logger.info(f"getting json via request url {commits_url}.")
        api_response = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=commits_url, headers=self.headers),
                repo_name=repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        assert api_response.ok, f"API response is: {api_response}"

        all_commits = api_response.json()

        return all_commits

    def _multipage_commit_grabber(
        self,
        commit_links: dict,
        repos_api_url: str,
        repo_name: str,
        branch: str,
        per_pg: str | int,
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
            self.logger.info(f"API is checking url: {commits_url}")

            # this is the important part: run API call with retries and sleeps if necessary to avoid rate limit issues
            api_response = run_with_retries(
                lambda: raise_if_response_error(
                    api_response=self.s.get(url=commits_url, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                self.logger,
            )

            assert api_response.ok, f"API response is: {api_response}"
            self.logger.info(f"API response is: {api_response}")

            headers_out = api_response.headers
            self.logger.debug(
                f"record ID request headers limit/remaining: {headers_out}/{headers_out.get('x-ratelimit-remaining')}"
            )

            json_pg = api_response.json()
            all_commits.extend(json_pg)

        return all_commits

    def get_all_branches_commits(
        self,
        repo_name: str,
        per_pg=100,
        out_filename: str = "all-branches-commits",
        write_out_location: str = "data/",
    ) -> dict[str, list[str]]:
        """
        Obtain all DEDUPLICATED commits data from all API request pages for ALL BRANCHES of a given GitHub repo `repo_name`.
        cf: get_all_pages_commits( ) which only returns main branch commits.

        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
        :type: int
        :param out_filename: filename suffix indicating commits content (Default: 'all-branches-commits')
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :return: `unique_commits_all_branches` dict of lists for repo `repo_name`.
        :rtype: dict

        Example:

        # setting up logger
        logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='../../logs/get_all_branches_commits_NOTEBOOK_logs.txt')

        # set example repo_name
        repo_name = 'JeschkeLab/DeerLab'

        # set up the class details for running inside jupyter notebook
        allbranchescommitsgetter = AllBranchesCommitsGetter(repo_name = repo_name, in_notebook=True, config_path='../../githubanalysis/config.cfg', logger=logger)

        # run function
        all_branches_commits = allbranchescommitsgetter.get_all_branches_commits(repo_name=repo_name)
        # ... response info from logger
        INFO:Commits data written out to file for repo JeschkeLab/DeerLab ../../data/all-branches-commits_JeschkeLab-DeerLab_2024-09-23.json.
        INFO:566 UNIQUE (deduplicated) commits data written out for all branches of JeschkeLab/DeerLab at ../../data/all-branches-commits_JeschkeLab-DeerLab_2024-09-23_deduplicated.json.
        """

        self.logger.debug(
            f"Getting commits for repo {repo_name}, running within notebook is {self.in_notebook}."
        )

        write_out = f"{self.data_location/out_filename}_{self.sanitised_repo_name}"

        write_out_extra_info_json = f"{write_out}_{self.current_date_info}.json"

        branchgetter = BranchGetter(
            in_notebook=self.in_notebook,
            config_path=self.config_path,
            logger=self.logger,
        )
        branches_shas = branchgetter.get_branch_shas(
            repo_name,
            per_pg,
        )

        all_branches_commits = {}

        for branch_sha in branches_shas:
            try:
                page = 1  # try first page only
                repos_api_url = "https://api.github.com/repos/"
                commits_url = make_url(
                    repos_api_url, repo_name, branch_sha, per_pg, page
                )

                # important bit: API request with auth headers
                api_response = run_with_retries(
                    fn=lambda: raise_if_response_error(
                        api_response=self.s.get(url=commits_url, headers=self.headers),
                        repo_name=repo_name,
                        logger=self.logger,
                    ),
                    logger=self.logger,
                )

                assert (
                    api_response.status_code != 401
                ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {commits_url} is {api_response}"
                # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

                commit_links = api_response.links

                if "last" in commit_links:
                    all_commits = self._multipage_commit_grabber(
                        commit_links, repos_api_url, repo_name, branch_sha, per_pg
                    )
                else:
                    all_commits = self._singlepage_commit_grabber(
                        repos_api_url, repo_name, branch_sha, per_pg
                    )

                all_branches_commits[branch_sha] = all_commits

            except Exception as e:
                self.logger.error(f"Exception error at get_all_branches_commits(): {e}")
                raise RuntimeError("failed to get all branches of commits") from e

        unique_commits_all_branches = deduplicate_commits(all_branches_commits)

        write_out_extra_info_dedup = (
            f"{write_out}_{self.current_date_info}_deduplicated.json"
        )

        with open(write_out_extra_info_json, "w") as json_file:
            json.dump(all_branches_commits, json_file)

        with open(write_out_extra_info_dedup, "w") as json_file:
            json.dump(unique_commits_all_branches, json_file)

        if not os.path.exists(write_out_extra_info_json):
            self.logger.error(
                f"JSON file does NOT exist at path: {os.path.exists(write_out_extra_info_json)}"
            )

        self.logger.info(
            f"Raw repo commits data (including duplicates) from all branches written out to file for repo {repo_name} {write_out_extra_info_json}."
        )

        # calculate number of unique commits
        total_commit_count = sum(
            len(commits_list) for commits_list in unique_commits_all_branches.values()
        )

        self.logger.info(
            f"{total_commit_count} UNIQUE (deduplicated) commits written out for all branches of {repo_name} at {write_out_extra_info_dedup}."
        )

        return unique_commits_all_branches
