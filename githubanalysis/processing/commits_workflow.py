"""Workflow for running commits processing and analysis code for 1 repo."""

import logging
import pandas as pd
import datetime
from pathlib import Path

import utilities.get_default_logger as loggit
from githubanalysis.processing.get_all_branches_commits import AllBranchesCommitsGetter
from githubanalysis.processing.get_commit_changes import CommitChanges
from githubanalysis.processing.reformat_commits import CommitReformatter
import githubanalysis.analysis.hattori_lanza_commit_size_classification as sizecat
from githubanalysis.analysis.hattori_lanza_commit_content_classification import (
    Hattori_Lanza_Content_Classification,
)
from githubanalysis.analysis.vasilescu_commit_files_classification import (
    Vasilescu_Commit_Classifier,
)


class RunCommits:
    logger: logging.Logger
    config_path: str
    in_notebook: bool
    current_date_info: str
    sanitised_repo_name: str
    repo_name: str
    write_read_location: str

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        write_read_location: str,
        logger: logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/commits_workflow_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name
        self.write_read_location = write_read_location

    def check_existing_formatted_commits(self):
        # generate filename and check if this file had been created already today:

        formatted_commits_filename = f"{self.write_read_location}processed-commits_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        formatted_commits_path = Path(formatted_commits_filename)
        self.logger.info(
            f"checking whether formatted commits dataset already exists at path {formatted_commits_path}"
        )

        if formatted_commits_path.is_file():  # read in existing dataset
            processed_commits_df = pd.read_csv(
                formatted_commits_filename, index_col=0, header=0
            )

            self.logger.info("loaded in previously-got commits data")
            return processed_commits_df

        else:  # run steps to get commits data and generate dataset
            allbranchescommitsgetter = AllBranchesCommitsGetter(
                repo_name=self.repo_name,
                in_notebook=self.in_notebook,
                config_path=self.config_path,
            )
            # TODO: this does not need to take repo name
            all_branches_commits = allbranchescommitsgetter.get_all_branches_commits(
                repo_name=self.repo_name
            )
            self.logger.info("did allbranchescommitsgetter()")

            reformat_commits = CommitReformatter(
                repo_name=self.repo_name,
                in_notebook=self.in_notebook,
            )
            processed_commits_df = reformat_commits.reformat_commits_object(
                unique_commits_all_branches=all_branches_commits
            )

            self.logger.info("did reformat commits")
            reformat_commits.save_formatted_commits(self.write_read_location)
            self.logger.info("saved out reformat commits")

            return processed_commits_df

    def getcommitschangesvcats(
        self,
        commitchanges: CommitChanges,
        processed_commits: pd.DataFrame,
        vasilescucommitclassifier: Vasilescu_Commit_Classifier,
    ):
        self.logger.info("Beginning getcommitschangesvcats( ).")
        n_files: list[tuple[int, str]] = []
        n_changes = []
        v_category = []

        i = 0
        for commit in processed_commits["commit_sha"]:
            i += 1
            # TODO: LOG
            self.logger.info(
                f"Getting change numbers and v_cats for {i} of {len(processed_commits)} commits for repo {self.repo_name}."
            )

            tmpdf = commitchanges.get_commit_changes(commit_hash=commit)

            n_files.append(
                commitchanges.get_commit_files_changed(
                    commit_changes_df=tmpdf, commit_hash=commit
                )
            )
            n_changes.append(
                commitchanges.get_commit_total_changes(
                    commit_changes_df=tmpdf, commit_hash=commit
                )
            )

            # apply Vasilescu et al commit classification (filetype) method:
            v_category.append(
                vasilescucommitclassifier.vasilescu_commit_files_classification(
                    commit_changes_df=tmpdf,
                    commit_hash=commit,
                )
            )
        return n_files, n_changes, v_category

    def merge_stats(
        self,
        n_files: list[tuple[int, str]],
        n_changes: list[tuple[int, str]],
        v_category: list[tuple[str, str]],
        processed_commits: pd.DataFrame,
    ):
        # generate changes_df of files changed from zipped lists of results
        output = [
            [commit_hash, files_changed, number_changes, vasilescu_category]
            for (
                (files_changed, commit_hash),
                (number_changes, _),
                (vasilescu_category, _),
            ) in zip(n_files, n_changes, v_category)
        ]
        changes_df = pd.DataFrame(
            data=output,
            columns=["commit_sha", "files_changed", "n_changes", "vasilescu_category"],
        )

        # merge changes_df to main commits df
        return processed_commits.merge(
            changes_df,
            on="commit_sha",
            validate="one_to_one",
        )

    def classify_content(self, processed_commits: pd.DataFrame):
        hattorilanzaclassifier = Hattori_Lanza_Content_Classification(
            in_notebook=self.in_notebook
        )

        results = []

        for msg in processed_commits["commit_message"]:
            rslt = hattorilanzaclassifier.hattori_lanza_commit_content_classification(
                msg
            )
            results.append(rslt)

        return results

    def classify_size(self, processed_commits: pd.DataFrame):
        results = []

        for msg in processed_commits["n_changes"]:
            self.logger.debug(f"commit size n_changes value is: {msg}")
            rslt = sizecat.hattori_lanza_commit_size_classification(commit_size=msg)
            results.append(rslt)
        return results

    def do_it_all(self):
        self.logger.info("checking whether formatted commits dataset already exists")
        # if all processed commits here from same day, don't re-run getter steps.
        processed_commits = self.check_existing_formatted_commits()
        self.logger.info("got formatted commits data")

        commitchanges = CommitChanges(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
        )
        vasilescucommitclassifier = Vasilescu_Commit_Classifier(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
        )
        n_files, n_changes, v_category = self.getcommitschangesvcats(
            commitchanges,
            processed_commits,
            vasilescucommitclassifier,
        )
        self.logger.info(
            "did get commits changes; get vasilescu categories; return lists"
        )

        processed_commits = self.merge_stats(
            n_files,
            n_changes,
            v_category,
            processed_commits,
        )
        self.logger.info("did merge the lists with processed commits data")

        write_out = f"{self.write_read_location}commits_changes_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        self.logger.info(
            f"writing processed commits with changes and v_cats file out to this path / filename: {write_out}"
        )

        processed_commits["hattori_lanza_content_cat"] = self.classify_content(
            processed_commits
        )
        self.logger.info("did hattori lanza commits content classification")
        processed_commits["hattori_lanza_size_cat"] = self.classify_size(
            processed_commits
        )
        self.logger.info("did hattori lanza size classification")

        write_out = f"{self.write_read_location}commits_cats_stats_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        self.logger.info(
            f"writing post-workflow file out to this path / filename: {write_out}"
        )

        processed_commits.to_csv(
            path_or_buf=write_out,
            header=True,
            index=False,
            na_rep="",
            mode="w",
        )
        self.logger.info("did writeout")

        return processed_commits
