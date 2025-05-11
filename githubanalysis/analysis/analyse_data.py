"""Data analysis workflow for github repo analysis."""

# import modules
from pathlib import Path
import gc
import datetime
import argparse

import logging
import utilities.get_default_logger as loggit
from githubanalysis.visualization.plot_dendrogram import Dendrogrammer
from githubanalysis.visualization.plot_repoindividual_upset_plot import UpsetPlotter
from githubanalysis.visualization.plot_multidim_PCA import PlotPCA

import random
import pandas as pd
import numpy as np

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import calinski_harabasz_score
from sklearn.decomposition import PCA

import matplotlib.pyplot as plt
import seaborn as sns
from typing import cast

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
    image_write_location: Path
    data_read_location: Path

    def __init__(
        self,
        dataset_name: str,
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
        self.data_read_location = Path("data/" if not in_notebook else "../../data/")
        self.data_write_location = (
            Path("data/" if not in_notebook else "../../data/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.image_write_location = (
            Path("images/" if not in_notebook else "../../images/")
            / f"analysis_run_{dataset_name}_{self.current_date_info}"
        )
        self.data_write_location.mkdir()
        self.image_write_location.mkdir()

    def subset_sample_to_repos(
        self,
        data: pd.DataFrame,
        subset_repos_file: str | Path | None,
        subset_pc: int,
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
                subset_repos_file = Path(self.data_read_location, subset_repos_file)
            # read in file of repos
            # if file is csv: pd.read_csv(subset_repos_file)
            # if file is txt: with file readlines etc
            with open(subset_repos_file, "r") as f:
                subset_repos = [txtline.strip() for txtline in f.readlines()]
            self.logger.info(
                f"length of subset_repos_file is: {len(subset_repos)} repos"
            )

            flics_seed = 42
            random.seed(flics_seed)
            self.logger.info(
                f"Subsetting percentage is: {subset_pc}; using random seed: {flics_seed}"
            )

            subset_pc_as_n = round((len(subset_repos) * (subset_pc / 100)))
            # Re: behaviour of round: Return number rounded to ndigits precision
            # after the decimal point. If ndigits is omitted or is None,
            # it returns the nearest integer to its input.
            # via https://docs.python.org/3/library/functions.html#round on 1 May 2025.

            subset_repos = random.sample(subset_repos, k=subset_pc_as_n)
            self.logger.info(
                f"After applying subset percentage, length of subset_repos_file is: {len(subset_repos)} repos"
            )

            subset_data = data[data["repo_name"].isin(subset_repos)]
            assert isinstance(subset_data, pd.DataFrame)

            self.logger.info(f"length of subset dataset is now: {len(subset_data)}")

            return subset_data

    def clean_and_contributors(self, data: pd.DataFrame) -> pd.DataFrame:
        ## gather category text info about what types of contributions users are contributing

        tmp_iss = data["pc_repo_issues"].apply(
            contribution_in_category, category="creates issues"
        )

        tmp_cmt = data["pc_repo_commits"].apply(
            contribution_in_category, category="creates commits"
        )

        tmp_ast = data["pc_issues_assigned_of_assigned"].apply(
            contribution_in_category, category="assigned issues"
        )

        tmpdf = pd.concat(
            {
                "gh_username": data["gh_username"],
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
                "gh_username": data["gh_username"],
                "contribution_types": contribution_categories,
            },
            axis=1,
        )

        ## gather bool -> numeric info about what types of contributions users are contributing

        tmp_iss_bool = data["pc_repo_issues"].apply(
            bool_contribution_in_category, category="creates issues"
        )

        tmp_cmt_bool = data["pc_repo_commits"].apply(
            bool_contribution_in_category, category="creates commits"
        )

        tmp_ast_bool = data["pc_issues_assigned_of_assigned"].apply(
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
                "gh_username": data["gh_username"],
                "CBRI": contribution_categories_bool,
            },
            axis=1,
        )

        ## pull CBRI and contribution type category values across to cleaned_data dataset

        data.loc[:, "CBRI"] = tmpdf_bool["CBRI"]
        data.loc[:, "contribution_types"] = tmpdf["contribution_types"]

        data.loc[:, "contributions_by_user"] = data.apply(
            lambda x: contribution_types_editor(
                CBRI=x.CBRI, rough_type_cat=x.contribution_types
            ),
            axis=1,
        )

        data = data.drop(columns=["contribution_types"])

        # # add AVERAGE Percentage Repo-Contributions' Depth by Contributor (pcCDC):
        # # each user's percentage of a repo's contributions in each contribution category are added together,
        # # ... then divided by number of contribution-types summed (e.g. 3 if combining commits, issue creation, issue assignment)
        data.loc[:, "pcCDC"] = (
            (data["pc_repo_commits"])
            + (data["pc_repo_issues"])
            + (data["pc_issues_assigned_of_assigned"])
        ) / 3

        pd.options.mode.copy_on_write = True

        data.loc[:, "n_commits"] = data["n_commits"]  # THIS DOES NOTHING?
        data.loc[:, "pc_n_commits"] = (
            (
                data[["n_commits"]]
                / data[
                    ["n_commits"]
                ].sum()  # calc repo-individual's total N commits as pc of sum of repo's commits.
            )
            * 100
        )

        # create percentage of users' commits which fall into each category:
        # this creates human-readble version of these variables
        data.loc[:, "pc_HLs-tiny"] = (
            data["hattori_lanza_size_cat_tiny"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_HLs-sml"] = (
            data["hattori_lanza_size_cat_small"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_HLs-med"] = (
            data["hattori_lanza_size_cat_medium"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_HLs-lrg"] = (
            data["hattori_lanza_size_cat_large"].div(data["n_commits"], axis=0) * 100
        )

        data.loc[:, "pc_HL-fweng"] = (
            data["hattori_lanza_content_cat_forward_engineering"].div(
                data["n_commits"], axis=0
            )
            * 100
        )
        data.loc[:, "pc_HL-reeng"] = (
            data["hattori_lanza_content_cat_reengineering"].div(
                data["n_commits"], axis=0
            )
            * 100
        )
        data.loc[:, "pc_HL-corr"] = (
            data["hattori_lanza_content_cat_corrective_engineering"].div(
                data["n_commits"], axis=0
            )
            * 100
        )
        data.loc[:, "pc_HL-mgmt"] = (
            data["hattori_lanza_content_cat_management"].div(data["n_commits"], axis=0)
            * 100
        )
        data.loc[:, "pc_HL-empty"] = (
            data["hattori_lanza_content_cat_empty_message"].div(
                data["n_commits"], axis=0
            )
            * 100
        )
        data.loc[:, "pc_HL-nocat"] = (
            data["hattori_lanza_content_cat_no_categorisation"].div(
                data["n_commits"], axis=0
            )
            * 100
        )

        data.loc[:, "pc_V-doc"] = (
            data["vasilescu_category_doc"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-code"] = (
            data["vasilescu_category_code"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-confg"] = (
            data["vasilescu_category_config"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-build"] = (
            data["vasilescu_category_build"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-dvdoc"] = (
            data["vasilescu_category_devdoc"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-test"] = (
            data["vasilescu_category_test"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-meta"] = (
            data["vasilescu_category_meta"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-img"] = (
            data["vasilescu_category_img"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-l10n"] = (
            data["vasilescu_category_l10n"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-ui"] = (
            data["vasilescu_category_ui"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-media"] = (
            data["vasilescu_category_media"].div(data["n_commits"], axis=0) * 100
        )
        data.loc[:, "pc_V-nocat"] = (
            data["vasilescu_category_unknown"].div(data["n_commits"], axis=0) * 100
        )

        return data

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
            filename="sample_cleaned_data_with_interactions_",
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
                # "n_commits",  # dropping the older column, keeping commits_created as probably later
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
        filepath = Path(self.data_write_location, filestr)
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
            self.image_write_location,
            f"sample_languages_{self.current_date_info}.{save_type}",
        )
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")

    def create_clustering_data_from_sample(
        self,
        clustering_variables: list[str],
        cleaned_data_with_interactions: pd.DataFrame,
    ):
        assert isinstance(
            clustering_variables, list
        ), f"clustering variables must be a list: please check input variables: {clustering_variables} which are of type {type(clustering_variables)}."
        clustering_data = cleaned_data_with_interactions[clustering_variables]
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

        X = clustering_data  # sample data, naming according to clustering/ML practices
        eval_chs = []
        eval_ns = []

        for n_clusters in range(2, max_clusters_to_eval + 1, 1):
            # range: start at 2 because need min of 2 clusters
            # end on max_clusters_to_eval number, increases by 1
            gc.collect()

            model = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric="euclidean",
                linkage="ward",
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

    def plot_eval_df(
        self,
        df: pd.DataFrame,
        file_name: str = "sample_CHscore_per_Ncluster_",
        save_type: str = "png",  # one of: ['png', 'pdf', 'svg']
    ):
        sns.barplot(data=df, x="N_clusters_evaluated", y="CH_score")
        plot_file = Path(
            self.image_write_location,
            f"{file_name}_{self.current_date_info}.{save_type}",
        )
        plt.title("Calinski-Harabasz Scores for different N Clusters")
        plt.savefig(fname=plot_file, format=save_type, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Plot saved out to file {plot_file}.")

    def do_clustering(
        self,
        clustering_data: pd.DataFrame,
        best_n_clusters: int,
        n_clusters_to_use: int | None = None,  # supply specific N of clusters to use.
    ) -> np.ndarray:
        gc.collect()  # free up space, just in case :)

        if n_clusters_to_use is not None:
            assert isinstance(
                n_clusters_to_use, int
            ), "If supplying a number of clusters to use, this must be an integer. Otherwise, the best_n_clusters will be used from evaluation steps."
            self.logger.info(
                f"Generating specific n of clusters: {n_clusters_to_use}, rather than best_n_clusters: {best_n_clusters}."
            )
            generate_clusters = n_clusters_to_use  # set the number to use
        else:
            generate_clusters = best_n_clusters
            self.logger.info(f"Generating best_n_clusters: {best_n_clusters}.")

        model = AgglomerativeClustering(
            n_clusters=generate_clusters, metric="euclidean", linkage="ward"
        )

        X = clustering_data
        self.logger.info(
            f"Attempting clustering with dataset shape {clustering_data.shape} and {len(clustering_data.columns)} columns: {clustering_data.columns}."
        )

        # fit the hierarchical clustering algorithm to dataset X
        model_predictions = model.fit_predict(X)
        # create the cluster_labels vector showing which cluster
        # each repo-individual belongs to
        cluster_labels = model_predictions

        return cluster_labels

    def label_clustering_data(
        self,
        cluster_labels: np.ndarray,
        cleaned_data_with_interactions: pd.DataFrame,
    ) -> pd.DataFrame:
        cleaned_data_with_interactions = cleaned_data_with_interactions.reset_index(
            drop=True
        )

        labelled_data = pd.concat(
            [
                pd.DataFrame({"cluster_labels": cluster_labels}),
                cleaned_data_with_interactions,
            ],
            axis=1,
        )

        # write out dataset used for clustering:
        self.writeout_data_to_csv(
            labelled_data,
            "clustered_sample_data_with_labels_",
        )
        return labelled_data

    def get_feature_importance(
        self,
        clustering_data: pd.DataFrame,
        clustering_variables: list,
    ) -> pd.DataFrame:
        if isinstance(clustering_data, pd.DataFrame):
            assert (
                clustering_data.empty is False
            ), "Dataframe data is empty; check inputs."

        self.logger.info(f"clustering data is df, with shape: {clustering_data.shape}.")

        self.logger.info(
            "Re-applying PCA and gathering PCA values from clustering data."
        )
        PCA_3 = PCA(n_components=3)
        PCA_3_df = pd.DataFrame(
            data=PCA_3.fit_transform(clustering_data),
            columns=[
                "principal component 1",
                "principal component 2",
                "principal component 3",
            ],
        )
        # write out PCA eigenvalues to csv:
        self.writeout_data_to_csv(
            PCA_3_df,
            "sample_PCA_eigenvalues_per_repo-individual_",
        )

        self.logger.info(
            f"Gathering feature importance values for each variable involved in clustering. These were: {clustering_variables}"
        )
        PCA_feature_importance = pd.DataFrame(
            PCA_3.components_,
            columns=PCA_3.feature_names_in_,
            index=["PCA_1", "PCA_2", "PCA_3"],
        )
        PCA_feature_importance["PCA"] = PCA_feature_importance.index
        PCA_feature_importance = PCA_feature_importance.reset_index(drop=True)

        PCA_variables_reshape = pd.melt(
            PCA_feature_importance,
            id_vars=["PCA"],
            value_vars=clustering_variables,
            var_name="variable_involved",
            value_name="PCA_importance_value",
        )
        PCA_features = PCA_variables_reshape.sort_values(
            by=["PCA", "PCA_importance_value"], ascending=[True, False]
        )
        PCA_features["rank"] = PCA_features.groupby("PCA")["PCA_importance_value"].rank(
            method="max",
            ascending=False,
        )
        top_PCA1_var = PCA_features.query("rank == 1 and PCA == 'PCA_1'")[
            "variable_involved"
        ].item()
        top_PCA1_value = PCA_features.query("rank == 1 and PCA == 'PCA_1'")[
            "PCA_importance_value"
        ].item()

        top_PCA2_var = PCA_features.query("rank == 1 and PCA == 'PCA_2'")[
            "variable_involved"
        ].item()
        top_PCA2_value = PCA_features.query("rank == 1 and PCA == 'PCA_2'")[
            "PCA_importance_value"
        ].item()

        top_PCA3_var = PCA_features.query("rank == 1 and PCA == 'PCA_3'")[
            "variable_involved"
        ].item()
        top_PCA3_value = PCA_features.query("rank == 1 and PCA == 'PCA_3'")[
            "PCA_importance_value"
        ].item()

        self.logger.info("PCA feature importances ranked:")
        self.logger.info(
            f"PCA1 mainly explained by {top_PCA1_var} with importance value {top_PCA1_value}."
        )
        self.logger.info(
            f"PCA2 mainly explained by {top_PCA2_var} with importance value {top_PCA2_value}."
        )
        self.logger.info(
            f"PCA3 mainly on {top_PCA3_var} with importance value {top_PCA3_value}."
        )

        # write out PCA importance rankings to csv:
        self.writeout_data_to_csv(
            PCA_features,
            "sample_feature_importance_data_",
        )
        return PCA_features

    def analysis_workflow(
        self,
        data: pd.DataFrame,
        subset_repos_file: str | Path,
        pc_subset: int,
        interactions_data_file: str | Path,
        repo_stats_file: str | Path,
        max_clusters_to_eval: int = 10,
        n_clusters_to_use: int | None = None,
    ):
        # if data is file:

        # if data is df:
        if isinstance(data, pd.DataFrame):
            assert data.empty is False, "Dataframe data is empty; check inputs."
            self.logger.info(f"data is df, with shape: {data.shape}.")

        self.logger.info(
            f"Before subsetting: Number of unique gh_usernames in sample is: {data.groupby('gh_username').ngroups}."
        )
        self.logger.info(
            f"Before subsetting: Number of gh_usernames appearing in more than one repository in this sample is: {len(data.groupby('gh_username')[['repo_name']].count().reset_index(names=['gh_username', 'count']).query('repo_name > 1'))}."
        )

        self.logger.info(
            f"Before subsetting: Number of repo-individuals (repo_name plus gh_username combos) in sample is: {data.groupby(['repo_name', 'gh_username']).ngroups}."
        )
        self.logger.info(
            f"Before subsetting: Number of repositories in sample is: {data.groupby('repo_name').ngroups}."
        )

        # if subset_repos_file is not None:
        if subset_repos_file is not None:
            data = self.subset_sample_to_repos(
                data,
                subset_repos_file=subset_repos_file,
                subset_pc=pc_subset,
            )
        # read in file of repos
        # subset data df to include only repo_names from file
        # otherwise use complete data df.

        self.writeout_data_to_csv(
            data,
            filename="sample_post-subset_data_",
        )

        interactions_data_file = Path(self.data_read_location, interactions_data_file)
        repo_stats_file = Path(self.data_read_location, repo_stats_file)

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
        self.writeout_data_to_csv(
            cleaned_data,
            filename="sample_cleaned_data_",
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
            subset_pc=pc_subset,
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

        clustering_variables = [  # THIS IS IMPORTANT: THESE WILL BE USED FOR CLUSTERING AND PCA VARIABLE FEATURE RANKING
            "pc_commit_created",
            "pc_issue_created",
            "pc_issue_closed",
            "pc_issues_assigned_of_assigned",
            "pc_pull_request_created",
            "pc_DC",
            "pc_sum_n_interactions",
            "pc_interaction_days",
            "pc_created-closed_issues",
        ]
        self.logger.info(
            f"Data will be clustered on the following {len(clustering_variables)} variables: {clustering_variables}."
        )

        clustering_data = self.create_clustering_data_from_sample(
            clustering_variables=clustering_variables,
            cleaned_data_with_interactions=cleaned_data_with_interactions,
        )

        self.writeout_data_to_csv(clustering_data, filename="sample_clustering_data")
        # clustering
        self.logger.info(f"Clustering dataset has shape {clustering_data.shape}")
        # plot dendrogram
        # save out
        dendrogrammer = Dendrogrammer(
            in_notebook=self.in_notebook,
            logger=self.logger,
            image_write_location=self.image_write_location,
        )
        dendrogrammer.plot_dendrogram(
            clustering_data=clustering_data,
            colours=["#D50032", "#1D2A3D", "#FDBC42"],
        )

        # clustering:
        # run clustering with diff N of clusters and calculate calinski_harabasz score to evaluate
        # log out n of clusters, ch scores, etc
        eval_CHs = self.evaluate_n_clusters(
            clustering_data=clustering_data,
            max_clusters_to_eval=max_clusters_to_eval,
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
            f"Calinski-Harabasz Score evaluation of {max_clusters_to_eval} clusters shows best number of clusters for sample is {best_n_clusters} with score {eval_CHs.loc[eval_CHs['CH_score'].idxmax(), 'CH_score']}."
        )
        self.plot_eval_df(eval_CHs)  # plot the evaluation CH Scores

        # run actual clustering with best N of clusters
        # write out clustering data
        # apply cluster_labels to original data (cleaned_data_with_interactions)
        cluster_labels = self.do_clustering(
            clustering_data=clustering_data,
            best_n_clusters=int(best_n_clusters),
            n_clusters_to_use=n_clusters_to_use,
        )

        labelled_data = self.label_clustering_data(
            cluster_labels=cluster_labels,
            cleaned_data_with_interactions=cleaned_data_with_interactions,
        )

        # log cluster number, sizes of n_repo_individuals, n_repos, distribution, etc.
        n_clusters = labelled_data.groupby("cluster_labels").ngroups
        self.logger.info(
            f"Applied {n_clusters} cluster labels to dataset to create labelled dataset of shape: {labelled_data.shape}."
        )
        # means for key variables by cluster

        # # create upset plot for interaction combinations
        # upsetplotter = UpsetPlotter(
        #     in_notebook=self.in_notebook,
        #     logger=self.logger,
        # )
        # self.logger.info("{Plotting single combined sample UpSet Plot")
        # upsetplotter.plot_upset_plot_interaction_combinations(
        #     separate_by_clusters=False,
        #     data=labelled_data,
        #     sort_combos_by="cardinality",
        #     file_name="sample_upset_plot_",
        #     save_type="pdf",  # one of: ['png', 'pdf', 'svg']
        # )

        # self.logger.info("Plotting separate clusters into UpSet Plot")
        # upsetplotter.plot_upset_plot_interaction_combinations(
        #     separate_by_clusters=True,
        #     data=labelled_data,
        #     sort_combos_by="cardinality",
        #     file_name="sample_upset_plot_",
        #     save_type="pdf",  # one of: ['png', 'pdf', 'svg']
        # )

        # PCA: run PCA to assess how variance is distributed
        # plot 3D
        plotpca = PlotPCA(
            in_notebook=self.in_notebook,
            logger=self.logger,
            image_write_location=self.image_write_location,
        )
        # plot 2D
        plotpca.plot_twodim_PCA(
            cluster_labels=cluster_labels,
            clustering_data=clustering_data,
        )
        plotpca.plot_threedim_PCA(
            cluster_labels=cluster_labels,
            clustering_data=clustering_data,
        )

        # log out PCA axis importance and variable importances per PCA axis
        self.logger.info(
            "Generating feature importance ranking for PCA via clustering data."
        )
        self.get_feature_importance(
            clustering_data=clustering_data, clustering_variables=clustering_variables
        )


parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--data-file",
    metavar="DATA",
    help="filename of main commits and issues datafile e.g merged-data-per-dev_x2868-repos_2025-05-10.csv",
    type=str,
    default="merged-data-per-dev_x2868-repos_2025-05-10.csv",
)
parser.add_argument(
    "-s",
    "--subset-file",
    metavar="SUBSET",
    type=str,
    help="File containing repo names to subset sample to; e.g. study-sample-repo-names_2025-05-01_x2981.txt",
    default="study-sample-repo-names_2025-05-01_x2981.txt",
)
parser.add_argument(
    "-p",
    "--pc-subset-repos",
    metavar="PC_SUBSET",
    help="Percentage of repos from subset file e.g. 100",
    type=int,
    default=100,
)
parser.add_argument(
    "-i",
    "--interactions-file",
    metavar="INTERACTIONS",
    type=str,
    help="File containing interaction data; e.g. merged-interactions-data-per-dev_x2946-repos_2025-05-11.csv",
    default="merged-interactions-data-per-dev_x2946-repos_2025-05-11.csv",
)
parser.add_argument(
    "-r",
    "--repo-stats-file",
    metavar="REPO_STATS",
    help="Summarised repo stats file; e.g. summarised_repo_stats_2025-05-01.csv",
    type=str,
    default="summarised_repo_stats_2025-05-01.csv",
)
parser.add_argument(
    "-m",
    "--max-n-clusters",
    metavar="MAX_CLUSTERS",
    help="Maximum number of clusters to evaluate for CH scores; e.g. 10",
    type=int,
    default=10,
)
parser.add_argument(
    "-n",
    "--n-clusters",
    metavar="N_CLUSTERS",
    help="Final number of clusters to generate; e.g. 5",
    type=int,
    required=False,
)
parser.add_argument(
    "-z",
    "--dataset-run-name",
    metavar="RUN_NAME",
    help="Tag required for dataset name generating writeout folder",
    type=str,
    required=True,
)


def main():
    args = parser.parse_args()
    data_arg: str = args.data_file
    subset_arg: str = args.subset_file
    pc_subset_repos_arg: int = args.pc_subset_repos
    interactions_arg: str = args.interactions_file
    repo_stats_arg: str = args.repo_stats_file
    max_clusters_arg: int = args.max_n_clusters
    n_clusters_arg: int | None = args.n_clusters
    run_name_arg: str = args.dataset_run_name

    dataanalyser = DataAnalyser(in_notebook=False, dataset_name=run_name_arg)

    dataanalyser.logger.info(
        f"""
        Running Data Analysis with arguments: {args}; 
        data: {data_arg}; 
        run name: {run_name_arg}; 
        subset to: {subset_arg}; 
        percentage of subset to use: {pc_subset_repos_arg};
        interactions: {interactions_arg}; 
        repo_stats summary data: {repo_stats_arg}; 
        max number of clusters to eval: {max_clusters_arg}; 
        number of clusters to use: {n_clusters_arg}; .
        """
    )

    # dataanalyser.read_location
    data_df = pd.read_csv(
        Path(dataanalyser.data_read_location, data_arg),
        header=0,
        low_memory=False,
    )
    try:
        dataanalyser.analysis_workflow(
            data=data_df,
            subset_repos_file=subset_arg,
            pc_subset=pc_subset_repos_arg,
            interactions_data_file=interactions_arg,
            repo_stats_file=repo_stats_arg,
            max_clusters_to_eval=max_clusters_arg,
            n_clusters_to_use=n_clusters_arg,
        )
    except Exception as e:
        dataanalyser.logger.error(
            f"Problem running data analysis workflow: {e}; arguments were: {args}."
        )
        raise RuntimeError


if __name__ == "__main__":
    main()
