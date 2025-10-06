# from sklearn.datasets import fetch_openml
from logging import Logger
from sklearn.model_selection import train_test_split

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import scipy.stats as stats
import warnings
# from typing import Literal


from sklearn.ensemble import (
    #    AdaBoostClassifier,
    #    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn import metrics
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import f1_score, precision_score
from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import GridSearchCV

from sklearn.model_selection import RandomizedSearchCV

from githubanalysis.analysis.baby_ML_pipeline import (
    ML_Pipeline_Decision_Tree,
    update_candidate_features,
)
from githubanalysis.setup_classes import DatasetSetup


TEST_SIZE = 0.2
RANDOM_STATE = 42
CLUSTERING_VARIABLES = [  # THIS IS IMPORTANT: THESE WILL BE USED FOR CLUSTERING AND PCA VARIABLE FEATURE RANKING
    "pc_commit_created",
    "pc_issue_created",
    "pc_issue_closed",
    "pc_issues_assigned_of_assigned",
    "pc_pull_request_created",
    "pc_pull_request_closed",
    "MRC",
    "pc_sum_n_interactions",
    "pc_interaction_days",
    "pc_created-closed_issues",
]  # read from file in future perhaps?


class HyperParams:  # Ananya's!
    def __init__(self, depth=10, trees=20, samples=20, criterion="gini", features=None):
        self.depth = depth
        self.trees = trees
        self.samples = samples
        self.criterion = criterion
        self.features = features

    def __str__(self):
        return "max_depth: {}; n_estimators: {}, n_samples: {}, criterion: {} features: {}".format(
            self.depth, self.trees, self.samples, self.criterion, self.features
        )


class TuningSetup(DatasetSetup):
    def _log_name(self) -> str:
        return "ML_tuning"

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.ml_pipeline_dt = ML_Pipeline_Decision_Tree(
            dataset_name=dataset_name,
            in_notebook=in_notebook,
            exists_ok=exists_ok,
            logger=logger,
        )
        self.model_type = "random_forest"
        self.le = LabelEncoder()
        self.ml_pipeline_dt.le = LabelEncoder()

    def prep_data(
        self,
        N_OBS: int = 10000,
        filename="sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv",
    ):
        data_file = Path(
            self.data_location,
            filename,
        )
        classified_df = pd.read_csv(
            data_file,
            header=0,
            low_memory=False,
        )

        if "pc_DC" in classified_df.columns:
            classified_df = classified_df.rename(
                columns={"pc_DC": "MRC", "breadth_interactions": "UIT"}
            )

        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "ephemeral_contributor", "Ephemeral Contributor"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "occasional_contributor", "Occasional Contributor"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "project_organiser", "Project Organiser"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "moderate_contributor", "Moderate Contributor"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "low-process_closer", "Low-Process Closer"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "low-coding_closer", "Low-Coding Closer"
        )
        classified_df["RSE_persona"] = classified_df["RSE_persona"].str.replace(
            "active_contributor", "Active Contributor"
        )

        classified_df = classified_df.sample(
            n=N_OBS,
            frac=None,
            replace=False,
            weights=None,
            random_state=42,
            axis=None,
            ignore_index=False,
        )

        self.RSE_info = {
            "data": classified_df[
                CLUSTERING_VARIABLES
            ].to_numpy(),  # data w/o labels, list per row
            "target": self.le.fit_transform(
                classified_df["RSE_persona"]
            ),  # numerical version of class assignment
            "feature_names": CLUSTERING_VARIABLES,
            "target_names": classified_df["RSE_persona"].unique(),
        }

        print(self.RSE_info["data"].shape)
        assert self.RSE_info["data"].shape == N_OBS, (
            "Size of RSE_info data doesn't match N_OBS"
        )
        N_FEATURES = self.RSE_info["data"].shape[1]
        self.n_feats = N_FEATURES
        print(N_FEATURES)
        # no return as saved RSE_info to self.ml_pipeline_dt

    def n_feats_around_optimal(self) -> list[int | None]:
        # self.ml_pipeline_dt.RSE_info["data"].shape[1]

        lit_optimal_feats = update_candidate_features(self.n_feats)
        print(lit_optimal_feats)

        min_feats = 2  # at least two required for choosing

        feat_range = list[int | None](range(min_feats, lit_optimal_feats + 3))

        assert max(i for i in feat_range if i is not None) <= self.n_feats
        # feat_range: list[int | None] = feat_range
        print(feat_range)
        feat_range.append(None)
        print(feat_range)
        return feat_range

    def setup_test_train(self):
        # set X (data, no colnames, no personas), y (personas only)
        X, y = (
            self.ml_pipeline_dt.RSE_info["data"],
            self.ml_pipeline_dt.RSE_info["target"],
        )

        # create testing/training dataset
        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = train_test_split(
            X,
            y,
            # test_size, #=test_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 25%
            # train_size, #=train_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 75%
            random_state=42,
            shuffle=True,  # shuffle_state,  # True by (sklearn) default
            stratify=self.ml_pipeline_dt.RSE_info[
                "target"
            ],  # same as y; None by (sklearn) default
        )
        self.X_train = X_train  # type: ignore
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        # add size info from test and training datasets to self for future reporting.
        self.X_train_size = self.X_train.shape
        self.y_train_size = self.y_train.shape
        self.X_test_size = self.X_test.shape
        self.y_test_size = self.y_test.shape

        print(f"{self.X_train_size = }")
        print(f"{self.X_test_size = }")
        # no return as all saved to self.

    # Ref: https://scikit-learn.org/stable/auto_examples/model_selection/plot_randomized_search.html
    # Utility function to report best scores
    def report(self, results, n_top=3):
        for i in range(1, n_top + 1):
            candidates = np.flatnonzero(results["rank_test_score"] == i)
            for candidate in candidates:
                print("Model with rank: {0}".format(i))
                print(
                    "Mean validation score: {0:.3f} (std: {1:.3f})".format(
                        results["mean_test_score"][candidate],
                        results["std_test_score"][candidate],
                    )
                )
                print("Parameters: {0}".format(results["params"][candidate]))
                print("")

    def param_searching(
        self,
    ):
        feat_range = self.n_feats_around_optimal()
        params = {
            "n_estimators": [75, 100, 125, 150, 175],
            "criterion": ["gini", "entropy", "log_loss"],
            "min_samples_split": range(2, 50),
            "max_depth": [3, 4, 6, 8, 10, 35],
            "max_samples": stats.uniform(0, 1),
            "max_features": feat_range,
        }

        N_CORES = joblib.cpu_count(only_physical_cores=True)
        print(f"Number of physical cores: {N_CORES}")

        clf = RandomForestClassifier(
            bootstrap=True,
            oob_score=True,
            max_leaf_nodes=None,
            ccp_alpha=0.0,
            class_weight=None,
            n_jobs=(N_CORES - 1),
        )
        rskf = RepeatedStratifiedKFold(
            n_splits=5,  # 5 is default
            n_repeats=10,  # 10 is default
            random_state=None,  # None is default
        )

        search = RandomizedSearchCV(
            clf,
            n_iter=25,  # controls 'combination of parameters'
            param_distributions=params,
            scoring="accuracy",
            cv=rskf.split(self.X_train, self.y_train),  # None: default 5-fold #
            n_jobs=(N_CORES - 1),
            verbose=2,
            random_state=None,  # default=None
        )

        # To ignore the warning about the OOB
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            search.fit(self.X_train, self.y_train)
            self.report(search.cv_results_, 5)  # Report the top 10 results
            best_params = HyperParams(
                depth=search.best_params_["max_depth"],
                trees=search.best_params_["n_estimators"],
                criterion=search.best_params_["criterion"],
                samples=search.best_params_["max_samples"],
                features=search.best_params_["max_features"],
            )
            print("Best score {:.2f} with:".format(search.best_score_))
            print(best_params)

        # run full model with the best params! :D
        selected_rfc = RandomForestClassifier(
            max_depth=best_params.depth,
            n_estimators=best_params.trees,
            criterion=best_params.criterion,  # type: ignore
            max_samples=best_params.samples,
            max_features=best_params.features,  # type: ignore
            oob_score=True,
        ).fit(self.X_train, self.y_train)

        y_pred = selected_rfc.predict(self.X_test)
        self.y_true = self.y_test

        true_df = pd.DataFrame(
            {
                "Test true": self.y_test,
                "Test predicted": y_pred,
            }
        )

        filename_out = (
            f"test_prediction_data_N{self.y_test_size}_{self.current_date_info}.csv"
        )
        save_out = Path(self.data_location, filename_out)
        true_df.to_csv(save_out, header=True, index=False)

        # features = train_in.iloc[:, select.get_support(indices=True)]  # Alt to using transform that preserves the name
        # features = features.columns
        # features = selected_train_in.columns
        feature_importances = selected_rfc.feature_importances_

        str_headers = "|"
        str_underline = "|"
        str_row = "|"
        for idx in range(len(self.n_feats)):
            str_headers += " {} [%] | ".format(self.n_feats[idx])
            str_underline += " {} | ".format("-" * (len(self.n_feats[idx]) + 4))
            str_row += (
                " "
                + ("{:.2f}".format(100.0 * feature_importances[idx])).center(
                    len(self.n_feats[idx]) + 4
                )
                + " | "
            )

        feature_imp = str_headers + "\n" + str_underline + "\n" + str_row

        print(
            f"""
            For Random Forest model trained on: \n
            datafile: sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv \n
            training-set size: N={self.X_train_size[0]} \n
            and evaluated using test-set size: N={self.X_test_size[0]} repo-individuals \n
            using N={self.X_test_size[1]} features \n 
            with N={best_params.trees} trees in forest  \n
            at {self.current_date_info} \n 
            with parameters: {selected_rfc.get_params(deep=False)} \n
            and feature importances: \n
            {feature_imp}
        """
        )

        # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score
        print(
            "Accuracy: {:.3f} (percent of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred),
            )
        )
        print(
            "Non-Normalised Accuracy: {:.0f} (number of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred, normalize=False),
            )
        )
        print(
            "Balanced Accuracy: {:.3f} (the average of recall obtained on each class)".format(
                metrics.balanced_accuracy_score(
                    self.y_true,
                    y_pred,
                    adjusted=False,
                )
            )
        )
        print(
            "F1 Score: {:.3f} (harmonic mean of the precision and recall, both equally weighted)".format(
                metrics.f1_score(
                    self.le.inverse_transform(self.y_true),  # y_true
                    self.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                    # labels=ml_pipeline_dt.RSE_info["target"],
                    # target_names=ml_pipeline_dt.RSE_info["target"],
                )
            )
        )
        print(
            "Precision: {:.3f} (Ratio of correctly predicted positive classes to total of positive predictions)".format(
                metrics.precision_score(
                    self.le.inverse_transform(self.y_true),  # y_true
                    self.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                    # labels=ml_pipeline_dt.RSE_info["target"],
                    # target_names=ml_pipeline_dt.RSE_info["target"],
                )
            )
        )
        print(
            "Recall: {:.3f} (Ratio of correctly predicted positive classes to all actual 'real' positive classes)".format(
                metrics.recall_score(
                    self.le.inverse_transform(self.y_true),  # y_true
                    self.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                    # labels=ml_pipeline_dt.RSE_info["target"],
                    # target_names=ml_pipeline_dt.RSE_info["target"],
                ),
            )
        )
        return (
            f1_score(y_true=self.y_test, y_pred=y_pred, average="macro"),
            # f1_score(y_true=unseen_out, y_pred=unseen_pred, average="macro"),
            precision_score(y_true=self.y_test, y_pred=y_pred, average="macro"),
            # precision_score(y_true=unseen_out, y_pred=unseen_pred, average="macro"),
            selected_rfc.score(self.y_test, y_pred),
            # selected_rfc.score(select.transform(unseen_in), unseen_out),
            best_params,
            feature_imp,
        )


def main():
    tuning_setup = TuningSetup(
        dataset_name="ML_tune",
        in_notebook=False,
        exists_ok=True,
        logger=None,
    )
    print("prepping dataset")
    tuning_setup.prep_data()
    print("splitting dataset")
    tuning_setup.setup_test_train()
    print("searching for params")
    tuning_setup.param_searching()


if __name__ == "__main__":
    main()
