import pandas as pd
from pathlib import Path


def read_interactions(
    interactions_file: Path,
    repo_list: list[str],
    logger,
) -> pd.DataFrame:
    """
    READS in .csv file of interactions of specific type (commits | issues (inc PRs) | code reviews)
    then SUBSETS these to discard any rows from repos NOT in the repo_list;
    returns the remaining in-list repos' interactions data of this type.
    """
    # READ IN DATA as df
    logger.info(
        f"Attempting to read in: {interactions_file}; this could take some SECONDS if it's a large file"
    )
    try:
        interactions_df = pd.read_csv(
            filepath_or_buffer=interactions_file,
            header=0,
            low_memory=False,
            dtype=object,
        )
        assert not interactions_df.empty, (
            "Read-in interactions df is empty but should not be."
        )
        assert interactions_df is not None, (
            "interactions_df is None, this is bad. Check the file {interactions_file}"
        )
        logger.debug(f"Columns for interactions_df are: {interactions_df.columns}")
    except:
        logger.error(f"Problem loading in interactions from file {interactions_file}")
        raise RuntimeError(
            f"interactions read in not working somehow for: {interactions_file}"
        )

    # subset df from file into the following repos' data only:
    # repo_name column value in repo_list e.g. df[df['A'].isin([3, 6])]
    logger.info(
        f"Length of interactions_df BEFORE subsetting to only repos in repo_list is: {len(interactions_df)}"
    )
    logger.info(
        f"Number of unique repos in interactions_df BEFORE subsetting to only repos in repo_list is: {interactions_df.repo_name.nunique()}"
    )
    interactions_df = (
        interactions_df[  # SUBSET DF TO ONLY THOSE ROWS WHERE REPO_NAME IN REPO_LIST
            interactions_df["repo_name"].isin(repo_list)
        ]
    )
    logger.info(
        f"Length of interactions_df AFTER subsetting to only repos in repo_list is: {len(interactions_df)}"
    )
    logger.info(
        f"Number of unique repos in interactions_df AFTER subsetting to repo_list repos is: {interactions_df.repo_name.nunique()}"
    )
    return interactions_df
