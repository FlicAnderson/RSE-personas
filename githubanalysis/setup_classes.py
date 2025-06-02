"""Classes for setting up all the functions and whatnot."""

from pathlib import Path
import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
import logging
import githubanalysis.processing.setup_github_auth as ghauth
import utilities.get_default_logger as loggit
from abc import ABC, abstractmethod


class EnvSetup(
    ABC
):  # ABC is to show this is not a 'real' class, mainly just concepts and whatnot
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str

    @abstractmethod  # show that this thing exists, but needs overwriting each time
    def _log_name(self) -> str: ...

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name=f"logs/{self._log_name()}.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues


class LocationSetup(EnvSetup):
    data_location: Path

    def __init__(self, in_notebook: bool, logger: None | logging.Logger = None) -> None:
        super().__init__(in_notebook, logger)

        self.data_location = Path("data/" if not in_notebook else "../../data/")


class RESTRequestSetup(LocationSetup):
    config_path: str
    s: requests.Session
    gh_token: str
    headers: dict[str, str]

    def __init__(
        self,
        config_path: str,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(in_notebook, logger)
        self.config_path = config_path
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


class DatasetSetup(LocationSetup):
    image_write_location: Path
    data_write_location: Path
    data_read_location: Path
    dataset_name: str

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(in_notebook, logger)

        self.data_read_location = self.data_location

        self.data_write_location = (
            self.data_location / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.image_write_location = (
            Path("images/" if not in_notebook else "../../images/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.dataset_name = dataset_name
        self.data_write_location.mkdir(exist_ok=exists_ok)
        self.image_write_location.mkdir(exist_ok=exists_ok)
