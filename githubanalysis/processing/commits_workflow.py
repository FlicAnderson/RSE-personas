"""Workflow for running commits processing and analysis code for 1 repo."""

import logging
import pandas as pd
import datetime

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

    # def getallcommits(
    #     self,
    #     repo_name=repo_name,
    #     config_path=config_path,
    # ):
    #     logger = loggit.get_default_logger(
    #         console=True,
    #         set_level_to="DEBUG",
    #         log_name="../../logs/get_all_branches_commits_logs.txt",
    #     )
    #     allbranchescommitsgetter = AllBranchesCommitsGetter(
    #         repo_name=repo_name,
    #         in_notebook=True,
    #         config_path="../../githubanalysis/config.cfg",
    #         logger=logger,
    #     )

    #     all_branches_commits = allbranchescommitsgetter.get_all_branches_commits(
    #         repo_name=repo_name
    #     )

    #     return all_branches_commits

    # def processcommits(
    #     self, all_branches_commits, repo_name, in_notebook, write_read_location
    # ):
    #     logger = loggit.get_default_logger(
    #         console=True,
    #         set_level_to="DEBUG",
    #         log_name="../../logs/commits_reformatters_NOTEBOOK_logs.txt",
    #     )
    #     reformat_commits = CommitReformatter(
    #         repo_name=repo_name, in_notebook=True, logger=logger
    #     )

    #     # feed dataframe of all_branches_commits into reformat_commits_object( ) function
    #     processed_commits = reformat_commits.reformat_commits_object(
    #         unique_commits_all_branches=all_branches_commits
    #     )

    #     # write out formatted commits.
    #     reformat_commits.save_formatted_commits(write_read_location="data/")

    #     return processed_commits

    # def getcommitschangesvcats(self, processed_commits):
    #     vlogger = loggit.get_default_logger(
    #         console=True,
    #         set_level_to="DEBUG",
    #         log_name="../../logs/vasilescu_commit_files_classification_NOTEBOOK_logs.txt",
    #     )
    #     vasilescucommitclassifier = Vasilescu_Commit_Classifier(
    #         repo_name="JeschkeLab/DeerLab",
    #         in_notebook=True,
    #         logger=vlogger,
    #         config_path="../../githubanalysis/config.cfg",
    #     )

    #     clogger = loggit.get_default_logger(
    #         console=True,
    #         set_level_to="DEBUG",
    #         log_name="../../logs/get_commit_changes_NOTEBOOK_logs.txt",
    #     )
    #     commitchanges = CommitChanges(
    #         logger=clogger,
    #         repo_name="JeschkeLab/DeerLab",
    #         in_notebook=True,
    #         config_path="../../githubanalysis/config.cfg",
    #     )

    #     n_files: list[tuple[int, str]] = []
    #     n_changes = []
    #     v_category = []

    #     i = 0
    #     for commit in processed_commits["commit_sha"]:
    #         i += 1
    #         print(f"{i} of {len(processed_commits)}")

    #         tmpdf = commitchanges.get_commit_changes(commit_hash=commit)

    #         n_files.append(
    #             commitchanges.get_commit_files_changed(commit_changes_df=tmpdf)
    #         )
    #         n_changes.append(
    #             commitchanges.get_commit_total_changes(commit_changes_df=tmpdf)
    #         )

    #         # apply Vasilescu et al commit classification (filetype) method:
    #         v_category.append(
    #             vasilescucommitclassifier.vasilescu_commit_files_classification(
    #                 commit_changes_df=tmpdf
    #             )
    #         )

    #     return n_files
    #     return n_changes
    #     return v_category

    # def mergecommitscats(self, n_files, n_changes, v_category, processed_commits):
    #     # generate changes_df of files changed from zipped lists of results
    #     output = [
    #         [commit_hash, files_changed, number_changes, vasilescu_category]
    #         for (files_changed, commit_hash), (number_changes, _), (
    #             vasilescu_category,
    #             _,
    #         ) in zip(n_files, n_changes, v_category)
    #     ]
    #     changes_df = pd.DataFrame(
    #         data=output,
    #         columns=["commit_sha", "files_changed", "n_changes", "vasilescu_category"],
    #     )

    #     # merge changes_df to main commits df
    #     processed_commits = processed_commits.merge(
    #         changes_df, on="commit_sha", validate="one_to_one"
    #     )

    #     return processed_commits

    # def contentcats(
    #     self,
    #     processed_commits,
    # ):
    #     logger = loggit.get_default_logger(
    #         console=True,
    #         set_level_to="WARNING",
    #         log_name="../../logs/hattori_lanza_commit_content_classification_NOTEBOOK_logs.txt",
    #     )
    #     hattorilanzaclassifier = Hattori_Lanza_Content_Classification(logger=logger)

    #     results = []

    #     for msg in processed_commits["commit_message"]:
    #         rslt = hattorilanzaclassifier.hattori_lanza_commit_content_classification(
    #             msg
    #         )
    #         results.append(rslt)

    #     processed_commits["hattori_lanza_content_cat"] = results

    #     return processed_commits

    # def sizecats(
    #     self,
    #     processed_commits,
    # ):
    #     results = []

    #     for msg in processed_commits["n_changes"]:
    #         rslt = sizecat.hattori_lanza_commit_size_classification(commit_size=msg)
    #         results.append(rslt)

    #     processed_commits["hattori_lanza_size_cat"] = results

    #     return processed_commits

    # def writeoutcommitscatsstats(
    #     self,
    #     processed_commits,
    #     write_read_location,
    #     sanitised_repo_name,
    #     current_date_info,
    # ):
    #     write_out = f"{write_read_location}commits_cats_stats_{sanitised_repo_name}_{current_date_info}.csv"

    #     processed_commits.to_csv(
    #         path_or_buf=write_out, header=True, index=False, na_rep="", mode="w"
    #     )

    # def readincommitscatsstats(
    #     self, write_read_location, sanitised_repo_name, current_date_info, filepath=""
    # ):
    #     if filepath is None:
    #         filepath = f"{write_read_location}commits_cats_stats_{sanitised_repo_name}_{current_date_info}.csv"

    #     commits_cats_stats = pd.read_csv(filepath_or_buffer=filepath, header=0)

    #     return commits_cats_stats

    # def run_commits_workflow_single(
    #     self,
    #     repo_name,
    #     config_path,
    # ):
    #     commits = self.getallcommits()

    #     processed_commits = self.processcommits(commits)

    #     n_files, n_changes, v_category = self.getcommitschangesvcats(processed_commits)

    #     merged_commits = self.mergecommitscats(
    #         n_files, n_changes, v_category, processed_commits
    #     )

    #     cat_processed_commits = self.contentcats(processed_commits=merged_commits)

    #     size_processed_commits = self.sizecats(processed_commits=cat_processed_commits)

    #     self.writeoutcommitscatsstats(processed_commits=size_processed_commits)

    #     cats_stats_commits = self.readincommitscatsstats()
    #     assert (
    #         len(cats_stats_commits) == len(commits)
    #     ), f"Warning! This df length ({len(cats_stats_commits)}) does not match length of original commit grab ({len(commits)}). "

    #     return cats_stats_commits

    def getcommitschangesvcats(
        self,
        commitchanges: CommitChanges,
        processed_commits: pd.DataFrame,
        vasilescucommitclassifier: Vasilescu_Commit_Classifier,
    ):
        n_files: list[tuple[int, str]] = []
        n_changes = []
        v_category = []

        i = 0
        for commit in processed_commits["commit_sha"]:
            i += 1
            # TODO: LOG
            print(f"{i} of {len(processed_commits)}")

            tmpdf = commitchanges.get_commit_changes(commit_hash=commit)

            n_files.append(
                commitchanges.get_commit_files_changed(commit_changes_df=tmpdf)
            )
            n_changes.append(
                commitchanges.get_commit_total_changes(commit_changes_df=tmpdf)
            )

            # apply Vasilescu et al commit classification (filetype) method:
            v_category.append(
                vasilescucommitclassifier.vasilescu_commit_files_classification(
                    commit_changes_df=tmpdf
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
        hattorilanzaclassifier = Hattori_Lanza_Content_Classification()

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
            rslt = sizecat.hattori_lanza_commit_size_classification(commit_size=msg)
            results.append(rslt)
        return results

    def do_it_all(self):
        allbranchescommitsgetter = AllBranchesCommitsGetter(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
        )
        # TODO: this does not need to take repo name
        all_branches_commits = allbranchescommitsgetter.get_all_branches_commits(
            repo_name=self.repo_name
        )

        reformat_commits = CommitReformatter(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
        )
        processed_commits = reformat_commits.reformat_commits_object(
            unique_commits_all_branches=all_branches_commits
        )
        reformat_commits.save_formatted_commits(self.write_read_location)
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

        processed_commits = self.merge_stats(
            n_files,
            n_changes,
            v_category,
            processed_commits,
        )

        processed_commits["hattori_lanza_content_cat"] = self.classify_content(
            processed_commits
        )
        processed_commits["hattori_lanza_size_cat"] = self.classify_size(
            processed_commits
        )

        # processed_commits.to_csv()
        write_out = f"{self.write_read_location}commits_cats_stats_{self.sanitised_repo_name}_{self.current_date_info}.csv"
        # TODO: log
        print(write_out)

        processed_commits.to_csv(
            path_or_buf=write_out,
            header=True,
            index=False,
            na_rep="",
            mode="w",
        )

        return processed_commits
