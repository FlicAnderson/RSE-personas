"""Collate COMMITS datafiles, generate dataframes ready for analysis."""

from pathlib import Path
import datetime
import os
import re
import pandas as pd
import logging
import category_encoders as ce
from sklearn.preprocessing import OneHotEncoder

import utilities.get_default_logger as loggit


class PrepDataCommits:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path
    read_location: Path

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/pre-analysis_data_commits_prep.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.read_location = Path("data/" if not in_notebook else "../../data/")
        self.write_location = Path("data/" if not in_notebook else "../../data/")

    def process_commits(
        self,
        read_location: str | Path,
        write_location: str | Path,
    ) -> pd.DataFrame | None:
        """
        Pull in commits_cats_stats_ files from read_location folder (default: data/)
        Read in commits data per file (equivalent to per-repo).
        Create data aggregations per dev per repo; gather hattori/vasilescu commit cats data summaries
        Join dfs together to get aggregated commits info per dev and aggregated h/v cats data
        Reshuffle various df slices and joins to get good output formats
        Collate devs commits data; Write out devs commits data to csv
        Return devs commits data
        """
        start_time = datetime.datetime.now()

        repolist = [
            f
            for f in os.listdir(read_location)
            if re.match(r"(commits_cats_stats_).*(.csv)", f)
        ]
        logger.info("{repolist}")

        multirepo = pd.DataFrame()
        multirepo_commit_cats = pd.DataFrame()

        print(f"Currently processing {len(repolist)} repos' worth of commits")

        for repofile in repolist:
            logger.debug(f"{repofile}")
            tmplocat = f"{read_location}{repofile}"
            repo = pd.read_csv(tmplocat)
            logger.debug(f"{len(repo)}")  # this number is N of Commits per repo

            ce_OHE = ce.OneHotEncoder(
                cols=[
                    "hattori_lanza_size_cat",
                    "hattori_lanza_content_cat",
                    "vasilescu_category",
                ],
                use_cat_names=True,
                handle_unknown="value",
            )
            repo = ce_OHE.fit_transform(repo)

            tmpname = repo["repo_name"][0]

            tmpdf = pd.DataFrame(
                {
                    "repo_name": tmpname,
                    "author_username": list(
                        repo.groupby("author_username").size().keys()
                    ),
                    "n_commits": list(repo.groupby("author_username").size()),
                    "pc_repo_commits": (repo.groupby("author_username").size())
                    / len(repo)
                    * 100,
                    "median_n_files_changed": repo.groupby("author_username")[
                        ["n_files_changed"]
                    ].median()["n_files_changed"],
                    "mean_n_files": repo.groupby("author_username")[
                        ["n_files_changed"]
                    ].mean()["n_files_changed"],
                    "std_n_files_changed": repo.groupby("author_username")[
                        ["n_files_changed"]
                    ].std()["n_files_changed"],
                    "median_n_changes_changed": repo.groupby("author_username")[
                        ["n_changes"]
                    ].median()["n_changes"],
                    "mean_n_changes": repo.groupby("author_username")[
                        ["n_changes"]
                    ].mean()["n_changes"],
                    "std_n_changes_changed": repo.groupby("author_username")[
                        ["n_changes"]
                    ].std()["n_changes"],
                    # "hattori_lanza_content_cat_reengineering_TEST": repo.groupby("author_username")[['hattori_lanza_content_cat_reengineering']].sum()['hattori_lanza_content_cat_reengineering'],
                }
            )
            logger.debug(f"repo {tmpname} has {len(tmpdf)} devs")

            tmpdf["n_of_commit_creators"] = len(tmpdf)

            # append tmpdf (current repo stats) to other repos' df
            multirepo = pd.concat([multirepo, tmpdf], axis=0, ignore_index=True)
            logger.debug("...")

            # create df of summed columns per dev-row, to get totals of Vasilescu and Hattori-Lanza categories amongst dev's commits
            commit_cats = repo.groupby(
                ["author_username", "repo_name"], as_index=False
            ).sum(numeric_only=True)
            multirepo_commit_cats = pd.concat(
                [multirepo_commit_cats, commit_cats], axis=0, ignore_index=True
            )  # join this repo to rest

            logger.info(
                f"Repo: {tmpname} has length of commit_cats: {len(commit_cats)}"
            )
            logger.info(
                f"Repo: {tmpname} has length of multirepo_commit_cats: {len(multirepo_commit_cats)}"
            )
            logger.info(f"Repo: {tmpname} has length of multirepo: {len(multirepo)}")
            logger.debug("-------------")

        # return multirepo
        # merge Vasilescu/Hattori-Lanza data on to other stats info
        commits_multirepo = pd.merge(
            left=multirepo,
            right=multirepo_commit_cats,
            how="left",
            left_on=["author_username", "repo_name"],
            right_on=["author_username", "repo_name"],
            indicator=False,
        )

        assert (
            len(multirepo) == len(multirepo_commit_cats)
        ), f"multirepo and the categories data in multirepo_commit_cats don't match length: {len(multirepo)} vs {len(multirepo_commit_cats)}"
        # #removing assert as they aren't the same length, think it's fine this way tbh, avoids cruft

        commits_multirepo_categories = [
            "repo_name",
            "author_username",
            "hattori_lanza_size_cat_tiny",
            "hattori_lanza_size_cat_small",
            "hattori_lanza_size_cat_medium",
            "hattori_lanza_size_cat_large",
            "hattori_lanza_content_cat_forward_engineering",
            "hattori_lanza_content_cat_reengineering",
            "hattori_lanza_content_cat_corrective_engineering",
            "hattori_lanza_content_cat_management",
            "hattori_lanza_content_cat_empty_message",
            "hattori_lanza_content_cat_no_categorisation",
            "vasilescu_category_doc",
            "vasilescu_category_img",
            "vasilescu_category_l10n",
            "vasilescu_category_ui",
            "vasilescu_category_media",
            "vasilescu_category_code",
            "vasilescu_category_meta",
            "vasilescu_category_config",
            "vasilescu_category_build",
            "vasilescu_category_devdoc",
            "vasilescu_category_db",
            "vasilescu_category_test",
            #'vasilescu_category_lib', # 'not in index'; presumably there weren't any?
            "vasilescu_category_unknown",
        ]

        # pull out the categorical data categories in a sensible order
        commits_categories_data = commits_multirepo[
            commits_multirepo_categories
        ].fillna(value=0)

        commits_multirepo_others = [
            "repo_name",
            "author_username",
            "n_of_commit_creators",
            "n_commits",
            "pc_repo_commits",
            "n_changes",
            "mean_n_changes",
            "median_n_changes_changed",
            "std_n_changes_changed",
            "n_files_changed",
            "mean_n_files",
            "median_n_files_changed",
            "std_n_files_changed",
        ]

        # pull out other data columns in sensible order
        commits_other_data = commits_multirepo[commits_multirepo_others]

        # join back together in nicer order
        devs_commits_data = pd.concat(
            [commits_other_data, commits_categories_data], axis=1
        )

        assert len(devs_commits_data) == len(multirepo)

        devs_commits_data = devs_commits_data.loc[
            :, ~devs_commits_data.columns.duplicated()
        ]  # remove duplicated 2 columns

        current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")

        filestr = f"{read_location}commits-data-per-dev_x{devs_commits_data['repo_name'].nunique()}-repos_{current_date_info}.csv"
        devs_commits_data.to_csv(path_or_buf=filestr, header=True, index=False)

        end_time = datetime.datetime.now()

        logger.info(
            f"Run time for {len(repolist)} repos with {len(devs_commits_data)} devs cumulatively: {end_time - start_time}"
        )

        return devs_commits_data


if __name__ == "__main__":
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/pre-analysis_data_commits_preps_logs.txt",
        in_notebook=False,
    )

    prepdatacommits = PrepDataCommits(in_notebook=False, logger=logger)

    prepdatacommits.process_commits(read_location="data/", write_location="data/")
