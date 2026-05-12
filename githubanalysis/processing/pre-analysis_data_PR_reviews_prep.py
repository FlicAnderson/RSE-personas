"""Collate PR Code Review (PRCR) datafiles, generate dataframes ready for analysis and get timestamp and interaction types info for Pull Request Code Reviews (PRCR)."""

from githubanalysis.setup_classes import DatasetSetup


class PrepDataPRReviews(DatasetSetup):
    def _log_name(self) -> str:
        return "pre-analysis_data_PR_reviews_prep"

    def process_PRCR(self):
        pass
