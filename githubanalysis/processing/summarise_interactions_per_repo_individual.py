import pandas as pd
import traceback
from pathlib import Path
import datetime
import logging
import pandas.api.types as ptypes


def summarise_interactions_per_repo_individual(
    all_types_interactions: pd.DataFrame,
    logger: logging.Logger,
    current_date_info: str,
    data_location: Path,
) -> pd.DataFrame:
    """
    MAIN INTERACTIONS CALCULATION AND SUMMARISING FUNCTION!

    This takes df of 'stacked' interactions data: all_types_interactions
    (interaction-per-line, multi lines per repo-individuial, multi repos)

    then:
     - drops rows with missing data (e.g. where gh_username value is missing as cannot calculate with missing repo-individuals ; missing repo_name; missing datetime_day' etc)
     - debugging / logging checks and reporting of Ns of rows deducted for missing data, date data types, etc
     - pre-calculation write-out as: combined_interactions_data_x....csv
     - create 'status_df': line-per-repo-individual summary df to hold calc'd data
     and in status_df:
     - calculation FOR EACH REPO-INDIVIDUAL: difference between earliest interaction date and latest interaction date in dataset; add to status_df as 'interaction_period_days'
     - calculation of number (count) of interactions PER INTERACTION TYPE PER REPO-INDIVIDUAL (e.g. commits 5, issue_creation 4, code_reviewed 2, etc); added to status_df
     - calculation of "interaction_days" (unique different days of interactions contributed of all sorts) PER REPO-INDIVIDUAL, added to status_df;
     - set any non-filled values in status_df to 0 as no interactions of those types were recorded
     - calculates net (raw N, and %) difference in issues (e.g. N created minus N closed and pc(%) created minus % closed)
     - (same as net difference in issues, but for pull requests)
     - calc total N of interactions of all sorts as "sum_n_interactions"
     - calc average N of interactions per interaction day as "mean_n_interactions_per_interaction_day" (= sum_N_interactions / N of interaction days)
     - generate "which_interactions": join strings of interaction_type together for all present interactions by repo_individual
     - calc "breadth_interactions" (Unique Interaction Types; N of different interaction types present for repo-individual)
     - calcs repo-individual's RC (% Repository Contribution) values for each CONTRIBUTION TYPE:
         - PR creation ("pc_pull_request_created")
         - PR closure ("pc_pull_request_closed")
         - commit creation ("pc_commit_created")
         - issue creation ("pc_issue_created")
         - issue closure ("pc_issue_closed")
         - reviews created ("pc_reviews_created")
        TODO: ??? ASSIGNMENT SHOULD GO HERE!!! ???
     - calcs repo-individual's RC (% Repository Contribution) of META INFO:
         - total number of interactions of ALL TYPES as "pc_sum_n_interactions"
         - calcs RC of all repository's unique interaction days as "pc_interaction_days"

    THEN returns status_df: a line-per-repo-individual summary df
    of each repo-individuals' contributions of all types!

    status_df has columns:
    [
        "repo_name",
        "gh_username",
        "code_reviewed",
        "commit_created",
        "issue_closed",
        "issue_created",
        "pull_request_closed",
        "pull_request_created",
        "interaction_days",
        "interaction_period_days",
        "created-closed_issues",
        "pc_created-closed_issues",
        "sum_n_interactions",
        "mean_n_interactions_per_interaction_day",
        "which_interactions",
        "breadth_interactions",
        "pc_pull_request_created",
        "pc_pull_request_closed",
        "pc_commit_created",
        "pc_issue_created",
        "pc_issue_closed",
        "pc_reviews_created",
        "pc_sum_n_interactions",
        "pc_interaction_days",
    ]
    """
    assert all_types_interactions is not None, (
        f"all_interactions_data should not be type None; type is: {type(all_types_interactions)}."
    )
    logger.info(
        f"At beginning of function summarise_interactions_per_repo_individual(), df 'all_types_interactions' shape is: {all_types_interactions.shape}."
    )
    # IDENTIFY NAs, esp @ gh_username
    logger.info(f"{all_types_interactions.columns = }")
    logger.info(
        f"NAs counted in gh_username cols: {all_types_interactions['gh_username'].isna().sum()}"
    )

    # # remove rows where gh_username is NaN/NA
    templen = len(all_types_interactions)
    all_types_interactions = all_types_interactions.dropna(subset="gh_username", axis=0)
    logger.info(
        f"Removed {templen - len(all_types_interactions)} missing GH_username rows"
    )

    # Gather MISSING data counts:
    n_all_before = len(all_types_interactions)
    n_gh_users = all_types_interactions["gh_username"].isna().sum()
    n_repos = all_types_interactions["repo_name"].isna().sum()
    n_missing_date = all_types_interactions["datetime_day"].isna().sum()

    logger.info(
        f"Filtering out rows including {n_gh_users + n_repos + n_missing_date} missing data elements: {n_repos} rows missing repo_names; {n_missing_date} rows missing date_time days."
    )

    # remove missing repo_name data, and rows with missing gh_usernames
    # AND with missing datetime_day values (NaT)
    all_types_interactions = all_types_interactions.dropna(
        subset=["gh_username", "repo_name", "datetime_day"]
    )
    n_after_drop = len(all_types_interactions)

    logger.info(
        f"Filtering out {n_all_before - n_after_drop} rows with missing data out of {n_all_before} rows in total."
    )
    logger.info(f"{n_after_drop} rows remaining.")

    logger.info(
        f"After removing missing data rows, `all_types_interactions` df contains {all_types_interactions.groupby(by=['repo_name', 'gh_username']).ngroups} repo-individuals from {all_types_interactions.groupby(by=['repo_name']).ngroups} repos."
    )

    # reasonably important writeout: combined issues + commits + reviews with missing data handled.
    writeout_combined = Path(
        data_location,
        f"combined_interactions_data_x{all_types_interactions.groupby('repo_name').ngroups}repos_x{all_types_interactions.groupby(['repo_name', 'gh_username']).ngroups}repo-indivds_{current_date_info}.csv",
    )
    logger.info(f"Writing out combined interactions as: {writeout_combined}.")
    all_types_interactions.to_csv(
        writeout_combined,
        header=True,
        index=False,
    )
    logger.debug(f"wrote out combined interactions file {writeout_combined}.")
    logger.info(
        "Now attempting calculation of timediffs to help calculate interaction_period."
    )
    try:
        all_types_interactions["datetime_day"] = pd.to_datetime(
            all_types_interactions["datetime_day"],
            # utc = False: this is the default, "inputs will not be coerced to UTC. Timezone-naive inputs will remain naive, while timezone-aware ones will keep their time offsets." Think this is best because we only have DAY not times as well
        )

        assert ptypes.is_datetime64_any_dtype(all_types_interactions["datetime_day"]), (
            "The column datetime_day is NOT a date type! This is BAD"
        )

        # pull out the number of days timediff between 1st and latest interactions
        timediff = (
            all_types_interactions.groupby(["repo_name", "gh_username"])[
                "datetime_day"
            ].max()
            - all_types_interactions.groupby(["repo_name", "gh_username"])[
                "datetime_day"
            ].min()
        )

    except Exception as e:
        tmp_errors = all_types_interactions["datetime_day"].isna()
        tmp_errors = all_types_interactions[tmp_errors]
        logger.error(
            f"Unexpected error during TIMEDIFF calculations, ({e}) traceback:\n{traceback.format_exc()}"
        )
        logger.error(
            f"error {e}: \n value_counts of types for datetime_day are: \n {all_types_interactions['datetime_day'].apply(lambda x: str(type(x))).value_counts(dropna=False)} \n"
        )
        logger.error(f"tmp_errors is: {tmp_errors}")
        tmp_errors.to_csv(
            Path(
                data_location,
                f"error_rows_interactions_data_{current_date_info}.csv",
            )
        )

        raise

    logger.debug(
        "completed timediff calculation: datetime_day max - datetime_day min by groups"
    )
    timediff = timediff.apply(
        lambda x: x + datetime.timedelta(days=1)
    )  # add 1 day so the time difference is inclusive of both first and last days (ie no zeroes!)
    timediff = timediff.apply(lambda x: x.days).reset_index()
    timediff = timediff.rename(columns={"datetime_day": "interaction_period_days"})
    logger.debug("rename timediff column as interaction_period_days")

    # pull interaction_types into separate columns, and add counts of each category into them
    status_df = (
        all_types_interactions.groupby(["repo_name", "gh_username", "interaction_type"])
        .agg(n_interactions=pd.NamedAgg(column="repo_name", aggfunc="count"))
        .pivot_table(
            values="n_interactions",
            index=["repo_name", "gh_username"],
            columns="interaction_type",
            fill_value=0,
        )
        .reset_index()
    )

    # count unique interaction_days per user:
    status_df["interaction_days"] = (
        all_types_interactions.groupby(by=["repo_name", "gh_username"])[
            ["datetime_day"]
        ]
        .nunique()
        .reset_index()["datetime_day"]
    )

    # to avoid unexpected behaviour, pre-drop rows where keys are null value:
    logger.info(
        f"Shape BEFORE dropping rows with missing values for repo_name or gh_username from status_df: {status_df.shape}"
    )
    status_df = status_df.dropna(subset=["repo_name", "gh_username"])
    logger.info(
        f"Shape AFTER dropping rows with missing values for repo_name or gh_username from status_df: {status_df.shape}"
    )

    logger.info(
        f"Shape BEFORE dropping rows with missing values for repo_name or gh_username from timediff: {timediff.shape}"
    )
    timediff = timediff.dropna(subset=["repo_name", "gh_username"])
    logger.info(
        f"Shape AFTER dropping rows with missing values for repo_name or gh_username from timediff: {timediff.shape}"
    )

    # join on 'interaction_period_days' column from timediff
    assert len(status_df) == len(timediff), (
        f"ERROR: lengths of statusdf and timediff are DIFFERENT, but this is NOT what we'd expect! status_df: {len(status_df)}, timediff: {len(timediff)}"
    )
    logger.info(f"Columns of status_df: {status_df.columns}")
    logger.info(f"Columns of timediff: {timediff.columns}")
    logger.info(
        f"INNER join (via pd.merge()) status_df and timediff on repo-individuals to obtain 'interaction_period_days' column from timediff; shape of status_df:{status_df.shape} shape of timediff: {timediff.shape}."
    )
    status_df = pd.merge(
        status_df,
        timediff,
        how="inner",  # JOIN TYPE: INNER: we assert both dfs are the same length so keys WILL match precisely.
        on=["repo_name", "gh_username"],
    )
    logger.info(
        f"NEW columns of status_df after merging in timediff info: {status_df.columns}"
    )
    # this merge is transferring the time period info ?
    logger.info(f"AFTER joining timediff and status_df: {status_df.shape}.")

    # setting values to 0 if they're not present
    # (ie weren't joined from other interactions sets where interactions weren't recorded):
    for col in [
        "commit_created",
        "issue_closed",
        "issue_created",
        "pull_request_created",
        "pull_request_closed",
        "code_reviewed",
        # "discussion_added",
    ]:
        if col not in status_df.columns:
            status_df.loc[:, col] = 0

    logger.info(
        "Calculating net interactions columns, sums, repository contributions, means etc..."
    )
    # create ratio of created:closed issues per user:
    status_df["created-closed_issues"] = (
        status_df["issue_created"] - status_df["issue_closed"]
    )

    # should not result in a divide by zero issue because no issues datafile exists if no issues in repo
    # (hopefully)
    status_df["pc_created-closed_issues"] = (
        status_df["issue_created"]
        / status_df.groupby("repo_name")["issue_created"].transform("sum")
    ) - (
        status_df["issue_closed"]
        / status_df.groupby("repo_name")["issue_closed"].transform("sum")
    ) * 100

    # calculate number of different interactions by each user:
    status_df["sum_n_interactions"] = (
        status_df["commit_created"]
        + status_df["issue_closed"]
        + status_df["issue_created"]
        + status_df["pull_request_created"]
        + status_df["pull_request_closed"]
        + status_df["code_reviewed"]
        # + status_df["discussion_added"]
    )

    # mean_n_interactions_per_interaction_days: sum of interactions ()all types) divide by number of unique interaction days
    status_df["mean_n_interactions_per_interaction_day"] = (
        status_df["sum_n_interactions"] / status_df["interaction_days"]
    )

    # gather text labels for which interactions were done by users:
    status_df["which_interactions"] = (
        all_types_interactions.groupby(by=["repo_name", "gh_username"])[
            ["interaction_type"]
        ]
        .agg(lambda x: ", ".join(list(map(str, set(x)))))
        .reset_index()["interaction_type"]
    )

    # get breadth of unique interactions :
    status_df["breadth_interactions"] = status_df.which_interactions.apply(
        lambda x: len(x.split())
    )

    # per-repo pc(pull_requests):
    status_df["pc_pull_request_created"] = (
        status_df["pull_request_created"]
        / status_df.groupby("repo_name")["pull_request_created"].transform("sum")
        * 100
    )

    status_df["pc_pull_request_closed"] = (
        status_df["pull_request_closed"]
        / status_df.groupby("repo_name")["pull_request_closed"].transform("sum")
        * 100
    )

    # per-repo sum(commits):
    status_df["pc_commit_created"] = (
        status_df["commit_created"]
        / status_df.groupby("repo_name")["commit_created"].transform("sum")
        * 100
    )

    # per-repo pc(opened issues):
    status_df["pc_issue_created"] = (
        status_df["issue_created"]
        / status_df.groupby("repo_name")["issue_created"].transform("sum")
        * 100
    )

    # per-repo pc(closed issues):
    status_df["pc_issue_closed"] = (
        status_df["issue_closed"]
        / status_df.groupby("repo_name")["issue_closed"].transform("sum")
        * 100
    )

    # RC (repo-contribution) of PR code reviews (PRCR):
    status_df["pc_reviews_created"] = (
        status_df["code_reviewed"]
        / status_df.groupby("repo_name")["code_reviewed"].transform("sum")
        * 100
    )

    # # RC (repo-contribution) of Issue Ticket Discussions (ITD):
    # status_df["pc_discussions"] = (
    #     status_df["discussion_added"]
    #     / status_df.groupby("repo_name")["discussion_added"].transform("sum")
    #     * 100
    # )

    # per-repo pc of total sum of n interactions:
    status_df["pc_sum_n_interactions"] = (
        status_df["sum_n_interactions"]
        / status_df.groupby("repo_name")["sum_n_interactions"].transform("sum")
        * 100
    )

    # per-repo pc of repo interaction_days:
    status_df["pc_interaction_days"] = (
        status_df["interaction_days"]
        / status_df.groupby("repo_name")["interaction_days"].transform("sum")
        * 100
    )

    logger.info(
        f"status_df being returned by summarise_interactions_per_repo_individual() has shape {status_df.shape} and columns: {status_df.columns}"
    )
    logger.info(
        f"status_df has {status_df.groupby(by=['repo_name', 'gh_username']).ngroups} repo-individuals from {status_df.groupby(by=['repo_name']).ngroups} repos."
    )
    return status_df
