"""Combine prepared issues and commits datasets."""

from pathlib import Path
import argparse
import datetime
import numpy as np
import pandas as pd
from githubanalysis.setup_classes import DatasetSetup
import utilities.get_default_logger as loggit


class PrepDataCombined(DatasetSetup):
    def _log_name(self) -> str:
        return "prep_combined"

    def process_multi_origin_data(
        self,
        commits_data_file: str | Path,
        issues_data_file: str | Path,
    ) -> pd.DataFrame | None:
        """
        Combines per-dev (per repo-individual) data from commits and issue tickets
        into single dataframe for analysis.

        Outputs: returns omnirepo, generates output .csv file: merged-data-per-dev_x2868-repos_2025-05-10.csv

        Example Run: python githubanalysis/processing/prep_combined.py -c commits-data-per-dev_x2320-repos_2025-04-15.csv -i issues-data-per-dev_x2829-repos_x237715-repo-individuals_2025-04-15.csv

        Columns of omnirepo df:
            repo_name,  # IMP
            author_username,
            n_of_commit_creators,
            n_commits,
            pc_repo_commits,  # IMP
            n_changes,
            mean_n_changes,
            median_n_changes_changed,
            std_n_changes_changed,
            n_files_changed,
            mean_n_files,
            median_n_files_changed,
            std_n_files_changed,
            hattori_lanza_size_cat_tiny,
            hattori_lanza_size_cat_small,
            hattori_lanza_size_cat_medium,
            hattori_lanza_size_cat_large,
            hattori_lanza_content_cat_forward_engineering,
            hattori_lanza_content_cat_reengineering,
            hattori_lanza_content_cat_corrective_engineering,
            hattori_lanza_content_cat_management,
            hattori_lanza_content_cat_empty_message,
            hattori_lanza_content_cat_no_categorisation,
            vasilescu_category_doc,
            vasilescu_category_img,
            vasilescu_category_l10n,
            vasilescu_category_ui,
            vasilescu_category_media,
            vasilescu_category_code,
            vasilescu_category_meta,
            vasilescu_category_config,
            vasilescu_category_build,
            vasilescu_category_devdoc,
            vasilescu_category_db,
            vasilescu_category_test,
            vasilescu_category_unknown,
            issue_author_username,
            n_issues,
            pc_repo_issues,  # IMP
            n_of_issues_creators,
            assigned_devs,
            n_issues_assigned,
            pc_issues_assigned_of_assigned,  # IMP
            _merge,
            issue_username,
            commiss_merge,
            gh_username,  # IMP
            _dataset_source,

        """
        commits_data_file = Path(self.data_read_location, commits_data_file)
        issues_data_file = Path(self.data_read_location, issues_data_file)
        self.logger.info(f"Commits data file: {commits_data_file}")
        self.logger.info(f"Issues data file: {issues_data_file}")

        start_time = datetime.datetime.now()

        commits_multirepo = pd.read_csv(commits_data_file)
        self.logger.info(f"length of commits df is {len(commits_multirepo)}")

        issues_multirepo = pd.read_csv(issues_data_file)
        self.logger.info(f"length of issues df is {len(issues_multirepo)}")

        commits_multirepo = commits_multirepo.drop_duplicates(
            keep="first", ignore_index=True
        )
        issues_multirepo = issues_multirepo.drop_duplicates(
            keep="first", ignore_index=True
        )

        omnirepo = pd.merge(
            left=commits_multirepo,
            right=issues_multirepo,
            how="outer",
            left_on=["author_username", "repo_name"],
            right_on=["issue_username", "repo_name"],
            # validate="one_to_one",
            suffixes=("_commits", "_issues"),
            indicator="commiss_merge",
        )
        self.logger.info(f"Merged dataset has length: {len(omnirepo)}.")

        # fill missing values where necesary
        omnirepo["n_commits"] = omnirepo["n_commits"].fillna(value=0)
        omnirepo["n_issues"] = omnirepo["n_issues"].fillna(value=0)
        omnirepo["pc_repo_commits"] = omnirepo["pc_repo_commits"].fillna(value=0)
        omnirepo["pc_repo_issues"] = omnirepo["pc_repo_issues"].fillna(value=0)
        omnirepo["pc_issues_assigned_of_assigned"] = omnirepo[
            "pc_issues_assigned_of_assigned"
        ].fillna(value=0)
        omnirepo["n_issues_assigned"] = omnirepo["n_issues_assigned"].fillna(value=0)
        omnirepo["author_username"] = omnirepo["author_username"].fillna(value="None")
        omnirepo["issue_author_username"] = omnirepo["issue_author_username"].fillna(
            value="None"
        )
        omnirepo["assigned_devs"] = omnirepo["assigned_devs"].fillna(value="unassigned")

        # create authoratative ghusername field for issues df:
        omnirepo["gh_username"] = np.where(
            omnirepo["author_username"] == "None",
            omnirepo["issue_username"],
            omnirepo["author_username"],
        )

        # create human-readable dataset source column:
        d = {"left_only": "Only Commits", "right_only": "Only Issues", "both": "Both"}
        omnirepo["_dataset_source"] = omnirepo["commiss_merge"].map(d)

        n_repos_omnirepo = int(omnirepo.groupby("repo_name").ngroups)

        filestr = f"merged-data-per-dev_x{omnirepo['repo_name'].nunique()}-repos_{self.current_date_info}.csv"
        writeout_path = Path(self.data_write_location, filestr)

        try:
            omnirepo.to_csv(path_or_buf=writeout_path, header=True, index=False)
            self.logger.info(f"Merged dataset file written out to {writeout_path}")

            end_time = datetime.datetime.now()

            self.logger.info(
                f"Run time for {n_repos_omnirepo} repos with {len(omnirepo)} devs cumulatively: {end_time - start_time}"
            )

            self.logger.info(
                f"Saved devs_commits_data df for {n_repos_omnirepo} repos with {len(omnirepo)} devs to file: {filestr}"
            )

            return omnirepo  # RETURN MERGED DATASET

        except Exception as e:
            self.logger.error(
                f"Error in attempting to write output file; {e}; error type: {type(e)}; writeout path attempted was: {writeout_path}"
            )


parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--commits-data-per-dev-file",
    metavar="COMMITS_DATA_PER_DEV_FILE",
    help="Path to .csv file containing commits data (line per repo-individual), eg 'commits-data-per-dev_x5828-repos_2025-02-15.csv'.",
    type=str,
)
parser.add_argument(
    "-i",
    "--issues-data-per-dev-file",
    metavar="ISSUES_DATA_PER_DEV_FILE",
    help="Path to .csv file containing issues data (line per repo-individual), eg 'issues-data-per-dev_x1716-repos_2024-12-11.csv'.",
    type=str,
)


if __name__ == "__main__":
    args = parser.parse_args()
    commits_data: str = args.commits_data_per_dev_file
    issues_data: str = args.issues_data_per_dev_file

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/prep_combined_logs.txt",
        in_notebook=False,
    )

    if ((commits_data is not None) + (issues_data is not None)) != 2:
        logger.error(
            "Exactly two arguments allowed; please avoid your current whole deal and supply commits and issues per-dev data files."
        )
        exit(1)

    logger.info(f"Args: {args}")
    print(args)

    logger.info(
        f"Running data combination pre-analysis preparation methods on commits data file {commits_data} and issues file {issues_data}."
    )

    prepdatacombined = PrepDataCombined(
        dataset_name="combined-issues-commits",
        in_notebook=False,
        logger=logger,
        exists_ok=True,
    )

    combined_data = prepdatacombined.process_multi_origin_data(
        commits_data_file=commits_data,
        issues_data_file=issues_data,
    )
