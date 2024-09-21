"""Get all data from all pages of issues for a GitHub repo."""

import sys
import os
import pandas as pd
import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.processing.repo_name_clean as name_clean


class IssueGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_all_pages_issues_logs.txt",
            )
        else:
            self.logger = logger

    def get_all_pages_issues(
        self,
        repo_name,
        config_path="githubanalysis/config.cfg",
        out_filename="all-issues",
        write_out_location="data/",
        issue_state="all",
    ):
        """
        Obtains all fields of data from all pages for a given github repo `repo_name`.
        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
        :type: str
        :param out_filename: filename suffix indicating issues content (Default: 'issues')
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :param issue_state: one of 'open', 'closed' or 'all'. GitHub issue API status options. Default: 'all'
        :type: str
        :returns: `all_issues` pd.DataFrame containing 30 fields per issue for given repo `repo_name`.
        :type: DataFrame

        Examples:
        ----------
        $ python githubanalysis/processing/get_all_pages_issues.py 'Dallinger/Dallinger'

        INFO:Using commandline argument Dallinger/Dallinger as repo name to retrieve GH issues for. Entered as: Dallinger/Dallinger
        INFO:Number of issues returned for repo Dallinger/Dallinger is 6207.
        INFO:There are 344 open issues (~6%) and 5863 closed issues (~94%).

        $ python githubanalysis/processing/get_all_pages_issues.py 'sizespectrum/mizer'
        INFO:Using commandline argument sizespectrum/mizer as repo name to retrieve GH issues for. Entered as: sizespectrum/mizer
        INFO:>> Running issue grab for repo sizespectrum/mizer, in page 1 of 3.
        INFO:>> Running issue grab for repo sizespectrum/mizer, in page 2 of 3.
        INFO:>> Running issue grab for repo sizespectrum/mizer, in page 3 of 3.
        INFO:Number of issues returned for repo sizespectrum/mizer is 281.
        INFO:There are 47 open issues (~17%) and 234 closed issues (~83%).
        """

        # get repo_name from commandline if given (accept commandline input)
        if len(sys.argv) == 2:
            repo_name = sys.argv[1]  # use second argv (user-provided by commandline)

            if not isinstance(repo_name, str):
                raise TypeError(
                    "Ensure argument is repository name in string format (e.g. 'repo-owner/repo-name')"
                )

            self.logger.info(
                f"Using commandline argument {repo_name} as repo name to retrieve GH issues for. Entered as: {sys.argv[1]}"
            )
        else:
            self.logger.debug(f"Repo name is {repo_name}. Getting issues.")

        # write-out file setup
        # get date for generating extra filename info
        current_date_info = datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        write_out = f"{write_out_location}{out_filename}_{sanitised_repo_name}"
        write_out_extra_info = f"{write_out}_{current_date_info}.csv"

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

        # create empty df to store issues data
        all_issues = pd.DataFrame()

        # count open issue tickets
        try:
            page = 1  # try first page only
            state = issue_state
            pulls = True  # DO NOT include PRs here
            issues_url = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=100&pulls={pulls}&page={page}"
            # per_page=30 by default on GH, set to max
            # default of 'state' is 'open' issues only

            api_response = s.get(url=issues_url, headers=headers)

        except Exception as e_connect:
            if api_response.status_code == 404:
                self.logger.error(
                    f"404 error in connecting to {repo_name}. Possibly this repo has been deleted or made private?"
                )
            self.logger.error(
                f"Error in setting up repo connection with repo name {repo_name} and config path {config_path}: {e_connect}."
            )

        if api_response.status_code != 404:
            self.logger.debug(f"Getting issues for repo {repo_name}.")

            issue_links = api_response.links
            store_pg = pd.DataFrame()
            pg_count = 0

            try:
                if "last" in issue_links:
                    issue_links_last = issue_links["last"]["url"].split("&page=")[1]
                    pages_issues = int(issue_links_last)

                    pg_range = range(1, (pages_issues + 1))

                    for i in pg_range:
                        pg_count += 1
                        self.logger.info(
                            f">> Running issue grab for repo {repo_name}, in page {pg_count} of {pages_issues}."
                        )
                        issues_query = f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page=100&pulls={pulls}&page={i}"
                        api_response = s.get(url=issues_query, headers=headers)
                        json_pg = api_response.json()
                        store_pg = pd.DataFrame.from_dict(
                            json_pg
                        )  # convert json to pd.df
                        # using pd.DataFrame.from_dict(json) instead of pd.read_json(url) because otherwise I lose rate handling

                        if len(store_pg.index) > 0:
                            store_pg["assigned_devs"] = store_pg[
                                ["assignees"]
                            ].applymap(
                                lambda x: [x.get("login") for x in x]
                            )  # use detail from get_issue_assignees() to create new column
                            try:
                                if "pull_request" in store_pg.columns:
                                    store_pg["is_PR"] = store_pg[
                                        "pull_request"
                                    ].notna()  # pull out PR info into boolean column; blank cells = NaN. This checks for NOT NA so True if PR.
                                else:
                                    store_pg["is_PR"] = False
                            except Exception as e_noPRs:
                                self.logger.error(
                                    f"Error trying to generate additional boolean is_PR column from data: {e_noPRs}."
                                )

                            # write out 'completed' page of issues as df to csv via APPEND (use added date filename with reponame inc)
                            store_pg.to_csv(
                                write_out_extra_info,
                                mode="a",
                                index=True,
                                header=not os.path.exists(write_out_extra_info),
                            )
                            all_issues = pd.concat(
                                [all_issues, store_pg],
                            )  # append this page (df) to main issues df
                        store_pg = pd.DataFrame()  # empty the df of last page

                else:  # there's no next page, grab all on this page and proceed.
                    pg_count += 1
                    self.logger.debug(f"getting json via request url {issues_url}.")
                    json_pg = api_response.json()
                    if not json_pg:  # check emptiness of result.
                        self.logger.debug(
                            "Result of api_response.json() is empty list."
                        )
                        self.logger.error(
                            "Result of API request is an empty json. Error - cannot currently handle this result nicely."
                        )
                    store_pg = pd.DataFrame.from_dict(json_pg)

                    if len(store_pg.index) > 0:
                        store_pg["assigned_devs"] = store_pg[["assignees"]].applymap(
                            lambda x: [x.get("login") for x in x]
                        )  # use detail from get_issue_assignees() to create new column
                        try:
                            if "pull_request" in store_pg.columns:
                                store_pg["is_PR"] = store_pg[
                                    "pull_request"
                                ].notna()  # pull out PR info into boolean column; blank cells = NaN. This checks for NOT NA so True if PR.
                            else:
                                store_pg["is_PR"] = False
                        except Exception as e_noPRs:
                            self.logger.error(
                                f"Error trying to generate additional boolean is_PR column from data: {e_noPRs}."
                            )

                    all_issues = store_pg
                    # write out the page content to csv via APPEND (use added date filename)
                    all_issues.to_csv(
                        write_out_extra_info,
                        mode="a",
                        index=True,
                        header=not os.path.exists(write_out_extra_info),
                    )

                self.logger.debug(
                    f"Total number of issues grabbed is {len(all_issues.index)} in {pg_count} page(s)."
                )
                self.logger.debug(
                    f"Issues data written out to file for repo {repo_name} at {write_out_extra_info}."
                )

                if all_issues["state"].nunique() > 1:
                    self.logger.debug(
                        f"There are {all_issues.state.value_counts().open} open issues (~{round(all_issues.state.value_counts(normalize=True).open*100)}%) and {all_issues.state.value_counts().closed} closed issues (~{round(all_issues.state.value_counts(normalize=True).closed*100)}%)."
                    )
                else:
                    if (
                        all_issues["state"][0] == "closed"
                    ):  # if we have only closed, set open to 0
                        self.logger.debug(
                            f"There are 0 open issues (0%) and {all_issues.state.value_counts().closed} closed issues (~{round(all_issues.state.value_counts(normalize=True).closed*100)}%)."
                        )
                    elif all_issues["state"][0] == "open":  # do vice versa!
                        self.logger.debug(
                            f"There are {all_issues.state.value_counts().open} open issues (~{round(all_issues.state.value_counts(normalize=True).open*100)}%) and 0 closed issues (0)."
                        )
                    else:
                        self.logger.error("Error in the 'state' column of issues df.")

                if all_issues["is_PR"].nunique() > 1:
                    self.logger.debug(
                        f"There are {all_issues['is_PR'].value_counts()[False]} issue tickets (~{round(all_issues['is_PR'].value_counts(normalize=True)[False]*100)}%) and {all_issues['is_PR'].value_counts()[True]} pull requests (~{round(all_issues['is_PR'].value_counts(normalize=True)[True]*100)}%)."
                    )
                else:
                    if not all_issues["is_PR"][0]:
                        self.logger.debug(
                            f"There are {all_issues['is_PR'].value_counts()[False]} issue tickets and (~{round(all_issues['is_PR'].value_counts(normalize=True)[False]*100)}%) and 0 (0%) issues that are PRs."
                        )
                    elif all_issues["is_PR"][0] is True:
                        self.logger.debug(
                            f"There are 0 issue tickets (0%) and {all_issues['is_PR'].value_counts()[True]} pull requests (~{round(all_issues['is_PR'].value_counts(normalize=True)[True]*100)}%)."
                        )
                    else:
                        self.logger.error("Error in 'is_PR' field of issues df.")

            except Exception as e_issues:
                self.logger.error(
                    f"Something failed in getting issues for repo {repo_name}: {e_issues}"
                )

        #     # check all important columns are present in the df.
        #     wanted_cols = ['url', 'repository_url', 'labels', 'number', 'title', 'state',
        #                 'assignee', 'assignees', 'created_at', 'closed_at', 'pull_request']
        #     try:
        #         assert all(item in all_issues.columns for item in wanted_cols)
        #     except AssertionError as err:
        #         print(f"column {[x for x in all_issues.columns if x not in wanted_cols]} not present in all_issues df; {err}")

        #     all_issues['created_at'] = pd.to_datetime(all_issues['created_at'], yearfirst=True, utc=True,
        #                                             format='%Y-%m-%dT%H:%M:%S%Z')
        #     all_issues['closed_at'] = pd.to_datetime(all_issues['closed_at'], yearfirst=True, utc=True,
        #                                             format='%Y-%m-%dT%H:%M:%S%Z')

        #     all_issues['repo_name'] = repo_name

        return all_issues

        # relevant fields: 'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
        # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url',
        # ... 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)


# this bit
if __name__ == "__main__":
    """
    get issues for specific GH repo. 
    gather into df 
    (TODO: writeout to csv)
    """
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/get_all_pages_issues_logs.txt",
    )

    issues_getter = IssueGetter(logger)

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    else:
        raise IndexError("Please enter a repo_name.")

    if "github" in repo_name:
        repo_name = name_clean.repo_name_clean(repo_name)

    issues_df = pd.DataFrame()

    # run the main function to get the issues!
    try:
        issues_df = issues_getter.get_all_pages_issues(
            repo_name=repo_name, config_path="githubanalysis/config.cfg"
        )
        if len(issues_df) != 0:
            logger.info(
                f"Number of issues returned for repo {repo_name} is {len(issues_df.index)}."
            )
            logger.info(
                f"There are {issues_df.state.value_counts().open} open issues (~{round(issues_df.state.value_counts(normalize=True).open*100)}%) and {issues_df.state.value_counts().closed} closed issues (~{round(issues_df.state.value_counts(normalize=True).closed*100)}%)."
            )
            logger.info(
                f"There are {issues_df['is_PR'].value_counts()[False]} issue tickets (~{round(issues_df['is_PR'].value_counts(normalize=True)[False]*100)}%) and {issues_df['is_PR'].value_counts()[True]} pull requests (~{round(issues_df['is_PR'].value_counts(normalize=True)[True]*100)}%)."
            )
        else:
            logger.warning(
                "Getting issues did not work, length of returned records is zero."
            )
    except Exception as e:
        logger.error(
            f"Exception while running get_all_pages_issues() on repo {repo_name}: {e}"
        )

    # generate filename and try to read file in for comparison.
    total_issues = pd.DataFrame()
    try:
        current_date_info = datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        issues_file = "data/all-issues"
        issues_file_extra_info = (
            f"{issues_file}_{sanitised_repo_name}_{current_date_info}.csv"
        )
        total_issues = pd.read_csv(issues_file_extra_info, header=0)
    except Exception as e:
        logger.error(
            f"There's been an exception while trying to read back in data generated by get_all_pages_issues() from {issues_file_extra_info}: {e}"
        )

    try:
        assert (
            len(issues_df.index) == len(total_issues.index)
        ), f"WARNING! Lengths of returned df ({len(issues_df)}) vs df read in from file ({len(total_issues)}) DO NOT MATCH. Did you append too many records to the gh_urls file??"
    except AssertionError as e:
        logger.error(
            f"The outputs of running the function and reading back in data DO NOT MATCH; {e}"
        )
