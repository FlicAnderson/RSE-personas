from zenodocode.get_zenodo_ids import get_zenodo_ids as fetch_zs
from zenodocode.get_gh_urls import GhURLsGetter


def get_zenodo_ids(n_records_to_fetch: int, config) -> list[int]:
    return fetch_zs(auth=config["ACESS"]["token"], total_records=n_records_to_fetch)  # type: ignore


def get_repo_urls(
    zenodo_IDs: list[int],
):
    return GhURLsGetter.get_gh_urls(self, zenodo_ids=zenodo_IDs, out_filename="gh_urls")


def prepare_workflow(n_records_to_fetch, config):
    config = load_config_file()

    ids = get_zenodo_ids(n_records_to_fetch, config)

    repo_urls = get_repo_urls(ids)

    gh_repo_urls = filter_gh_repo_urls(repo_urls)

    summarised_gh_repos = summarise_gh_repos(gh_repo_urls)

    return summarised_gh_repos
