"""Summarise key stats for GitHub repository."""

import sys
import pandas as pd
import datetime
from datetime import datetime
from datetime import timezone
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.analysis.calc_days_since_repo_creation as dayssince


class RepoStatsSummariser:
    # shoutout to @dk949 for advice and patient explanation on using Classes for fun & profit

    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/summarise_repo_stats_logs.txt",
            )
        else:
            self.logger = logger

    def summarise_repo_stats(
        self, repo_name, config_path="githubanalysis/config.cfg", per_pg=1
    ):
        """
        Connect to given GitHub repository and get details
        when given 'username' and 'repo_name' repository name.
        Results are of type dict, containing keys for each stat.

        NOTE: Requires `access_token` setup with GitHub package.

        :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
        :type: str
        :param config_path: file path of config.cfg file containing GitHub Access Token. Default = 'githubanalysis/config.cfg'.
        :type: str
        :returns: repo_stats: dictionary w/ keys: "repo_name", "devs", "total_commits", "tickets", "last_commit", "repo_age_days",
        ... "repo_license", "repo_visibility", "repo_language".
        :type: dict

        Examples:
        ----------
        >>> summarise_repo_stats(repo_name='riboviz/riboviz', per_pg=100)
        TODO
        """

        # get auth string
        gh_token = ghauth.setup_github_auth(config_path=config_path)
        headers = {"Authorization": "token " + gh_token}

        s = requests.Session()
        retries = Retry(
            total=10,
            connect=5,
            read=3,
            backoff_factor=1.5,
            status_forcelist=[202, 502, 503, 504],
        )
        s.mount("https://", HTTPAdapter(max_retries=retries))

        # create output dict to update with stats:
        repo_stats = {}

        # get repo_name gh connection:
        repo_stats.update({"repo_name": repo_name})
        self.logger.debug(f"Repo name is {repo_name}")

        try:
            base_repo_url = "https://api.github.com/repos"
            connect_to = f"{base_repo_url}/{repo_name}"

            api_response = s.get(url=connect_to, headers=headers)
            print(
                f"API response at initial connection to {repo_name} is {api_response}"
            )
            self.logger.info(
                f"API response at initial connection to {repo_name} for request {api_response.url} is {api_response}."
            )
            repo_con = api_response.json()
            api_status = api_response.status_code

            repo_stats.update({"initial_HTTP_code": api_status})

        except Exception as e_connect:
            if api_response.status_code == 404:
                self.logger.error(
                    f"404 error in connecting to {repo_name}. Possibly this repo has been deleted or made private?"
                )
            if api_response.status_code == 401:
                self.logger.error(
                    f"401 (unauthorized) error in connecting to {repo_name}. Is your GitHub Personal Authentication Token valid and config.cfg file correctly formatted?"
                )
            self.logger.error(
                f"Error in setting up repo connection with repo name {repo_name} and config path {config_path}: {e_connect}."
            )

        if api_response.status_code != 404:
            try:
                # issue tickets enabled y/n:
                if repo_con.get("has_issues"):
                    repo_stats.update({"issues_enabled": repo_con.get("has_issues")})
                else:
                    self.logger.debug(
                        f"GitHub repository {repo_name} does not have issues enabled."
                    )
                    repo_stats.update({"issues_enabled": repo_con.get("has_issues")})

                self.logger.debug(
                    f"Repo issues enabled is {repo_stats.get('issues_enabled')}"
                )
            except Exception as e_tixenabled:
                self.logger.error(
                    f"Error in checking issues enabled with repo name {repo_name} and config path {config_path}: {e_tixenabled}."
                )

            # get stats:

            # is the repo a fork of something else?
            try:
                repo_con.get("fork")
                if repo_con.get("fork"):
                    repo_stats.update({"repo_is_fork": repo_con.get("fork")})
                else:
                    repo_stats.update({"repo_is_fork": repo_con.get("fork")})
                self.logger.debug(f"Repo is a fork: {repo_stats.get('repo_is_fork')}")
            except Exception as e_fork:
                self.logger.debug(
                    f"Error in checking whether repo is a fork at repo name {repo_name} and config path {config_path}: {e_fork}."
                )

            # count number of devs (contributors; including anonymous contribs* )
            try:
                contribs_url = f"https://api.github.com/repos/{repo_name}/contributors?per_page=1&anon=1"

                api_response = s.get(contribs_url, headers=headers)

                total_contributors = 1  # repo created by 1 person minimum; don't need to update unless there's more than one page (@ 1x person per page)

                if api_response.ok:
                    contrib_links = api_response.links
                    if "last" in contrib_links:
                        contrib_links_last = contrib_links["last"]["url"].split(
                            "&page="
                        )[1]
                        total_contributors = int(contrib_links_last)

                    if total_contributors >= 500:
                        self.logger.debug(
                            f"Repo {repo_name} has over 500 contributors, so API may not return contributors numbers accurately."
                        )

                    # * NOTE: gh API does NOT return username info where number of contributors is > 500;
                    #  ... after this they're listed as anonymous contributors.
                    #  ... It's NOT possible to get the number of contributors GH web page returns using API info.
                    # source: https://docs.github.com/en/free-pro-team@latest/rest/repos/repos?apiVersion=2022-11-28#list-repository-contributors
                    # > "GitHub identifies contributors by author email address.
                    # > This endpoint groups contribution counts by GitHub user, which includes all associated email addresses.
                    # > To improve performance, only the first 500 author email addresses in the repository link to GitHub users.
                    # > The rest will appear as anonymous contributors without associated GitHub user information."

                repo_stats.update({"devs": total_contributors})
                self.logger.debug(
                    f"Repo number of contributors is {repo_stats.get('devs')}"
                )

            except Exception as e_countdevs:
                self.logger.error(
                    f"Error in checking number of contributors with repo name {repo_name} and config path {config_path}: {e_countdevs}. API response: {api_response}"
                )

            # try:
            #     # count total number of commits
            #     total_commits = None

            #     base_commits_url = f"https://api.github.com/repos/{repo_name}/commits?per_page=1"

            #     s = requests.Session()
            #     retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
            #     s.mount('https://', HTTPAdapter(max_retries=retries))
            #     try:
            #         api_response = s.get(url=base_commits_url, timeout=10)
            #         commit_links = api_response.links
            #         commit_links_last = commit_links['last']['url'].split("&page=")[1]
            #         total_commits = int(commit_links_last)

            #         self.logger.debug(f"API response for getting total commits: {api_response}")

            #     except Exception as e:
            #         self.logger.error(f"API response total_commits_last_year fail exception: {e}; error type {type(e)}.")

            #     repo_stats.update({"total_commits": total_commits})
            #     self.logger.debug(f"Repo total commits is {repo_stats.get('total_commits')}.")

            # except Exception as e_commitstotal:
            #     self.logger.error(f"Error in checking total number of commits at repo name {repo_name} and config path {config_path}: {e_commitstotal}. API response: {api_response}")

            # count total commits in last year
            # Do something sensible re: no commits in last year returned TODO
            try:
                base_commit_stats_url = (
                    f"https://api.github.com/repos/{repo_name}/stats/commit_activity"
                )

                s = requests.Session()
                retries = Retry(
                    total=10,
                    connect=5,
                    read=3,
                    backoff_factor=1.5,
                    status_forcelist=[202, 502, 503, 504],
                )
                s.mount("https://", HTTPAdapter(max_retries=retries))
                try:
                    api_response = s.get(
                        url=base_commit_stats_url, timeout=10, headers=headers
                    )
                    self.logger.debug(
                        f"API response for getting total commits in year: {api_response}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"API response total_commits_last_year fail exception: {e}; error type {type(e)}."
                    )

                try:
                    total_commits_df = pd.DataFrame(api_response.json())
                    total_commits_1_year = total_commits_df["total"].sum()
                except Exception as e:
                    self.logger.error(
                        f"Failed trying to calculate the sum of commits in 1 year for repo {repo_name}: {e}."
                    )
                repo_stats.update({"total_commits_last_year": total_commits_1_year})
                self.logger.debug(
                    f"Repo total commits last year is {repo_stats.get('total_commits_last_year')}."
                )
            except Exception as e_commitsyear:
                self.logger.error(
                    f"Error in checking commits in last year at {repo_name} and config path {config_path}: {e_commitsyear}. API response: {api_response}"
                )

            try:
                # date of most recently updated PR:
                per_pg = 1
                state = "all"
                sort = "updated"
                direction = "desc"
                params_string = (
                    f"?per_pg={per_pg}&state={state}&sort={sort}&direction={direction}"
                )

                PRs_url = (
                    f"https://api.github.com/repos/{repo_name}/pulls{params_string}"
                )

                api_response = s.get(PRs_url, headers=headers)

                PRs_bool = None
                last_PR_updated = None

                if api_response.ok:
                    self.logger.debug(
                        f"API response for getting PRs info: {api_response}"
                    )

                    try:
                        assert len(api_response.json()) != 0, "No json therefore no PRs"
                        last_PR_update = api_response.json()[0][
                            "updated_at"
                        ]  # 0th(1st) for latest update as sorted desc.
                        date_format = "%Y-%m-%dT%H:%M:%S%z"
                        last_PR_updated = datetime.strptime(last_PR_update, date_format)
                        # as datetime w/ UTC timezone awareness(last_PR_update)
                        PRs_bool = True
                    except:
                        self.logger.debug(
                            f"No PRs found for repo {repo_name}; setting PRs_bool to False and last_PR_updated to None."
                        )
                        PRs_bool = False
                        last_PR_updated = None
                else:
                    api_response.raise_for_status()

                repo_stats.update({"has_PRs": PRs_bool})
                self.logger.debug(f"Repo PRs is {repo_stats.get('has_PRs')}.")
                repo_stats.update({"last_PR_update": last_PR_updated})
                self.logger.debug(
                    f"Repo last PR update is {repo_stats.get('last_PR_update')}."
                )
            except Exception as e_PRs:
                self.logger.error(
                    f"Error in checking commits in last year at {repo_name} and config path {config_path}: {e_PRs}. API response: {api_response}"
                )

            # count open issue tickets
            try:
                if repo_con.get("has_issues"):
                    state = "open"
                    issues_url = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=1"

                    api_response = s.get(url=issues_url, headers=headers)

                    if api_response.ok:
                        issue_links = api_response.links
                        if "last" in issue_links:
                            issue_links_last = issue_links["last"]["url"].split(
                                "&page="
                            )[1]
                            open_issues = int(issue_links_last)
                            repo_stats.update({"open_tickets": open_issues})
                        else:
                            open_issues = 0
                            repo_stats.update({"open_tickets": open_issues})
                else:
                    open_issues = 0
                    repo_stats.update({"open_tickets": open_issues})

                repo_stats.update({"open_tickets": open_issues})
                self.logger.debug(
                    f"Repo number of open issue tickets is {repo_stats.get('open_tickets')}."
                )
            except Exception as e_opentix:
                self.logger.error(
                    f"Error in checking open issue numbers at {repo_name} and config path {config_path}: {e_opentix}."
                )

            # count closed issue tickets
            try:
                if repo_con.get("has_issues"):
                    state = "closed"
                    issues_url = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=1"

                    api_response = s.get(url=issues_url, headers=headers)

                    if api_response.ok:
                        issue_links = api_response.links
                        if "last" in issue_links:
                            issue_links_last = issue_links["last"]["url"].split(
                                "&page="
                            )[1]
                            closed_issues = int(issue_links_last)
                            repo_stats.update({"closed_tickets": closed_issues})
                        else:
                            closed_issues = 0
                            repo_stats.update({"closed_tickets": closed_issues})
                else:
                    closed_issues = 0
                    repo_stats.update({"closed_tickets": closed_issues})

                repo_stats.update({"closed_tickets": closed_issues})
                self.logger.debug(
                    f"Repo number of closed issue tickets is {repo_stats.get('closed_tickets')}."
                )
            except Exception as e_closedtix:
                self.logger.error(
                    f"Error in checking closed issue numbers at {repo_name} and config path {config_path}: {e_closedtix}."
                )

            try:
                # get age of repo
                repo_age_days = dayssince.calc_days_since_repo_creation(
                    datetime.now(timezone.utc).replace(tzinfo=timezone.utc),
                    repo_name,
                    since_date=None,
                    return_in="whole_days",
                    config_path=config_path,
                )
                repo_stats.update({"repo_age_days": repo_age_days})
                self.logger.debug(
                    f"Repo age in days is {repo_stats.get('repo_age_days')}."
                )
            except Exception as e_age:
                self.logger.error(
                    f"Error in checking age of repo at {repo_name} with config path {config_path}: {e_age}."
                )

            # get license type
            try:
                license_type = repo_con.get("license")

                if license_type is not None:
                    license_type = license_type["spdx_id"]

                repo_stats.update({"repo_license": license_type})
                self.logger.debug(
                    f"Repo license type is {repo_stats.get('repo_license')}."
                )

            except Exception as e_license:
                self.logger.error(
                    f"Error in checking license of repo at {repo_name} with config path {config_path}: {e_license}."
                )

            # is repo accessible?
            try:
                repo_vis = repo_con.get("visibility")
                if repo_vis == "public":
                    repo_visibility = True
                else:
                    repo_visibility = False
                repo_stats.update({"repo_visibility": repo_visibility})
                self.logger.debug(
                    f"Repo visibility (~publicness) is {repo_stats.get('repo_visibility')}."
                )

            except Exception as e_visibility:
                self.logger.error(
                    f"Error in checking visibility of repo at {repo_name} with config path {config_path} - repo_con.get('visibility' returns {repo_con.get('visibility')} :{e_visibility}."
                )

            # does repo contain code
            try:
                # repo languages include: python, (C, C++), (shell?, R?, FORTRAN?)
                languages_url = f"https://api.github.com/repos/{repo_name}/languages"
                api_response = s.get(languages_url, headers=headers)

                languages = (
                    api_response.json().keys()
                )  # returns a dict_keys rather than anything cleverer

                if len(languages) == 0:
                    repo_stats.update({"repo_language": "None"})
                elif "Python" or "C" or "C++" or "Shell" in languages:
                    repo_stats.update({"repo_language": languages})
                else:
                    repo_stats.update({"repo_language": "other"})
                self.logger.debug(
                    f"Repo language is {repo_stats.get('repo_language')}."
                )

            except Exception as e_lingo:
                self.logger.error(
                    f"Error in checking language of repo at {repo_name} with config path {config_path}: {e_lingo}."
                )

        else:
            repo_stats.update({"issues_enabled": None})
            repo_stats.update({"repo_is_fork": None})
            repo_stats.update({"devs": None})
            repo_stats.update({"total_commits_last_year": None})
            repo_stats.update({"has_PRs": None})
            repo_stats.update({"last_PR_update": None})
            repo_stats.update({"open_tickets": None})
            repo_stats.update({"closed_tickets": None})
            repo_stats.update({"repo_age_days": None})
            repo_stats.update({"repo_license": None})
            repo_stats.update({"repo_visibility": None})
            repo_stats.update({"repo_language": None})
            self.logger.error(
                f"404 error in connecting to {repo_name}; filling all stats with None"
            )

        self.logger.info(f"Stats for {repo_name}: {repo_stats}")
        self.logger.debug(f"Returned stats object has {len(repo_stats)} categories.")
        return repo_stats


# this bit
if __name__ == "__main__":
    """
    Run summarise_repo_stats() from terminal on supplied repo name.
    """
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/summarise_repo_stats_logs.txt",
    )

    repo_summariser = RepoStatsSummariser(logger)

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    else:
        raise IndexError("Please enter a repo_name.")

    if "github" in repo_name:
        repo_name = name_clean.repo_name_clean(repo_name)

    output_stats = {}
    # run summarise_repo_stats() on repo_name.
    try:
        output_stats = repo_summariser.summarise_repo_stats(
            repo_name=repo_name, config_path="githubanalysis/config.cfg", per_pg=1
        )
        logger.info(f"Stats for repo {repo_name} summarised as: {output_stats}.")
    except Exception as e:
        logger.error(f"Exception while running summarise_repo_stats(): {e}")
