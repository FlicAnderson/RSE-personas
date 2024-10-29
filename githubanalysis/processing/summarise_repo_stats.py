"""Summarise key stats for GitHub repository."""

import sys
import pandas as pd
import datetime
from datetime import timezone
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.analysis.calc_days_since_repo_creation as dayssince


class RepoStatsSummariser:
    logger: logging.Logger
    config_path: str
    in_notebook: bool
    current_date_info: str
    sanitised_repo_name: str
    repo_name: str
    write_read_location: str
    # shoutout to @dk949 for advice and patient explanation on using Classes for fun & profit

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        write_read_location: str,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/summarise_repo_stats_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name
        self.write_read_location = write_read_location
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

    def summarise_repo_stats(self, repo_name: str):
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
        :rtype: dict

        Examples:
        ----------
        >>> summarise_repo_stats(repo_name='riboviz/riboviz')
        {'repo_name': 'riboviz/riboviz',
        'initial_HTTP_code': 200,
        'issues_enabled': True,
        'repo_is_fork': False,
        'devs': 23,
        'total_commits_last_year': 0,
        'has_PRs': True,
        'last_PR_update': datetime.datetime(2023, 4, 24, 8, 37, 56, tzinfo=datetime.timezone.utc),
        'open_tickets': 167,
        'closed_tickets': 315,
        'repo_age_days': 1991,
        'repo_license': 'Apache-2.0',
        'repo_visibility': True,
        'repo_language': dict_keys(['Python', 'R', 'Nextflow', 'Shell', 'Makefile', 'Batchfile'])}
        """

        # create output dict to update with stats:
        repo_stats = {}

        # get repo_name gh connection:
        repo_stats.update({"repo_name": repo_name})
        # self.logger.debug(f"Repo name is {repo_name}")

        base_repo_url = "https://api.github.com/repos"
        connect_to = f"{base_repo_url}/{repo_name}"

        self.logger.info(f"getting json via request url {connect_to}.")

        api_response = run_with_retries(
            fn=lambda: raise_if_response_error(
                api_response=self.s.get(url=connect_to, headers=self.headers),
                repo_name=self.repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        assert api_response.ok, f"API response is: {api_response}"

        self.logger.info(
            f"API response at initial connection to {repo_name} is {api_response}"
        )
        self.logger.info(
            f"API response at initial connection to {repo_name} for request {api_response.url} is {api_response}."
        )

        api_status = api_response.status_code

        repo_stats.update({"initial_HTTP_code": api_status})

        # if api_response.status_code == 404:
        #     self.logger.error(
        #         f"404 error in connecting to {repo_name}. Possibly this repo has been deleted or made private?"
        #     )
        # if api_response.status_code == 401:
        #     self.logger.error(
        #         f"401 (unauthorized) error in connecting to {repo_name}. Is your GitHub Personal Authentication Token valid and config.cfg file correctly formatted?"
        #     )
        # self.logger.error(
        #     f"Error in setting up repo connection with repo name {repo_name} and config path {config_path}."
        # )

        if api_response.status_code != 404:
            try:
                # issue tickets enabled y/n:
                if api_response.json().get("has_issues"):
                    repo_stats.update(
                        {"issues_enabled": api_response.json().get("has_issues")}
                    )
                else:
                    self.logger.debug(
                        f"GitHub repository {repo_name} does not have issues enabled."
                    )
                    repo_stats.update(
                        {"issues_enabled": api_response.json().get("has_issues")}
                    )

                self.logger.debug(
                    f"Repo issues enabled is {repo_stats.get('issues_enabled')}"
                )
            except Exception as e_tixenabled:
                self.logger.error(
                    f"Error in checking issues enabled with repo name {repo_name} and config path {self.config_path}: {e_tixenabled}."
                )

            # get stats:

            # get license type

            license_type = api_response.json().get("license")

            if license_type is not None:
                license_type = license_type["spdx_id"]

            repo_stats.update({"repo_license": license_type})
            self.logger.debug(f"Repo license type is {repo_stats.get('repo_license')}.")

            self.logger.error(
                f"Error in checking license of repo at {repo_name} with config path {self.config_path}."
            )

            # is repo accessible?
            repo_vis = api_response.json().get("visibility")
            if repo_vis == "public":
                repo_visibility = True
            else:
                repo_visibility = False
            repo_stats.update({"repo_visibility": repo_visibility})
            self.logger.debug(
                f"Repo visibility (~publicness) is {repo_stats.get('repo_visibility')}."
            )

            self.logger.error(
                f"Error in checking visibility of repo at {repo_name} with config path {self.config_path} - api_response.json().get('visibility') returns {api_response.json().get('visibility')}."
            )

            # is the repo a fork of something else?
            api_response.json().get("fork")
            if api_response.json().get("fork"):
                repo_stats.update({"repo_is_fork": api_response.json().get("fork")})
            else:
                repo_stats.update({"repo_is_fork": api_response.json().get("fork")})
            self.logger.debug(f"Repo is a fork: {repo_stats.get('repo_is_fork')}")

            self.logger.debug(
                f"Error in checking whether repo is a fork at repo name {repo_name} and config path {self.config_path}."
            )

            # count number of devs (contributors; including anonymous contribs* )
            contribs_url = f"https://api.github.com/repos/{repo_name}/contributors?per_page=1&anon=1"

            self.logger.info(f"getting json via request url {contribs_url}.")
            contributors_api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=contribs_url, headers=self.headers),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            assert (
                contributors_api_response.ok
            ), f"API response is: {contributors_api_response}"

            total_contributors = 1  # repo created by 1 person minimum; don't need to update unless there's more than one page (@ 1x person per page)

            if contributors_api_response.ok:
                contrib_links = contributors_api_response.links
                if "last" in contrib_links:
                    contrib_links_last = contrib_links["last"]["url"].split("&page=")[1]
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

                self.logger.error(
                    f"Error in checking number of contributors with repo name {repo_name} and config path {self.config_path}: API response: {contributors_api_response}"
                )

            # does repo contain code
            # repo languages include: python, (C, C++), (shell?, R?, FORTRAN?)
            languages_url = f"https://api.github.com/repos/{repo_name}/languages"
            # languages_api_response = s.get(languages_url, headers=headers)
            self.logger.info(f"getting json via request url {languages_url}.")
            languages_api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=languages_url, headers=self.headers),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            assert (
                languages_api_response.ok
            ), f"API response is: {languages_api_response}"

            languages = (
                languages_api_response.json().keys()
            )  # returns a dict_keys rather than anything cleverer

            if len(languages) == 0:
                repo_stats.update({"repo_language": "None"})
            elif "Python" or "C" or "C++" or "Shell" in languages:
                repo_stats.update({"repo_language": languages})
            else:
                repo_stats.update({"repo_language": "other"})
            self.logger.debug(f"Repo language is {repo_stats.get('repo_language')}.")

            self.logger.error(
                f"Error in checking language of repo at {repo_name} with config path {self.config_path}."
            )

            # count total commits in last year
            # Do something sensible re: no commits in last year returned TODO
            base_commit_stats_url = (
                f"https://api.github.com/repos/{repo_name}/stats/commit_activity"
            )

            self.logger.info(f"getting json via request url {base_commit_stats_url}.")
            stats_api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(
                        url=base_commit_stats_url, headers=self.headers, timeout=10
                    ),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            assert stats_api_response.ok, f"API response is: {stats_api_response}"

            self.logger.debug(
                f"API response for getting total commits in year: {stats_api_response}"
            )

            total_commits_df = pd.DataFrame(stats_api_response.json())
            total_commits_1_year = total_commits_df["total"].sum()

            self.logger.error(
                f"Failed trying to calculate the sum of commits in 1 year for repo {repo_name}."
            )
            repo_stats.update({"total_commits_last_year": total_commits_1_year})
            self.logger.debug(
                f"Repo total commits last year is {repo_stats.get('total_commits_last_year')}."
            )
            self.logger.error(
                f"Error in checking commits in last year at {repo_name} and config path {self.config_path}. API response: {stats_api_response}"
            )

            # date of most recently updated PR:
            per_pg = 1
            state = "all"
            sort = "updated"
            direction = "desc"
            params_string = (
                f"?per_pg={per_pg}&state={state}&sort={sort}&direction={direction}"
            )

            PRs_url = f"https://api.github.com/repos/{repo_name}/pulls{params_string}"

            self.logger.info(f"getting json via request url {PRs_url}.")
            PRs_api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=PRs_url, headers=self.headers),
                    repo_name=self.repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            assert PRs_api_response.ok, f"API response is: {PRs_api_response}"

            PRs_bool = None
            last_PR_updated = None

            if PRs_api_response.ok:
                self.logger.debug(
                    f"API response for getting PRs info: {PRs_api_response}"
                )

                try:
                    assert len(PRs_api_response.json()) != 0, "No json therefore no PRs"
                    last_PR_update = PRs_api_response.json()[0][
                        "updated_at"
                    ]  # 0th(1st) for latest update as sorted desc.
                    date_format = "%Y-%m-%dT%H:%M:%S%z"
                    last_PR_updated = datetime.datetime.strptime(
                        last_PR_update, date_format
                    )
                    # as datetime w/ UTC timezone awareness(last_PR_update)
                    PRs_bool = True
                except:
                    self.logger.debug(
                        f"No PRs found for repo {repo_name}; setting PRs_bool to False and last_PR_updated to None."
                    )
                    PRs_bool = False
                    last_PR_updated = None
            else:
                PRs_api_response.raise_for_status()

            repo_stats.update({"has_PRs": PRs_bool})
            self.logger.debug(f"Repo PRs is {repo_stats.get('has_PRs')}.")
            repo_stats.update({"last_PR_update": last_PR_updated})
            self.logger.debug(
                f"Repo last PR update is {repo_stats.get('last_PR_update')}."
            )
            self.logger.error(
                f"Error in checking commits in last year at {repo_name} and config path {self.config_path}"
            )

            # count open issue tickets
            if repo_stats.get("issues_enabled"):
                state = "open"
                issues_url = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=1"

                self.logger.info(f"getting json via request url {issues_url}.")
                issues_api_response = run_with_retries(
                    fn=lambda: raise_if_response_error(
                        api_response=self.s.get(url=issues_url, headers=self.headers),
                        repo_name=self.repo_name,
                        logger=self.logger,
                    ),
                    logger=self.logger,
                )
                assert issues_api_response.ok, f"API response is: {issues_api_response}"

                if issues_api_response.ok:
                    issue_links = issues_api_response.links
                    if "last" in issue_links:
                        issue_links_last = issue_links["last"]["url"].split("&page=")[1]
                        open_issues = int(issue_links_last)
                        repo_stats.update({"open_tickets": open_issues})
                    else:
                        open_issues = 0
                        repo_stats.update({"open_tickets": open_issues})
            else:
                open_issues = 0
                repo_stats.update({"open_tickets": open_issues})

            self.logger.debug(
                f"Repo number of open issue tickets is {repo_stats.get('open_tickets')}."
            )

            self.logger.error(
                f"Error in checking open issue numbers at {repo_name} and config path {self.config_path}."
            )

            # count closed issue tickets
            try:
                if repo_stats.get("issues_enabled"):
                    state = "closed"
                    issues_url = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=1"

                    self.logger.info(f"getting json via request url {issues_url}.")
                    clsd_issues_api_response = run_with_retries(
                        fn=lambda: raise_if_response_error(
                            api_response=self.s.get(
                                url=issues_url, headers=self.headers
                            ),
                            repo_name=self.repo_name,
                            logger=self.logger,
                        ),
                        logger=self.logger,
                    )
                    assert (
                        clsd_issues_api_response.ok
                    ), f"API response is: {clsd_issues_api_response}"

                    if clsd_issues_api_response.ok:
                        issue_links = clsd_issues_api_response.links
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

                self.logger.debug(
                    f"Repo number of closed issue tickets is {repo_stats.get('closed_tickets')}."
                )
            except Exception as e_closedtix:
                self.logger.error(
                    f"Error in checking closed issue numbers at {repo_name} and config path {self.config_path}: {e_closedtix}."
                )
                # get age of repo
                repo_age_days = dayssince.calc_days_since_repo_creation(
                    datetime.datetime.now(timezone.utc).replace(tzinfo=timezone.utc),
                    repo_name,
                    since_date=None,
                    return_in="whole_days",
                    config_path=self.config_path,
                )
                repo_stats.update({"repo_age_days": repo_age_days})
                self.logger.debug(
                    f"Repo age in days is {repo_stats.get('repo_age_days')}."
                )

                self.logger.error(
                    f"Error in checking age of repo at {repo_name} with config path {self.config_path}."
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
