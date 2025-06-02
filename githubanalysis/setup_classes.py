"""Classes for setting up all the functions and whatnot."""

from pathlib import Path
import datetime
import logging
import utilities.get_default_logger as loggit
from abc import ABC, abstractmethod


class EnvSetup(
    ABC
):  # ABC is to show this is not a 'real' class, mainly just concepts and whatnot
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str

    @abstractmethod  # show that this thing exists, but needs overwriting each time
    def log_name(self) -> str: ...

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name=f"logs/{self.log_name()}.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues


class LocatSetup(EnvSetup):
    image_write_location: Path
    data_read_location: Path
    dataset_name: str

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(in_notebook, logger)

        self.data_read_location = Path("data/" if not in_notebook else "../../data/")
        self.data_write_location = (
            Path("data/" if not in_notebook else "../../data/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.image_write_location = (
            Path("images/" if not in_notebook else "../../images/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.dataset_name = dataset_name
