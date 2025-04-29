"""Data analysis workflow for github repo analysis."""

# import modules
from pathlib import Path
import datetime
from ast import literal_eval

import logging
import utilities.get_default_logger as loggit
from githubanalysis.visualization.plot_dendrogram import Dendrogrammer

import pandas as pd
import numpy as np

from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, cut_tree, dendrogram
from sklearn.metrics import calinski_harabasz_score

import matplotlib.pyplot as plt
import seaborn as sns
from typing import cast
from scipy.stats import zscore

import re

# data cleaning stuff:
# accept / load clean github data for analysis
# do analysis :D
# save analysis results out
# pass analysis results for optional visualisation


def contribution_in_category(contribution: float, category: str) -> str:
    if contribution > 0.0:
        return category
    else:
        return ""


def bool_contribution_in_category(contribution: float, category: str) -> bool:
    if contribution > 0.0:
        return True
    else:
        return False


def contribution_types_editor(CBRI: int, rough_type_cat: str) -> str:
    assert CBRI is not None, "CBRI is None; check this."
    assert rough_type_cat is not None, "rough_type_cat is None; check this."
    rough_type_cat = rough_type_cat.strip()
    rough_type_cat = re.sub("    ", "  ", rough_type_cat)

    if CBRI == 1:
        return f"ONLY {rough_type_cat}"
    elif CBRI == 2:
        return re.sub("(  )", " and ", rough_type_cat)
    elif CBRI == 3:
        return "creates commits and creates issues and assigned issues"


class DataAnalyser:
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
                log_name="logs/analyse_data.txt",
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
        self.write_location = Path("images/" if not in_notebook else "../../images/")

    def subset_sample_to_repos(
        self,
        data: pd.DataFrame,
        subset_repos_file: str | Path | None,
    ) -> pd.DataFrame:
        """
        Subset a sample dataframe down to only include repositories from a specific file
        """
        # subset data df to include only repo_names from file
        # otherwise use complete data df.

        assert isinstance(
            data, pd.DataFrame
        ), f"data is not in pd.DataFrame format; please check this. type(data) is: {type(data)}"
        assert data.empty is False, "Dataframe data is empty; check inputs."

        self.logger.info(f"data is df, with shape: {data.shape}.")

        if subset_repos_file is None:
            self.logger.info(
                f"No subset_repos_file provided, so returning complete dataset of length: {len(data)}."
            )
            return data  # if no subset_repos_file, don't subset, just return as-is.
        else:
            assert isinstance(
                subset_repos_file, (str, Path)
            ), f"subset_repos_file is neither string nor Path object; {type(subset_repos_file)}"

            if isinstance(subset_repos_file, str):
                subset_repos_file = Path(self.read_location, subset_repos_file)
            # read in file of repos
            # if file is csv: pd.read_csv(subset_repos_file)
            # if file is txt: with file readlines etc
            with open(subset_repos_file, "r") as f:
                subset_repos = [txtline.strip() for txtline in f.readlines()]
            self.logger.info(
                f"length of subset_repos_file is: {len(subset_repos)} repos"
            )

            subset_data = data[data["repo_name"].isin(subset_repos)]
            assert isinstance(subset_data, pd.DataFrame)

            self.logger.info(f"length of subset dataset is now: {len(subset_data)}")

            return subset_data

    def clean_and_contributors(self, cleaned_data: pd.DataFrame) -> pd.DataFrame:
        ## gather category text info about what types of contributions users are contributing

        tmp_iss = cleaned_data["pc_repo_issues"].apply(
            contribution_in_category, category="creates issues"
        )

        tmp_cmt = cleaned_data["pc_repo_commits"].apply(
            contribution_in_category, category="creates commits"
        )

        tmp_ast = cleaned_data["pc_issues_assigned_of_assigned"].apply(
            contribution_in_category, category="assigned issues"
        )

        tmpdf = pd.concat(
            {
                "gh_username": cleaned_data["gh_username"],
                "contributes_creates_commits": tmp_cmt,
                "contributes_creates_issues": tmp_iss,
                "contributes_assigned_issues": tmp_ast,
            },
            axis=1,
        )

        contribution_categories = tmpdf.agg(
            lambda x: f"{x['contributes_creates_commits']}  {x['contributes_creates_issues']}  {x['contributes_assigned_issues']}",
            axis=1,
        )

        tmpdf = pd.concat(
            {
                "gh_username": cleaned_data["gh_username"],
                "contribution_types": contribution_categories,
            },
            axis=1,
        )

        ## gather bool -> numeric info about what types of contributions users are contributing

        tmp_iss_bool = cleaned_data["pc_repo_issues"].apply(
            bool_contribution_in_category, category="creates issues"
        )

        tmp_cmt_bool = cleaned_data["pc_repo_commits"].apply(
            bool_contribution_in_category, category="creates commits"
        )

        tmp_ast_bool = cleaned_data["pc_issues_assigned_of_assigned"].apply(
            bool_contribution_in_category, category="assigned issues"
        )

        tmpdf_bool = pd.concat(
            {
                "contributes_creates_commits": tmp_cmt_bool,
                "contributes_creates_issues": tmp_iss_bool,
                "contributes_assigned_issues": tmp_ast_bool,
            },
            axis=1,
        )

        contribution_categories_bool = tmpdf_bool.sum(axis=1)

        tmpdf_bool = pd.concat(
            {
                "gh_username": cleaned_data["gh_username"],
                "CBRI": contribution_categories_bool,
            },
            axis=1,
        )

        ## pull CBRI and contribution type category values across to cleaned_data dataset

        cleaned_data.loc[:, "CBRI"] = tmpdf_bool["CBRI"]
        cleaned_data.loc[:, "contribution_types"] = tmpdf["contribution_types"]

        cleaned_data.loc[:, "contributions_by_user"] = cleaned_data.apply(
            lambda x: contribution_types_editor(
                CBRI=x.CBRI, rough_type_cat=x.contribution_types
            ),
            axis=1,
        )

        cleaned_data = cleaned_data.drop(columns=["contribution_types"])

        # # add AVERAGE Percentage Repo-Contributions' Depth by Contributor (pcCDC):
        # # each user's percentage of a repo's contributions in each contribution category are added together,
        # # ... then divided by number of contribution-types summed (e.g. 3 if combining commits, issue creation, issue assignment)
        cleaned_data.loc[:, "pcCDC"] = (
            (cleaned_data["pc_repo_commits"])
            + (cleaned_data["pc_repo_issues"])
            + (cleaned_data["pc_issues_assigned_of_assigned"])
        ) / 3

        pd.options.mode.copy_on_write = True

        cleaned_data.loc[:, "n_commits"] = cleaned_data["n_commits"]
        cleaned_data.loc[:, "pc_n_commits"] = (
            cleaned_data[["n_commits"]] / cleaned_data[["n_commits"]].sum()
        ) * 100

        # create percentage of users' commits which fall into each category:
        # this creates human-readble version of these variables
        cleaned_data.loc[:, "pc_HLs-tiny"] = (
            cleaned_data["hattori_lanza_size_cat_tiny"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HLs-sml"] = (
            cleaned_data["hattori_lanza_size_cat_small"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HLs-med"] = (
            cleaned_data["hattori_lanza_size_cat_medium"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HLs-lrg"] = (
            cleaned_data["hattori_lanza_size_cat_large"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )

        cleaned_data.loc[:, "pc_HL-fweng"] = (
            cleaned_data["hattori_lanza_content_cat_forward_engineering"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HL-reeng"] = (
            cleaned_data["hattori_lanza_content_cat_reengineering"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HL-corr"] = (
            cleaned_data["hattori_lanza_content_cat_corrective_engineering"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HL-mgmt"] = (
            cleaned_data["hattori_lanza_content_cat_management"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HL-empty"] = (
            cleaned_data["hattori_lanza_content_cat_empty_message"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_HL-nocat"] = (
            cleaned_data["hattori_lanza_content_cat_no_categorisation"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )

        cleaned_data.loc[:, "pc_V-doc"] = (
            cleaned_data["vasilescu_category_doc"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-code"] = (
            cleaned_data["vasilescu_category_code"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-confg"] = (
            cleaned_data["vasilescu_category_config"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-build"] = (
            cleaned_data["vasilescu_category_build"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-dvdoc"] = (
            cleaned_data["vasilescu_category_devdoc"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-test"] = (
            cleaned_data["vasilescu_category_test"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-meta"] = (
            cleaned_data["vasilescu_category_meta"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-img"] = (
            cleaned_data["vasilescu_category_img"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-l10n"] = (
            cleaned_data["vasilescu_category_l10n"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-ui"] = (
            cleaned_data["vasilescu_category_ui"].div(cleaned_data["n_commits"], axis=0)
            * 100
        )
        cleaned_data.loc[:, "pc_V-media"] = (
            cleaned_data["vasilescu_category_media"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )
        cleaned_data.loc[:, "pc_V-nocat"] = (
            cleaned_data["vasilescu_category_unknown"].div(
                cleaned_data["n_commits"], axis=0
            )
            * 100
        )

        return cleaned_data

    def combine_cleaned_data_with_interactions(
        self,
        cleaned_data: pd.DataFrame,
        all_interaction_data: pd.DataFrame,
    ):
        self.logger.info(f"{cleaned_data.shape =}")

        self.logger.info(f"{all_interaction_data.shape =}")

        # merge interaction data onto main analysis dataset:
        cleaned_data_with_interactions = pd.merge(
            cleaned_data,
            all_interaction_data,
            how="inner",
            on=["repo_name", "gh_username"],
        )  # join on repo-individual as key
        self.logger.info(f"{cleaned_data_with_interactions.shape = }")
        self.logger.info(
            f"Number of unique cols in cleaned_data_with_interactions is: {cleaned_data_with_interactions.columns.nunique()}."
        )
        self.writeout_data_to_csv(
            cleaned_data_with_interactions,
            filename="test_cleaned_data_with_interactions_",
        )

        assert (
            "pc_issues_assigned_of_assigned" in cleaned_data_with_interactions.columns
        )
        # recalculate some columns to add assignment info
        cleaned_data_with_interactions["breadth_interactions"] = (
            cleaned_data_with_interactions.apply(
                lambda row: (row["breadth_interactions"] + 1)
                if row["pc_issues_assigned_of_assigned"] > 0
                else row["breadth_interactions"],
                axis=1,
            )
        )
        cleaned_data_with_interactions["which_interactions"] = (
            cleaned_data_with_interactions.apply(
                lambda row: (f"{row['which_interactions']}, assigned_issue")
                if row["pc_issues_assigned_of_assigned"] > 0
                else row["which_interactions"],
                axis=1,
            )
        )

        # cleaned_data_with_interactions =
        cleaned_data_with_interactions.drop(
            columns=[
                "pc_repo_commits",
                "pc_repo_issues",
                "CBRI",
                "contributions_by_user",
                "pcCDC",
                "n_commits",  # dropping the older column, keeping commits_created as probably later
                "_merge",
                "issue_username",
                "commiss_merge",
                "_dataset_source",
                "issue_author_username",
            ],
            inplace=True,
        )  # remove old columns

        # regenerate pcCDC from interactions columns but rename to pc_DC (percent Depth of Contributions):
        cleaned_data_with_interactions.loc[:, "pc_DC"] = (
            (cleaned_data_with_interactions["pc_commit_created"])
            + (cleaned_data_with_interactions["pc_issue_created"])
            + (cleaned_data_with_interactions["pc_issue_closed"])
            + (cleaned_data_with_interactions["pc_issues_assigned_of_assigned"])
            + (cleaned_data_with_interactions["pc_pull_request_created"])
        ) / 5
        return cleaned_data_with_interactions
        # cleaned_data_with_interactions.rename(columns={"breadth_interactions": "CBRI"}) # probably clearer if I don't rename it :C

    def writeout_data_to_csv(self, df: pd.DataFrame, filename: str | Path):
        filestr = f"{filename}_{self.current_date_info}.csv"
        filepath = Path(self.read_location, filestr)
        df.to_csv(path_or_buf=filepath, header=True, index=False)
        return filepath

    def sample_languages(self, relevant_repo_stats: pd.DataFrame) -> pd.DataFrame:
        n_sample_repos = relevant_repo_stats.groupby("repo_name").ngroups
        relevant_repo_stats = relevant_repo_stats.dropna(
            subset="repo_language"
        ).reset_index()
        relevant_repo_stats.loc[:, "repo_language"] = relevant_repo_stats[
            "repo_language"
        ].apply(lambda x: eval(x) if isinstance(x, str) else x)
        relevant_repo_stats_languages = relevant_repo_stats.explode("repo_language")

        self.logger.info(
            f"{relevant_repo_stats_languages.groupby('repo_language').ngroups} unique languages listed in dataset of {n_sample_repos} unique repositories..."
        )  # 93 unique languages listed in the dataset.

        # # GET DESCENDING LIST OF NUMBERS OF REPOS FROM DATASET USING X REPO LANGUAGE (can use >1 language per repo):

        dataset_languages = (
            relevant_repo_stats_languages.groupby("repo_language")["repo_language"]
            .count()
            .sort_values(ascending=False)
            .reset_index(name="n_repos_using_language")
        )

        dataset_languages.loc[:, "pc_repos_using_language"] = (
            dataset_languages["n_repos_using_language"] / n_sample_repos
        ) * 100
        # write out repo_stats of analysis repos
        self.logger.info(
            f"Top 15 RS Repo Languages from Dataset: {dataset_languages.loc[0:14]}"
        )
        writeout_to_languages = self.writeout_data_to_csv(
            df=dataset_languages, filename="sample_languages_info_"
        )
        self.logger.info(
            f"dataset languages information written out to {writeout_to_languages}"
        )
        return dataset_languages

    def plot_sample_languages(
        self,
        dataset_languages: pd.DataFrame,
        n_repos: int | None,
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        over1pclanguages = dataset_languages.query("pc_repos_using_language >= 1")

        sns.barplot(
            data=over1pclanguages, x="repo_language", y="pc_repos_using_language"
        )
        if n_repos is not None and isinstance(n_repos, int):
            titletxt = f"Percentage (>=1%) of SAMPLE Repos using 'Language' (N repos = {n_repos})"
        else:
            titletxt = "Percentage (>=1%) of SAMPLE Repos using 'Language'"
        plt.title(titletxt)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plot_file = Path(
            self.write_location,
            f"sample_languages_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")

    def create_clustering_data_from_sample(
        self,
        cleaned_data_with_interactions,
    ):
        clustering_data = cleaned_data_with_interactions[
            [  # keep only these columns:
                "pc_commit_created",
                "pc_issue_created",
                "pc_issue_closed",
                "pc_issues_assigned_of_assigned",
                "pc_pull_request_created",
                "pc_DC",
                "pc_sum_n_interactions",
                "pc_interaction_days",
                "interaction_days",  # ideally should be pc_of_repo_age!
                "interaction_period_days",  # ideally should be pc_of_repo_age!
                "pc_created-closed_issues",
                # "mean_n_interactions_per_interaction_day",
            ]
        ]
        return clustering_data

    def evaluate_n_clusters(
        self,
        clustering_data: pd.DataFrame,
        max_clusters_to_eval: int = 10,  # how many clusters to test with CH scores
        use_metric: str = "euclidean",
        use_linkage: str = "ward",
    ) -> pd.DataFrame:
        """
        This uses the Calinski & Harabasz Score aka Variance Ratio
        Criterion to evaluate best fit number of clusters without overfitting.

        QUOTE: "The score is defined as ratio of the sum of between-cluster
        dispersion and of within-cluster dispersion." via sklearn docs at
        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.calinski_harabasz_score.html
        accessed 10th Feb 2025
        """
        if isinstance(clustering_data, pd.DataFrame):
            assert (
                clustering_data.empty is False
            ), "Dataframe data is empty; check inputs."

        self.logger.info(f"clustering data is df, with shape: {clustering_data.shape}.")

        clusters_range = range(2, max_clusters_to_eval + 1, 1)
        # start at 2 because need min of 2 clusters
        # end on max_clusters_to_eval number
        # increase by 1
        X = clustering_data  # sample data, naming according to clustering/ML practices
        eval_chs = []
        eval_ns = []

        for n in clusters_range:
            n_clusters = n
            model = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric=literal_eval(use_metric),
                linkage=literal_eval(use_linkage),
            )
            model_predictions = model.fit_predict(X)
            cluster_labels = model_predictions
            eval_chs.append(calinski_harabasz_score(X, cluster_labels))
            eval_ns.append(n_clusters)
            self.logger.info(
                f"CH score for n_clusters {n_clusters} is {calinski_harabasz_score(X, cluster_labels)}."
            )
        eval_df = pd.DataFrame(  # return df of scores per n of clusters evaluated.
            {
                "CH_score": eval_chs,
                "N_clusters_evaluated": eval_ns,
            }
        )
        # write out results df
        writeout_to_CHscores = self.writeout_data_to_csv(
            eval_df,
            "sample_calinski-harabasz_scores_across_N_clusters_",
        )
        self.logger.info(
            f"CH scores for {len(eval_df)} clusters written out to file {writeout_to_CHscores}."
        )

        return eval_df

    def do_clustering(
        self,
        clustering_data: pd.DataFrame,
        best_n_clusters: int,
        cleaned_data_with_interactions: pd.DataFrame,
    ) -> pd.DataFrame:
        model = AgglomerativeClustering(
            n_clusters=best_n_clusters, metric="euclidean", linkage="ward"
        )  # x2 clusters because of CH Score!

        X = clustering_data

        # fit the hierarchical clustering algorithm to dataset X
        model_predictions = model.fit_predict(X)
        # create the cluster_labels vector showing which cluster
        # each repo-individual belongs to
        cluster_labels = model_predictions

        cleaned_data_with_interactions = cleaned_data_with_interactions.reset_index(
            drop=True
        )

        sklearn_hcwdata = pd.concat(
            [
                pd.DataFrame({"cluster_labels": cluster_labels}),
                cleaned_data_with_interactions,
            ],
            axis=1,
        )

        # write out dataset used for clustering:
        self.writeout_data_to_csv(
            sklearn_hcwdata,
            "clustered_sample_data_with_labels_",
        )
        return sklearn_hcwdata

    def analysis_workflow(
        self,
        data: pd.DataFrame,
        subset_repos_file: str | Path,
        interactions_data_file: str | Path,
        repo_stats_file: str | Path,
    ):
        # if data is file:

        # if data is df:
        if isinstance(data, pd.DataFrame):
            assert data.empty is False, "Dataframe data is empty; check inputs."
            self.logger.info(f"data is df, with shape: {data.shape}.")

        # if subset_repos_file is not None:
        if subset_repos_file is not None:
            data = self.subset_sample_to_repos(
                data,
                subset_repos_file=subset_repos_file,
            )
        # read in file of repos
        # subset data df to include only repo_names from file
        # otherwise use complete data df.

        interactions_data_file = Path(self.read_location, interactions_data_file)
        repo_stats_file = Path(self.read_location, repo_stats_file)

        self.logger.info(
            f"Number of repositories in sample is: {data.groupby('repo_name').ngroups}."
        )

        # self.logger.info("Team size of repositories in sample is: TODO.")
        # min, max, mean, stddev, size of repos - n of contributors via API, n of repo-individuals.

        self.logger.info(
            f"Number of unique gh_usernames in sample is: {data.groupby('gh_username').ngroups}."
        )
        self.logger.info(
            f"Number of gh_usernames appearing in more than one repository in this sample is: {len(data.groupby('gh_username')[['repo_name']].count().reset_index(names=['gh_username', 'count']).query('repo_name > 1'))}."
        )

        self.logger.info(
            f"Number of repo-individuals (repo_name plus gh_username combos) in sample is: {data.groupby(['repo_name', 'gh_username']).ngroups}."
        )

        # log out:
        # number of probable 'bots'
        # number of 'ghost' users
        # number of repo-individuals who come from issues API, or commits API, or appear in both APIs.

        # clean data and rename columns as req

        cleaned_data = self.clean_and_contributors(
            data,
        )

        interact = pd.read_csv(
            interactions_data_file,
            header=0,
            low_memory=False,
        )

        self.logger.info(f"Column names from cleaned_df: {cleaned_data.columns}")
        self.logger.info(f"Column names from interactions file: {interact.columns}")
        # add interaction data, merge onto cleaned_data.
        cleaned_data_with_interactions = self.combine_cleaned_data_with_interactions(
            cleaned_data=cleaned_data,
            all_interaction_data=interact,
        )
        self.logger.info(
            f"Combined cleaned_data_with_interaction_data df has shape: {cleaned_data_with_interactions.shape}."
        )

        write_out_to_combined = self.writeout_data_to_csv(
            df=cleaned_data_with_interactions,
            filename="cleaned_data_with_interaction-data-per-dev_",
        )
        self.logger.info(
            f"Combined cleaned_data and interaction_data written out to {write_out_to_combined}"
        )

        # read in summarised repo stats data, subset to repos in sample
        repo_stats = pd.read_csv(
            repo_stats_file,
            header=0,
        )
        assert (
            repo_stats is not None
        ), f"repo_stats was not read correctly, please check file {repo_stats_file}"
        repo_stats = self.subset_sample_to_repos(  # subset to relevant repos only
            repo_stats,
            subset_repos_file=subset_repos_file,
        )

        # write out relevant repo stats:
        write_out_to_repo_stats = self.writeout_data_to_csv(
            df=repo_stats, filename="summarised_SAMPLE_repos_stats"
        )
        self.logger.info(
            f"Relevant repo_stats subset written out to {write_out_to_repo_stats}"
        )

        n_repos = cleaned_data_with_interactions.groupby("repo_name").ngroups
        n_users = len(cleaned_data_with_interactions)

        # analyse & write out languages from sample
        # plot languages data from sample
        self.plot_sample_languages(
            self.sample_languages(relevant_repo_stats=repo_stats),
            n_repos=n_repos,
        )
        self.logger.info(
            "Sample repos languages info collected and written out and plotted."
        )

        # save out pre-processing dataset
        n_repos = cleaned_data_with_interactions.groupby("repo_name").ngroups
        n_users = len(cleaned_data_with_interactions)
        write_out_to_preprocessed = self.writeout_data_to_csv(
            cleaned_data_with_interactions,
            f"pre-processing_dataset_x{n_repos}repos_x{n_users}project-individuals_",
        )
        self.logger.info(
            f"Processed sample data written out to {write_out_to_preprocessed}"
        )

        clustering_data = self.create_clustering_data_from_sample(
            cleaned_data_with_interactions=cleaned_data_with_interactions
        )

        self.writeout_data_to_csv(clustering_data, filename="test_clustering_data")
        # clustering
        self.logger.info(f"Clustering dataset has shape {clustering_data.shape}")
        # plot dendrogram
        # save out
        dendrogrammer = Dendrogrammer(in_notebook=False, logger=self.logger)
        dendrogrammer.plot_dendrogram(
            clustering_data=clustering_data,
            colours=["#D50032", "#1D2A3D", "#FDBC42"],
        )

        # clustering:
        # run clustering with diff N of clusters and calculate calinski_harabasz score to evaluate
        # log out n of clusters, ch scores, etc
        eval_CHs = self.evaluate_n_clusters(
            clustering_data=clustering_data,
            max_clusters_to_eval=10,
        )
        best_n_clusters = cast(  # cast here means "trust me, this is an int"
            np.int64,
            eval_CHs.loc[  # from evaluation dataframe:
                # get index of highest CH score, get number of clusters that represented
                eval_CHs["CH_score"].idxmax(), "N_clusters_evaluated"
            ],
        )
        assert (
            best_n_clusters.dtype == np.int64
        ), "Check that N_clusters_evaluated column contains integers!"

        self.logger.info(
            f"Calinski-Harabasz Score evaluation shows best number of clusters for sample is {best_n_clusters} with score {eval_CHs.loc[eval_CHs['CH_score'].idxmax(), 'CH_score']}."
        )

        # run actual clustering with best N of clusters
        # write out clustering data
        # apply cluster_labels to original data (cleaned_data_with_interactions)
        self.do_clustering(
            clustering_data=clustering_data,
            best_n_clusters=int(best_n_clusters),
            cleaned_data_with_interactions=cleaned_data_with_interactions,
        )

        # log cluster number, sizes of n_repo_individuals, n_repos, distribution, etc.
        # means for key variables by cluster

        # create upset plot for interaction combinations

        # PCA: run PCA to assess how variance is distributed
        # plot 2D
        # plot 3D
        # log out axis importance


def main():
    dataanalyser = DataAnalyser(in_notebook=False)
    # dataanalyser.read_location
    data_df = pd.read_csv(
        Path(
            dataanalyser.read_location, "merged-data-per-dev_x3740-repos_2025-04-15.csv"
        ),
        header=0,
        low_memory=False,
    )
    dataanalyser.analysis_workflow(
        data=data_df,
        subset_repos_file="deRSE-sample-intersection-repos_2025-04-22_x21.txt",
        interactions_data_file="merged-interactions-data-per-dev_x3821-repos_2025-04-18.csv",
        repo_stats_file="summarised_repo_stats_2025-03-26.csv",
    )


if __name__ == "__main__":
    main()
