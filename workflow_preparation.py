from zenodocode.get_zenodo_ids import get_zenodo_ids as fetch_zs
from zenodocode.get_gh_urls import GhURLsGetter
import pandas as pd
from enum import Enum, auto


def get_zenodo_ids(n_records_to_fetch: int, config) -> list[int]:
    return fetch_zs(auth=config["ACCESS"]["token"], total_records=n_records_to_fetch)  # type: ignore


def get_gh_repo_urls(zenodo_IDs: list[int]):
    getter = GhURLsGetter()
    return getter.get_gh_urls(zenodo_ids=zenodo_IDs)


"""
TODO:
- [ ] finish summarise_gh_repos
- [ ] We want to be able to resume from existing files:
   - [ ] This requires error handling: 
   - [ ]
"""


class SkipTo(Enum):
    NONE = auto()
    REPO_UYRLS = auto()
    SUMMARISED_GH_URLS = auto()


def prepare_workflow(
    n_records_to_fetch,
    config,
    skip_to: SkipTo = SkipTo.NONE,
    starting_data=None,
):
    if skip_to.value < SkipTo.SUMMARISED_GH_URLS.value:
        if skip_to.value < SkipTo.REPO_UYRLS.value:
            if skip_to.value < SkipTo.NONE.value:
                ids = get_zenodo_ids(n_records_to_fetch, config)
            else:
                ids = starting_data
            gh_repo_urls = get_gh_repo_urls(ids)
        else:
            gh_repo_urls = starting_data
        summarised_gh_repos = summarise_gh_repos(gh_repo_urls)
    else:
        summarised_gh_repos = starting_data

    return summarised_gh_repos
