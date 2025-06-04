"""Function to retrieve and return branches info for a given GitHub repository."""

from githubanalysis.setup_classes import RESTRequestSetup
import logging
from utilities.check_gh_reponse import (
    run_with_retries,
    raise_if_response_error,
)


class BranchGetter(RESTRequestSetup):
    def _log_name(self) -> str:
        return "get_branches"

    def __init__(
        self,
        in_notebook: bool,
        config_path: str,
        logger: logging.Logger | None,
    ) -> None:
        super().__init__(
            config_path=config_path, in_notebook=in_notebook, logger=logger
        )

    def get_branch_shas(self, repo_name, per_pg=100) -> set[str]:
        """
        Get branch info for given repo repo_name and return it.

        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
        :type: int
        :return: Branch hashes in a set for repo `repo_name`.
        :rtype: set of strings
        """

        repos_api_url = "https://api.github.com/repos/"
        api_call = f"{repos_api_url}{repo_name}/branches?per_page={per_pg}"
        # assemble API call
        api_response = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=api_call, headers=self.headers),
                repo_name=repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )

        assert (
            api_response.status_code != 401
        ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {api_call} is {api_response}"
        # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

        assert (
            api_response.status_code == 200
        ), f"WARNING! API Response code is NOT 200 ({api_response.status_code}). Cannot proceed with data gathering for get_branches()."

        branches: list = api_response.json()
        # pull sha out of commit field as separate field

        return {branch["commit"]["sha"] for branch in branches}
        # this is returned as a set for deduplication purposes to avoid
        # multiple API calls for branches with matching SHAs!
