from logging import Logger

from githubanalysis.setup_classes import LocationSetup


class Repo_Reader(LocationSetup):
    def _log_name(self) -> str:
        return "repo_reader"

    def __init__(self, in_notebook: bool, logger: None | Logger = None) -> None:
        super().__init__(in_notebook, logger)

    def simple_read_repos_from_file(self, filename) -> list[str]:
        with open(filename, "r") as f:
            repos = [txtline.strip() for txtline in f.readlines()]
            return repos

    def get_repos(
        self,
        repo_list_file_name: str,  # ideally deal with this so it handles PATHS
    ) -> list[str]:
        """
        Read the list of repo names from input file (commandline argument.)
        Returns list of strings (reponames)
        """
        repo_list = self.simple_read_repos_from_file(
            filename=self.data_location / repo_list_file_name
        )
        return repo_list
