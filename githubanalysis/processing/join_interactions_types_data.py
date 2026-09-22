import pandas as pd
import traceback
from pathlib import Path
import logging


def join_all_interactions(
    commits_interactions: pd.DataFrame,
    issues_interactions: pd.DataFrame,
    reviews_interactions: pd.DataFrame,
    # discussions_interactions: pd.DataFrame,
    logger: logging.Logger,
    current_date_info: str,
    data_location: Path,
) -> pd.DataFrame:
    """
    Function combines issues (+ PRs) and commits and reviews
    interactions and abridged timestamp data; returns df of this.

    Returned df is interaction-per-line with many lines per repo-individual and includes multiple repos.

    Returned df has columns:
    ['repo_name', 'gh_username', 'datetime_day', 'contribution', 'interaction_type']
    """
    pd.options.mode.copy_on_write = True
    # logger.debug(discussions_interactions.info())
    logger.debug(
        "Columns of issues, commits and reviews interactions dfs respectively:..."
    )
    logger.debug(issues_interactions.columns)
    logger.debug(commits_interactions.columns)
    logger.debug(reviews_interactions.columns)
    # logger.debug(discussions_interactions.columns)

    # assert "datetime_day" in discussions_interactions.columns, (
    #     "The datetime_day column is missing from discussions_interactions df; please fix, rename and retry"
    # )  # in case I forget to address this earlier.

    logger.info(
        f"PRE-CONCAT 'issues_interactions' df NAs counted in gh_username col: {issues_interactions['gh_username'].isna().sum()}"
    )
    filestr_iss = f"issues_interactions_x{len(issues_interactions)}interactions_x{issues_interactions.groupby(by=['repo_name']).ngroups}repos_x{issues_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{current_date_info}.csv"
    writeout_path_iss = Path(data_location, filestr_iss)
    issues_interactions.to_csv(writeout_path_iss, header=True, index=False)

    logger.info(
        f"PRE-CONCAT 'commits_interactions' df NAs counted in gh_username col: {commits_interactions['gh_username'].isna().sum()}"
    )
    filestr_cmt = f"commits_interactions_x{len(commits_interactions)}interactions_x{commits_interactions.groupby(by=['repo_name']).ngroups}repos_x{commits_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{current_date_info}.csv"
    writeout_path_cmt = Path(data_location, filestr_cmt)
    commits_interactions.to_csv(writeout_path_cmt, header=True, index=False)

    logger.info(
        f"PRE-CONCAT 'reviews_interactions' df NAs counted in gh_username col: {reviews_interactions['gh_username'].isna().sum()}"
    )
    filestr_rvw = f"review_interactions_x{len(reviews_interactions)}interactions_x{reviews_interactions.groupby(by=['repo_name']).ngroups}repos_x{reviews_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{current_date_info}.csv"
    writeout_path_rvw = Path(data_location, filestr_rvw)
    reviews_interactions.to_csv(writeout_path_rvw, header=True, index=False)

    # filestr_dsc = f"discussions_interactions_x{len(discussions_interactions)}interactions_x{discussions_interactions.groupby(by=['repo_name']).ngroups}repos_x{reviews_interactions.groupby(by=['repo_name', 'gh_username']).ngroups}repo-individs_{current_date_info}.csv"
    # writeout_path_dsc = Path(data_location, filestr_dsc)
    # discussions_interactions.to_csv(writeout_path_dsc, header=True, index=False)

    logger.debug(
        f"wrote out commits, issues and reviews interactions dfs to separate csv files: {writeout_path_cmt} and {writeout_path_iss} and {writeout_path_rvw}."
    )  # TODO: add discussion to this when implementing

    # JOIN ISSUES AND COMMITS AND REVIEWS DATA TOGETHER HERE:
    logger.info(
        "Attempting THE JOIN (outer join via concat): issues + commits + reviews..."
    )
    try:
        all_types_interactions = pd.concat(
            # CONCAT rather than merge, because the columns match exactly, and we're aiming for a LONG df of stacked interactions
            objs=[issues_interactions, commits_interactions, reviews_interactions],
            join="outer",  # outer join returns ALL rows, matching where possible, applying NaNs if not; KEEPS non-shared columns (V. IMP!)
        )
        logger.info(
            f"POST-CONCAT 'all_types_interactions' df NAs counted in gh_username col: {all_types_interactions['gh_username'].isna().sum()}"
        )
        writeout_path_tmp = Path(
            data_location,
            f"tmp_interactions_merge_{current_date_info}.csv",
        )
        all_types_interactions.to_csv(writeout_path_tmp, header=True, index=False)
        logger.info(f"Intermediate output of JOIN written out to {writeout_path_tmp}")
    except Exception as e:
        logger.error(
            f"Problem attempting to concatenate all types of interactions from issues, commits, reviews: {e}; "  # arguments were: {args}."
        )
        logger.error(
            f"Unexpected error with THE JOIN (issues + commits + reviews) via concat(), traceback:\n{traceback.format_exc()}"
        )
        raise

    logger.debug(
        "joined issues and commits and reviews interactions"
    )  # TODO: add discussions df to this when implementing
    return all_types_interactions
