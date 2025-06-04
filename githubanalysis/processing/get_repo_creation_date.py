"""Set up GitHub API connection for given GitHub repository."""

import pandas as pd
import logging
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries
from githubanalysis.setup_classes import RESTRequestSetup


class RepoDater(RESTRequestSetup):
    repo_name: str

    def _log_name(self) -> str:
        return "get_repo_creation_date"

    def __init__(
        self,
        repo_name: str,
        config_path: str,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(
            config_path=config_path,
            in_notebook=in_notebook,
            logger=logger,
        )
        self.repo_name = repo_name

    def get_repo_creation_date(self):
        """
        NOTE: Requires `access_token` setup with GitHub.
        """
        base_repo_url = "https://api.github.com/repos"
        repo_url = f"{base_repo_url}/{self.repo_name}"
        api_response = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=repo_url, headers=self.headers),
                repo_name=self.repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        api_response_json = api_response.json()

        # get creation date:
        repo_creation_date = pd.to_datetime(
            api_response_json.get("created_at")
        )  # type is pandas._libs.tslibs.timestamps.Timestamp
        repo_creation_date = repo_creation_date.tz_convert(
            "UTC"
        )  # created_at date now 'intelligently' utc

        self.logger.info(
            f"Creation date of repo {self.repo_name} is {repo_creation_date.year} {repo_creation_date.month} {repo_creation_date.day}."
        )

        return repo_creation_date
