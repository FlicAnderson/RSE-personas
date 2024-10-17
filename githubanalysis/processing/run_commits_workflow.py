from githubanalysis.processing.commits_workflow import RunCommits


import argparse
import pandas as pd
from logging import Logger

parser = argparse.ArgumentParser()
parser.add_argument(
    "--repo-names",
    metavar="PATH",
    help="Name of the repo to workflow",
    type=str,
)


def single_repo_method(repo_name: str) -> pd.DataFrame:
    """
    This is used by multi_repo_method()
    """
    runcommits = RunCommits(
        repo_name=repo_name,
        in_notebook=True,
        config_path="../../githubanalysis/config.cfg",  # TODO make this editable and useful
        write_read_location="../../data/",
    )
    repodf = runcommits.do_it_all()
    return repodf


def read_repos_from_file(filename, logger: Logger) -> dict[str, pd.DataFrame | None]:
    with open(filename, "r") as f:
        repos = [txtline.strip() for txtline in f.readlines()]
        return multi_repo_method(repo_names=repos, logger=logger)


def multi_repo_method(
    repo_names: list[str], logger: Logger
) -> dict[str, pd.DataFrame | None]:
    """
    Loop through several repos from a file input, running
    single_repo_method() on each.
    Return dictionary of repodfs with repo_name as key.
    """
    collation_dict = {}
    for repo in repo_names:
        try:
            repodf = single_repo_method(repo_name=repo)
        except Exception as e:
            logger.error(
                f"Encountered repo-getting-workflow-borking error in repo {repo}; error {e}"
            )
            collation_dict[repo] = None
            continue  # skip to next loop iteration

        collation_dict[repo] = repodf

    return collation_dict


if __name__ == "__main__":
    args = parser.parse_args()
    names = args.repo_names
