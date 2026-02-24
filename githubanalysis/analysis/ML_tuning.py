# from sklearn.datasets import fetch_openml
from logging import Logger
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import scipy.stats as stats
import warnings
import time
from typing import Literal
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass, asdict
# from sklearn.model_selection import *


from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
    GradientBoostingClassifier,
)
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import f1_score, precision_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
from sklearn.experimental import enable_halving_search_cv  # noqa
from sklearn.model_selection import (
    RandomizedSearchCV,
    GridSearchCV,
    HalvingGridSearchCV,  # noqa
)

from githubanalysis.analysis.ML_pipeline import (
    ML_Pipeline_Decision_Tree,
    update_candidate_features,
)
from githubanalysis.setup_classes import DatasetSetup

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


@dataclass
class HyperParamsRF:  # credit to Ananya & David
    # taken from v1.3.0 https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
    n_estimators: int = 100
    criterion: Literal["gini", "entropy", "log_loss"] = "gini"
    max_depth: int | None = None
    min_samples_split: int | float = 2
    min_samples_leaf: int | float = 1
    min_weight_fraction_leaf: float = 0.0
    max_features: Literal["sqrt", "log2", None] | int | float = "sqrt"
    max_leaf_nodes: int | None = None
    min_impurity_decrease: float = 0.0
    bootstrap: bool = True
    oob_score: bool = True  # bool or callable, default=False
    n_jobs: int | None = None
    random_state: int | None = None  # int, RandomState instance or None, default=None
    verbose: int = 2
    warm_start: bool = False
    class_weight: Literal["balanced", "balanced_subsample"] | None = (
        None  # {“balanced”, “balanced_subsample”}, dict or list of dicts, default=None
    )
    ccp_alpha: float = 0.0  # non-negative float, default=0.0
    max_samples: int | float | None = (
        None  # the number of samples to draw from X to train each base estimator.
    )
    # monotonic_cst: int | None = (
    #     None  # array-like of int of shape (n_features), default=None
    # ) # v1.4 onwards


@dataclass
class HyperParamsHGBT:
    loss: str = "log_loss"
    learning_rate: float = 0.1
    max_iter: int = 100  # forest size
    max_leaf_nodes: int | None = 31
    max_depth: int | None = None
    min_samples_leaf: int = 20
    l2_regularization: float = 0.0
    # max_features: float = 1.0 # added in v 1.4!
    max_bins: int = 255
    categorical_features: str | None = (
        None  # array-like of {bool, int, str} of shape (n_features) or shape (n_categorical_features,), default=’from_dtype’
    )
    monotonic_cst: int | None = (
        None  # array-like of int of shape (n_features) or dict, default=None
    )
    interaction_cst: None = None  # {“pairwise”, “no_interactions”} or sequence of lists/tuples/sets of int, default=None
    warm_start: bool = False
    early_stopping: str | bool = "auto"
    scoring: str | None = "loss"
    validation_fraction: float | int | None = 0.1
    n_iter_no_change: int = 10
    tol: float = 1e-07
    verbose: int = 2
    random_state: int | None = None
    class_weight: str | None = (
        None  # dict or ‘balanced’, default=None # TODO: adjust this typing so that dicts can be used!
    )


class BaseTuningSetup(DatasetSetup):
    def _log_name(self) -> str:
        return f"ML_tuning_{self.SEARCH_METHOD}"

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        N_JOBS: int,
        exists_ok: bool = False,
        logger: None | Logger = None,
        ML_CLASS: str = "RF",
        N_OBS: int = 10000,
        N_ITER: int = 50,
        RANDOM_STATE: int = 42,
        SEARCH_METHOD: str = "RandomizedSearchCV",
    ) -> None:
        self.SEARCH_METHOD = SEARCH_METHOD
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.ml_pipeline_dt = ML_Pipeline_Decision_Tree(
            dataset_name=dataset_name,
            in_notebook=in_notebook,
            exists_ok=exists_ok,
            logger=logger,
        )
        self.ML_CLASS = ML_CLASS
        assert self.ML_CLASS in [
            "RF",
            "HGBT",
            "GBT",
        ]
        self.le = LabelEncoder()
        self.N_OBS = N_OBS
        self.N_ITER = N_ITER
        self.RANDOM_STATE = RANDOM_STATE
        assert self.SEARCH_METHOD in [
            "RandomizedSearchCV",
            "GridSearchCV",
            "HalvingGridSearchCV",
        ]
        self.N_JOBS = N_JOBS
        # self.SEARCH_METHOD options should match names of selected hyper-parameter optimisers from here: https://scikit-learn.org/stable/api/sklearn.model_selection.html#hyper-parameter-optimizers

    def prep_data(
        self,
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
            n=self.N_OBS,
            frac=None,
            replace=False,
            weights=None,
            random_state=self.RANDOM_STATE,
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

        self.logger.info(self.RSE_info["data"].shape)
        assert self.RSE_info["data"].shape[0] == self.N_OBS, (
            f"Size of RSE_info data doesn't match N_OBS: {self.RSE_info['data'].shape[0]} vs {self.N_OBS}"
        )
        N_FEATURES = self.RSE_info["data"].shape[1]
        self.n_feats = N_FEATURES
        self.logger.info(N_FEATURES)
        # no return as saved RSE_info to self

    def n_feats_around_optimal(self) -> list[int | None]:
        lit_optimal_feats = update_candidate_features(self.n_feats)
        self.logger.info(lit_optimal_feats)

        min_feats = 2  # at least two required for choosing

        feat_range = list[int | None](range(min_feats, lit_optimal_feats + 2))

        assert max(i for i in feat_range if i is not None) <= self.n_feats
        # feat_range: list[int | None] = feat_range
        self.logger.info(feat_range)
        feat_range.append(None)
        self.logger.info(feat_range)
        return feat_range

    def setup_test_train(self):
        # set X (data, no colnames, no personas), y (personas only)
        X, y = (
            self.RSE_info["data"],
            self.RSE_info["target"],
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
            random_state=self.RANDOM_STATE,
            shuffle=True,  # shuffle_state,  # True by (sklearn) default
            stratify=self.RSE_info["target"],  # same as y; None by (sklearn) default
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

        self.logger.info(f"{self.X_train_size = }")
        self.logger.info(f"{self.X_test_size = }")
        # no return as all saved to self.

    # Ref: https://scikit-learn.org/stable/auto_examples/model_selection/plot_randomized_search.html
    # Utility function to report best scores
    def report(self, results, n_top=3):
        for i in range(1, n_top + 1):
            candidates = np.flatnonzero(results["rank_test_score"] == i)
            for candidate in candidates:
                self.logger.info("Model with rank: {0}".format(i))
                self.logger.info(
                    "Mean validation score: {0:.5f} (std: {1:.5f})".format(
                        results["mean_test_score"][candidate],
                        results["std_test_score"][candidate],
                    )
                )
                self.logger.info("Parameters: {0}".format(results["params"][candidate]))
                self.logger.info("")


class AbstractParamSearch(ABC):
    def __init__(self, base_tuning_setup: BaseTuningSetup) -> None:
        self.base_tuning_setup = base_tuning_setup
        self.rskf = RepeatedStratifiedKFold(  # THIS step will be repeated for all the ML models.
            n_splits=5,  # 5 is default
            n_repeats=10,  # 10 is default
            random_state=self.base_tuning_setup.RANDOM_STATE,  # None is default
        )
        self.base_tuning_setup.logger.info("rskf declared")
        self.N_CORES = self.base_tuning_setup.N_JOBS  # input from commandline param

    @abstractmethod
    def if_randomized_searching(self) -> RandomizedSearchCV | None: ...

    @abstractmethod
    def if_grid_searching(self) -> GridSearchCV | None: ...

    @abstractmethod
    def if_halving_grid_searching(self) -> HalvingGridSearchCV | None: ...

    def decide_which_hyper_param_method(self) -> Any:
        if self.base_tuning_setup.SEARCH_METHOD == "RandomizedSearchCV":
            search = self.if_randomized_searching()
        elif self.base_tuning_setup.SEARCH_METHOD == "GridSearchCV":
            search = self.if_grid_searching()
        elif self.base_tuning_setup.SEARCH_METHOD == "HalvingGridSearchCV":
            search = self.if_halving_grid_searching()
        else:
            raise ValueError(
                f"SEARCH_METHOD is not of correct type; SEARCH_METHOD is {self.base_tuning_setup.SEARCH_METHOD} there was a problem"
            )
        return search

    @abstractmethod
    def param_searching(self) -> HyperParamsRF | HyperParamsHGBT | None: ...

    @abstractmethod
    def searched_params_fit_to_classifier(self) -> tuple | None: ...


class HGBTParamSearch(AbstractParamSearch):
    def __init__(self, base_tuning_setup) -> None:
        super().__init__(base_tuning_setup=base_tuning_setup)
        self.search_method = (self.base_tuning_setup.SEARCH_METHOD,)
        self.params = {
            # TESTED / SEARCHED PARAMS:
            "learning_rate": [
                0.01,
                0.02,
                0.05,
                0.1,
            ],  # default 0.1, can also use 0.01; # shrinkage param (lambda)
            "max_iter": [
                75,
                100,
                125,
                150,
                200,
            ],  # default=100, number of iterations/trees to generate; forest_size
            "max_leaf_nodes": [
                None,
                25,
                31,
                50,
                75,
            ],  # None= no max; default=31 for some reason?
            "min_samples_leaf": [
                20,
                10,
                5,
                2,
            ],  # default=20; minimum samples per leaf - in small datasets, it's worth lowering this or you get only shallow trees; # TODO: adjust this!
            "warm_start": [
                False,
                True,
            ],  # warm_start=False,  # if True reuse previous solution to fit/add estimators (True req retrain on same data only or -> invalidity!)
            "scoring": [
                "loss",
                "f1_macro",
            ],  # scoring to use w/ early stopping: 'str':*; a scorer callable; None:'accuracy' is used; 'loss'(default): checked with loss value; *=https://scikit-learn.org/stable/modules/model_evaluation.html#scoring-string-names;
            # DEFAULT PARAMS:
            "loss": [HyperParamsHGBT.loss],
            "max_depth": [HyperParamsHGBT.max_depth],
            "l2_regularization": [HyperParamsHGBT.l2_regularization],
            # "max_features": [HyperParamsHGBT.max_features],
            "max_bins": [HyperParamsHGBT.max_bins],
            "categorical_features": [HyperParamsHGBT.categorical_features],
            "monotonic_cst": [HyperParamsHGBT.monotonic_cst],
            "interaction_cst": [HyperParamsHGBT.interaction_cst],
            "early_stopping": [HyperParamsHGBT.early_stopping],
            "validation_fraction": [HyperParamsHGBT.validation_fraction],
            "n_iter_no_change": [HyperParamsHGBT.n_iter_no_change],
            "tol": [HyperParamsHGBT.tol],
            "verbose": [HyperParamsHGBT.verbose],
            "random_state": [
                HyperParamsHGBT.random_state
            ],  # this is over-written in self.clf below
            "class_weight": [HyperParamsHGBT.class_weight],
        }
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        self.base_tuning_setup.logger.info(
            f"Number of physical cores: {self.base_tuning_setup.N_JOBS}"
        )
        assert self.base_tuning_setup.ML_CLASS == "HGBT", (
            f"There's been an issue, base_tuning_setup ML_CLASS is expected to be HGBT, but isn't... It's: {self.base_tuning_setup.ML_CLASS}"
        )
        self.clf = HistGradientBoostingClassifier(
            random_state=self.base_tuning_setup.RANDOM_STATE,
        )  # no other params set here as defaults are set in self.params!
        self.base_tuning_setup.logger.info(f"clf declared: {self.clf}")

    def if_randomized_searching(self):
        # print("if randomised searching for HGBT model")
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        search = RandomizedSearchCV(
            self.clf,  # estimator
            n_iter=self.base_tuning_setup.N_ITER,  # controls 'combination of parameters'
            param_distributions=self.params,  # dictionary of parameter keys and lists or distributions of parameter options to try
            scoring="f1_macro",
            cv=self.rskf.split(
                self.base_tuning_setup.X_train, self.base_tuning_setup.y_train
            ),  # None: default 5-fold #
            n_jobs=self.base_tuning_setup.N_JOBS,
            verbose=4,
            error_score=np.nan,  # np.nan=default; Value to assign to the score if an error occurs in estimator fitting
            random_state=self.base_tuning_setup.RANDOM_STATE,  # default=None # setting this to self.RANDOM_STATE defeats the point of using randomness, but may be more reproducable, surely?
            return_train_score=True,  # default=False.
        )
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using search settings: {search}."
        )
        return search

    def if_grid_searching(self):
        print("if grid searching for HGBT model")

    def if_halving_grid_searching(self):
        print("if halving-grid searching for HGBT model")

    def param_searching(self):
        # print("param searching happens here for HGBT model")
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using {self.base_tuning_setup.SEARCH_METHOD}."
        )

        search = self.decide_which_hyper_param_method()

        self.base_tuning_setup.logger.info("search declared")
        start_hyper_param_search = time.time()
        self.base_tuning_setup.logger.info("param timer started")

        with warnings.catch_warnings():
            warnings.simplefilter("once")
            try:
                search.fit(
                    self.base_tuning_setup.X_train, self.base_tuning_setup.y_train
                )
            except ValueError as e:
                self.base_tuning_setup.logger.error(f"Error in search.fit(): {e}")

            self.base_tuning_setup.report(
                search.cv_results_, n_top=5
            )  # Report the top 5 results

            self.base_tuning_setup.logger.info(
                f"Completed search.fit() and have best results: {search}"
            )

            param_search_results = pd.DataFrame(
                search.cv_results_
            )  # could use comparison approaches like https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html#sphx-glr-auto-examples-model-selection-plot-grid-search-stats-py on these

            best_params = HyperParamsHGBT(
                loss=search.best_params_["loss"],
                learning_rate=search.best_params_["learning_rate"],
                max_iter=search.best_params_["max_iter"],
                max_leaf_nodes=search.best_params_["max_leaf_nodes"],
                max_depth=search.best_params_["max_depth"],
                min_samples_leaf=search.best_params_["min_samples_leaf"],
                l2_regularization=search.best_params_["l2_regularization"],
                # max_features=search.best_params_["max_features"],
                max_bins=search.best_params_["max_bins"],
                categorical_features=search.best_params_["categorical_features"],
                monotonic_cst=search.best_params_["monotonic_cst"],
                interaction_cst=search.best_params_["interaction_cst"],
                warm_start=search.best_params_["warm_start"],
                early_stopping=search.best_params_["early_stopping"],
                scoring=search.best_params_["scoring"],
                validation_fraction=search.best_params_["validation_fraction"],
                n_iter_no_change=search.best_params_["n_iter_no_change"],
                tol=search.best_params_["tol"],
                verbose=search.best_params_["verbose"],
                random_state=search.best_params_["random_state"],
                class_weight=search.best_params_["class_weight"],
            )

            self.base_tuning_setup.logger.info(
                "Best score {:.5f} with:".format(
                    search.best_score_
                )  # params settings that gave best results on holdout data
            )
            self.base_tuning_setup.logger.info(
                best_params
            )  # parameter settings that gave the best results on the hold out data.
        end_hyper_param_search = time.time()
        hyper_param_search_time = end_hyper_param_search - start_hyper_param_search
        self.base_tuning_setup.logger.info(
            f"Hyper-Parameter search using {self.base_tuning_setup.SEARCH_METHOD} method for {self.base_tuning_setup.ML_CLASS} took {hyper_param_search_time} seconds for {self.base_tuning_setup.N_ITER} across {len(self.params)} parameter categories, across {search.n_splits_} cross-validation splits (folds/iterations) and refitting the best model took {search.refit_time_} seconds."
        )
        params_filename_out = f"{self.base_tuning_setup.ML_CLASS}_paramsearch_{self.base_tuning_setup.SEARCH_METHOD}_N{self.base_tuning_setup.y_test_size[0]}_{self.base_tuning_setup.current_date_info}.csv"
        params_save_out = Path(
            self.base_tuning_setup.data_location, params_filename_out
        )
        param_search_results.to_csv(params_save_out, header=True, index=False)
        self.base_tuning_setup.logger.info(
            f"Index of the best candidate parameter settings is: {search.best_index_}, in {params_save_out}"
        )
        return best_params

    def searched_params_fit_to_classifier(self):
        best_params = self.param_searching()

        start_selected_hgbtc_fit = time.time()
        self.base_tuning_setup.logger.info("fit timer started")
        # run full model with the best params for HGBT, with SOME specifics: verbose, random state
        selected_hgbtc = HistGradientBoostingClassifier(
            **asdict(
                best_params
            ),  # expand the dictionary created from best_params as arguments to the HGBT function :D
            # random_state=self.base_tuning_setup.RANDOM_STATE,  # controls the randomness of the estimator during splitting
            verbose=4,  # increased for 'best model fit' from candidate fits during search
        ).fit(self.base_tuning_setup.X_train, self.base_tuning_setup.y_train)
        end_selected_hgbtc_fit = time.time()
        selected_hgbtc_fit_time = end_selected_hgbtc_fit - start_selected_hgbtc_fit
        self.base_tuning_setup.logger.info(
            f"Selected Parameters HGBT model took {selected_hgbtc_fit_time} seconds to fit"
        )

        start_selected_hgbtc_predict = time.time()
        y_pred = selected_hgbtc.predict(self.base_tuning_setup.X_test)
        end_selected_hgbtc_predict = time.time()
        selected_hgbtc_predict_time = (
            end_selected_hgbtc_predict - start_selected_hgbtc_predict
        )
        self.y_true = self.base_tuning_setup.y_test
        self.base_tuning_setup.logger.info(
            f"Selected Parameters HGBT model took {selected_hgbtc_predict_time} seconds to predict"
        )

        true_df = pd.DataFrame(
            {
                "Test true": self.base_tuning_setup.y_test,
                "Test predicted": y_pred,
            }
        )

        filename_out = f"test_prediction_data_N{self.base_tuning_setup.y_test_size[0]}_{self.base_tuning_setup.current_date_info}.csv"
        save_out = Path(self.base_tuning_setup.data_location, filename_out)
        true_df.to_csv(save_out, header=True, index=False)

        # feature_importances = selected_hgbtc.feature_importances_

        self.base_tuning_setup.logger.info(
            f"""
            For {self.base_tuning_setup.ML_CLASS} model trained on: \n
            datafile: sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv \n
            with N observations (repo-individuals): {self.base_tuning_setup.N_OBS} \n
            hyper-parameter-searched with search method {self.base_tuning_setup.SEARCH_METHOD} \n 
            on {self.base_tuning_setup.N_ITER} iterations \n
            training-set size: N={self.base_tuning_setup.X_train_size[0]} \n
            and evaluated using test-set size: N={self.base_tuning_setup.X_test_size[0]} repo-individuals \n
            using N={self.base_tuning_setup.X_test_size[1]} features \n 
            with maximum of N={best_params.max_iter} trees iterated \n
            at {self.base_tuning_setup.current_date_info} \n 
            with parameters: {selected_hgbtc.get_params(deep=False)} \n
            and feature importances: 
        """
        )

        # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score
        self.base_tuning_setup.logger.info(
            "Accuracy: {:.5f} (percent of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred),
            )
        )
        self.base_tuning_setup.logger.info(
            "Non-Normalised Accuracy: {:.0f} (number of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred, normalize=False),
            )
        )
        self.base_tuning_setup.logger.info(
            "Balanced Accuracy: {:.5f} (the average of recall obtained on each class)".format(
                metrics.balanced_accuracy_score(
                    self.y_true,
                    y_pred,
                    adjusted=False,
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "F1 Score: {:.5f} (harmonic mean of the precision and recall, both equally weighted)".format(
                metrics.f1_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Precision: {:.5f} (Ratio of correctly predicted positive classes to total of positive predictions)".format(
                metrics.precision_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Recall: {:.5f} (Ratio of correctly predicted positive classes to all actual 'real' positive classes)".format(
                metrics.recall_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                ),
            )
        )
        # # multiclass means you can only be in one category only e.g. media format (film or tv-show)
        # # multilabel means you can have multiple labels applying to the same observation e.g. genre of media (horror, shark movie, animals)
        self.base_tuning_setup.logger.info(
            "Area Under the Receiver Operating Characteristic Curve (ROC AUC), (NB: calculated average='macro' and multiclass='ovr'): {:.5f}".format(
                roc_auc_score(
                    y_true=self.base_tuning_setup.y_test,  # y_true
                    y_score=selected_hgbtc.predict_proba(
                        self.base_tuning_setup.X_test
                    ),  # y_score
                    # y_true=y_test,
                    # y_score=pipeline_class_obj.pipe.named_steps["clf"].predict_proba(X_test),
                    average="macro",
                    multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                    # multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Area Under the Receiver Operating Characteristic Curve (ROC AUC), (NB: calculated average='macro' and multiclass='ovo'): {:.5f}".format(
                roc_auc_score(
                    y_true=self.base_tuning_setup.y_test,  # y_true
                    y_score=selected_hgbtc.predict_proba(
                        self.base_tuning_setup.X_test
                    ),  # y_score
                    average="macro",
                    # multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                    multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
                )
            )
        )

        classification_rep = metrics.classification_report(
            y_true=self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
            y_pred=self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
            zero_division=0,  # in later versions of sklearn options inc 0.0 or np.nan, here it's int.
            digits=5,
            # output_dict=True,  # default=False
        )
        self.base_tuning_setup.logger.info("\n")
        self.base_tuning_setup.logger.info(
            classification_rep
        )  # try this to avoid logger error with formatting of report
        self.base_tuning_setup.logger.info("Returning final results now:")
        return (
            selected_hgbtc,  # this is the actual model, but currently not using this output
            f1_score(
                y_true=self.base_tuning_setup.y_test, y_pred=y_pred, average="macro"
            ),
            precision_score(
                y_true=self.base_tuning_setup.y_test, y_pred=y_pred, average="macro"
            ),
            selected_hgbtc.score(
                self.base_tuning_setup.X_test, self.base_tuning_setup.y_test
            ),
            best_params,
            # feature_imp,
        )

    # next function would apply selected_rfc to a dataset to predict RSE Personas with it.


class GBTParamSearch(AbstractParamSearch):
    def __init__(self, base_tuning_setup) -> None:
        super().__init__(base_tuning_setup)
        self.search_method = (self.base_tuning_setup.SEARCH_METHOD,)

    def if_randomized_searching(self):
        print("if randomised searching for GBT model")

    def if_grid_searching(self):
        print("if grid searching for GBT model")

    def if_halving_grid_searching(self):
        print("if halving-grid searching for GBT model")

    def param_searching(self):
        self.decide_which_hyper_param_method()
        print("param searching happens here for GBT model")
        return None

    def searched_params_fit_to_classifier(self):
        self.param_searching()
        print(
            "returning model with best hyperparameters fitted, and results, for GBT model"
        )
        return None


class RFParamSearch(AbstractParamSearch):
    def __init__(
        self,
        base_tuning_setup: BaseTuningSetup,
    ) -> None:
        super().__init__(
            base_tuning_setup=base_tuning_setup,
        )
        self.search_method = (self.base_tuning_setup.SEARCH_METHOD,)
        self.params = {
            # TESTED / SEARCHED PARAMS:
            "n_estimators": [
                75,
                100,
                125,
                150,
            ],  # this does not need to go very high in RF....
            "criterion": ["gini", "entropy", "log_loss"],
            "max_depth": [10, 35, 50, None],  # prev: "max_depth": [3, 4, 6, 8, 10, 35],
            "min_samples_split": [2],  # prev: range(2, 50)
            "max_features": self.base_tuning_setup.n_feats_around_optimal(),
            "min_impurity_decrease": stats.uniform(
                0, 0.1
            ),  # node will be split if split induces a decrease of the impurity greater than or equal to this
            "ccp_alpha": stats.uniform(0, 0.25),  # 0 means no pruning.
            "max_samples": stats.uniform(
                0.01, 0.75
            ),  #  # prev 0.01, 1.0; if this is a float, it represents a percentage of the samples; this shouldn't start at 0 because then the max_samples can be none??
            # DEFAULT PARAMS:
            "min_samples_leaf": [HyperParamsRF.min_samples_leaf],
            "min_weight_fraction_leaf": [HyperParamsRF.min_weight_fraction_leaf],
            "max_leaf_nodes": [HyperParamsRF.max_leaf_nodes],
            "bootstrap": [HyperParamsRF.bootstrap],
            "oob_score": [HyperParamsRF.oob_score],
            "random_state": [
                HyperParamsRF.random_state
            ],  # this is over-written in self.clf below
            "verbose": [HyperParamsRF.warm_start],
            "warm_start": [HyperParamsRF.warm_start],
            "class_weight": [HyperParamsRF.class_weight],
        }
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        self.base_tuning_setup.logger.info(
            f"Number of physical cores: {self.base_tuning_setup.N_JOBS}"
        )
        assert self.base_tuning_setup.ML_CLASS == "RF", (
            f"There's been an issue, base_tuning_setup ML_CLASS is expected to be RF, but isn't... It's: {self.base_tuning_setup.ML_CLASS}"
        )

        self.clf = RandomForestClassifier(
            n_jobs=self.base_tuning_setup.N_JOBS,
            random_state=self.base_tuning_setup.RANDOM_STATE,
            # other params set in self.params
        )
        self.base_tuning_setup.logger.info(f"clf declared: {self.clf}")

    def if_randomized_searching(self):
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        search = RandomizedSearchCV(
            self.clf,  # estimator
            n_iter=self.base_tuning_setup.N_ITER,  # controls 'combination of parameters'
            param_distributions=self.params,  # dictionary of parameter keys and lists or distributions of parameter options to try
            scoring="f1_macro",  # "accuracy",
            cv=self.rskf.split(
                self.base_tuning_setup.X_train, self.base_tuning_setup.y_train
            ),  # None: default 5-fold #
            n_jobs=self.base_tuning_setup.N_JOBS,  # this may be unnecessary here as it's initialised for this class
            verbose=4,
            error_score=np.nan,  # np.nan=default; Value to assign to the score if an error occurs in estimator fitting
            random_state=self.base_tuning_setup.RANDOM_STATE,  # default=None # setting this to self.RANDOM_STATE defeats the point of using randomness, but may be more reproducable, surely?
            return_train_score=True,  # default=False.
        )
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using search settings: {search}."
        )
        return search

    def if_grid_searching(self):
        self.params["max_samples"] = [
            0.1,
            0.25,
            0.5,
            0.75,
        ]  # change the type of max_samples to test;  # removed 1.0, # can't use ALL the samples to train with. That's nonsense.
        # params["max_samples"] = np.arange(0,1.1, 0.1) # shift the uniform distribution random malarky used in the randomized, and go to a larger ordered set of values for the 'grid'
        self.params["min_samples_split"] = [2]
        self.params["ccp_alpha"] = np.arange(0, 0.25, 0.05)
        self.params["min_impurity_decrease"] = np.arange(0, 0.15, 0.05)
        # params["max_leaf_nodes"] = list(range(7, 260, 10))
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        search = GridSearchCV(
            self.clf,  # estimator
            param_grid=self.params,  # dictionary of parameter keys and lists or distributions of parameter options to try
            scoring="f1_macro",  # "accuracy", # strategy evaluating performance of cross-validated model on test set. Default "None" uses the default evaluation criterion of the estimator.
            cv=self.rskf.split(
                self.base_tuning_setup.X_train, self.base_tuning_setup.y_train
            ),  # None: default 5-fold  # cross-validation splitting strategy
            n_jobs=(
                self.N_CORES
            ),  # number of jobs to run in parallel; default=None (means 1)
            refit=True,  # default: True # refit an estimator using the best found parameters
            verbose=2,
            pre_dispatch="1.5*n_jobs",  # Controls the number of jobs that get dispatched during parallel execution; int, or str, default=’2*n_jobs’
            error_score="raise",
            return_train_score=False,  # default: False; returning these in cv_results_ will be computationally expensive, but could help give info on over/underfitting; not strictly required.
        )
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using search settings: {search}."
        )
        return search

    def if_halving_grid_searching(self):
        self.params["max_samples"] = [
            0.1,
            0.25,
            0.5,
            0.75,
        ]  # change the type of max_samples to test;  # removed 1.0, # can't use ALL the samples to train with. That's nonsense.
        # params["max_samples"] = np.arange(0,1.1, 0.1) # shift the uniform distribution random malarky used in the randomized, and go to a larger ordered set of values for the 'grid'
        self.params["min_samples_split"] = [2]
        self.params["ccp_alpha"] = np.arange(0, 0.02, 0.005)
        self.params["min_impurity_decrease"] = np.arange(0, 0.15, 0.05)
        # params["max_leaf_nodes"] = list(range(7, 260, 10))
        self.base_tuning_setup.logger.info(f"param options are: {self.params}")
        search = HalvingGridSearchCV(
            self.clf,  # estimator
            param_grid=self.params,  # dictionary of parameter keys and lists or distributions of parameter options to try
            factor=3,  # 3=default; the 'halving' param: which proportion of candidates selected for the next iteration (e.g. 3 is 1/3rd)
            resource="n_samples",  # default: 'n_samples'. the resource that increases with each iteration.  Can be 'n_iterations' or 'n_estimators' for gradient boosting estimators. 'max_resources' cannot be auto if that's true
            max_resources="auto",  # default: 'n_samples'; maximum amount of resource candidates can use for given iteration; By default, this is set to n_samples when resource='n_samples' (default), else an error is raised.
            min_resources="exhaust",  # default="exhaust"; The minimum amount of resource that any candidate is allowed to use for a given iteration."‘exhaust’ leads to a more accurate estimator, but is slightly more time consuming."
            aggressive_elimination=False,  # only relevant in cases where insufficient resources to reduce remaining candidates to at most 'factor' after last iteration. If True, search process will ‘replay’ first iteration for as long as needed until the number of candidates is small enough. False by default: last iteration may evaluate more than 'factor' candidates
            cv=None,  # default 5-fold.
            # following alternative removed as it seemed to break the run when attempted with HalvingGridSearchCV?
            # cv=rskf.split(
            #     self.X_train, self.y_train
            # ),  # None: default 5-fold  # cross-validation splitting strategy
            scoring="f1_macro",  # "accuracy", # strategy evaluating performance of cross-validated model on test set. Default "None" uses the default evaluation criterion of the estimator.
            refit=True,  # default: True # refit an estimator using the best found parameters
            n_jobs=(
                self.N_CORES
            ),  # number of jobs to run in parallel; default=None (means 1)
            error_score="raise",
            return_train_score=True,  # default: False; returning these in cv_results_ will be computationally expensive, but could help give info on over/underfitting; not strictly required.
            random_state=self.base_tuning_setup.RANDOM_STATE,  # state used for subsampling dataset when resources != 'n_samples'.
            verbose=2,
            # pre_dispatch="1.5*n_jobs",  # Controls the number of jobs that get dispatched during parallel execution; int, or str, default=’2*n_jobs’
        )
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using search settings: {search}."
        )
        return search

    def param_searching(self):
        self.base_tuning_setup.logger.info(
            f"Searching hyper-parameters using {self.base_tuning_setup.SEARCH_METHOD}."
        )

        search = self.decide_which_hyper_param_method()

        self.base_tuning_setup.logger.info("search declared")
        start_hyper_param_search = time.time()
        self.base_tuning_setup.logger.info("param timer started")

        # To ignore the warning about the OOB
        with warnings.catch_warnings():
            warnings.simplefilter("once")
            try:
                search.fit(
                    self.base_tuning_setup.X_train, self.base_tuning_setup.y_train
                )
            except ValueError as e:
                self.base_tuning_setup.logger.error(f"Error in search.fit(): {e}")

            self.base_tuning_setup.report(
                search.cv_results_, n_top=5
            )  # Report the top 5 results

            self.base_tuning_setup.logger.info(
                f"Completed search.fit() and have best results: {search}"
            )
            param_search_results = pd.DataFrame(
                search.cv_results_
            )  # could use comparison approaches like https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html#sphx-glr-auto-examples-model-selection-plot-grid-search-stats-py on these

            best_params = HyperParamsRF(
                n_estimators=search.best_params_["n_estimators"],
                criterion=search.best_params_["criterion"],
                max_depth=search.best_params_["max_depth"],
                min_samples_split=search.best_params_["min_samples_split"],
                min_samples_leaf=search.best_params_["min_samples_leaf"],
                min_weight_fraction_leaf=search.best_params_[
                    "min_weight_fraction_leaf"
                ],
                max_features=search.best_params_["max_features"],
                max_leaf_nodes=search.best_params_["max_leaf_nodes"],
                min_impurity_decrease=search.best_params_["min_impurity_decrease"],
                bootstrap=search.best_params_["bootstrap"],
                oob_score=search.best_params_["oob_score"],
                # n_jobs=search.best_params_["n_jobs"], # removed because this is NOT set in the initial params used in search
                random_state=search.best_params_["random_state"],
                verbose=search.best_params_["verbose"],
                class_weight=search.best_params_["class_weight"],
                ccp_alpha=search.best_params_["ccp_alpha"],
                max_samples=search.best_params_["max_samples"],
                # monotonic_cst=search.best_params_["monotonic_cst"],
            )
            self.base_tuning_setup.logger.info(
                "Best score {:.5f} with:".format(
                    search.best_score_
                )  # params settings that gave best results on holdout data
            )
            self.base_tuning_setup.logger.info(
                best_params
            )  # parameter settings that gave the best results on the hold out data.
        end_hyper_param_search = time.time()
        hyper_param_search_time = end_hyper_param_search - start_hyper_param_search
        self.base_tuning_setup.logger.info(
            f"Hyper-Parameter search using {self.base_tuning_setup.SEARCH_METHOD} method for {self.base_tuning_setup.ML_CLASS} took {hyper_param_search_time} seconds for {self.base_tuning_setup.N_ITER} across {len(self.params)} parameter categories, across {search.n_splits_} cross-validation splits (folds/iterations) and refitting the best model took {search.refit_time_} seconds."
        )

        params_filename_out = f"{self.base_tuning_setup.ML_CLASS}_paramsearch_{self.base_tuning_setup.SEARCH_METHOD}_N{self.base_tuning_setup.y_test_size[0]}_{self.base_tuning_setup.current_date_info}.csv"
        params_save_out = Path(
            self.base_tuning_setup.data_location, params_filename_out
        )
        param_search_results.to_csv(params_save_out, header=True, index=False)
        self.base_tuning_setup.logger.info(
            f"Index of the best candidate parameter settings is: {search.best_index_}, in {params_save_out}"
        )
        return best_params

    def searched_params_fit_to_classifier(self):
        best_params = self.param_searching()

        start_selected_rfc_fit = time.time()
        self.base_tuning_setup.logger.info("fit timer started")
        # run full model with the best params! :D
        selected_rfc = RandomForestClassifier(
            # pull params from the hyperparams class for RF, with SOME specifics: verbose, random state, n_jobs
            n_estimators=best_params.n_estimators,
            criterion=best_params.criterion,
            max_depth=best_params.max_depth,
            min_samples_split=best_params.min_samples_split,
            min_samples_leaf=best_params.min_samples_leaf,
            min_weight_fraction_leaf=best_params.min_weight_fraction_leaf,
            max_features=best_params.max_features,  # type: ignore
            max_leaf_nodes=best_params.max_leaf_nodes,
            min_impurity_decrease=best_params.min_impurity_decrease,
            bootstrap=best_params.bootstrap,
            oob_score=best_params.oob_score,
            n_jobs=self.base_tuning_setup.N_JOBS,
            random_state=self.base_tuning_setup.RANDOM_STATE,
            verbose=4,  # increased for 'best model fit' from candidate fits during search
            class_weight=best_params.class_weight,
            ccp_alpha=best_params.ccp_alpha,
            max_samples=best_params.max_samples,
            # monotonic_cst=best_params.monotonic_cst,
        ).fit(self.base_tuning_setup.X_train, self.base_tuning_setup.y_train)
        end_selected_rfc_fit = time.time()
        selected_rfc_fit_time = end_selected_rfc_fit - start_selected_rfc_fit
        self.base_tuning_setup.logger.info(
            f"Selected Parameters RF model took {selected_rfc_fit_time} seconds to fit"
        )

        start_selected_rfc_predict = time.time()
        y_pred = selected_rfc.predict(self.base_tuning_setup.X_test)
        end_selected_rfc_predict = time.time()
        selected_rfc_predict_time = (
            end_selected_rfc_predict - start_selected_rfc_predict
        )
        self.y_true = self.base_tuning_setup.y_test
        self.base_tuning_setup.logger.info(
            f"Selected Parameters RF model took {selected_rfc_predict_time} seconds to predict"
        )

        true_df = pd.DataFrame(
            {
                "Test true": self.base_tuning_setup.y_test,
                "Test predicted": y_pred,
            }
        )

        filename_out = f"test_prediction_data_N{self.base_tuning_setup.y_test_size[0]}_{self.base_tuning_setup.current_date_info}.csv"
        save_out = Path(self.base_tuning_setup.data_location, filename_out)
        true_df.to_csv(save_out, header=True, index=False)

        feature_importances = selected_rfc.feature_importances_

        self.base_tuning_setup.logger.info(
            f"""
            For Random Forest model trained on: \n
            datafile: sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv \n
            with N observations (repo-individuals): {self.base_tuning_setup.N_OBS} \n
            hyper-parameter-searched on {self.base_tuning_setup.N_ITER} iterations \n
            training-set size: N={self.base_tuning_setup.X_train_size[0]} \n
            and evaluated using test-set size: N={self.base_tuning_setup.X_test_size[0]} repo-individuals \n
            using N={self.base_tuning_setup.X_test_size[1]} features \n 
            with N={best_params.n_estimators} trees in forest  \n
            at {self.base_tuning_setup.current_date_info} \n 
            with parameters: {selected_rfc.get_params(deep=False)} \n
            and feature importances: 
        """
        )
        for idx in range(len(CLUSTERING_VARIABLES)):
            self.base_tuning_setup.logger.info(
                "{}: {:.5f}[%]".format(
                    CLUSTERING_VARIABLES[idx], 100.0 * feature_importances[idx]
                )
            )

        # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score
        self.base_tuning_setup.logger.info(
            "Accuracy: {:.5f} (percent of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred),
            )
        )
        self.base_tuning_setup.logger.info(
            "Non-Normalised Accuracy: {:.0f} (number of correctly classified samples)".format(
                metrics.accuracy_score(self.y_true, y_pred, normalize=False),
            )
        )
        self.base_tuning_setup.logger.info(
            "Balanced Accuracy: {:.5f} (the average of recall obtained on each class)".format(
                metrics.balanced_accuracy_score(
                    self.y_true,
                    y_pred,
                    adjusted=False,
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Out of Bag Error: {:.5f} (smaller better)".format(
                # 1-oob_score_ via https://scikit-learn.org/stable/auto_examples/ensemble/plot_ensemble_oob.html#id2
                1 - selected_rfc.oob_score_
            )
        )
        self.base_tuning_setup.logger.info(
            "F1 Score: {:.5f} (harmonic mean of the precision and recall, both equally weighted)".format(
                metrics.f1_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Precision: {:.5f} (Ratio of correctly predicted positive classes to total of positive predictions)".format(
                metrics.precision_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Recall: {:.5f} (Ratio of correctly predicted positive classes to all actual 'real' positive classes)".format(
                metrics.recall_score(
                    self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
                    self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
                    average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                ),
            )
        )
        # # multiclass means you can only be in one category only e.g. media format (film or tv-show)
        # # multilabel means you can have multiple labels applying to the same observation e.g. genre of media (horror, shark movie, animals)
        self.base_tuning_setup.logger.info(
            "Area Under the Receiver Operating Characteristic Curve (ROC AUC), (NB: calculated average='macro' and multiclass='ovr'): {:.5f}".format(
                roc_auc_score(
                    y_true=self.base_tuning_setup.y_test,  # y_true
                    y_score=selected_rfc.predict_proba(
                        self.base_tuning_setup.X_test
                    ),  # y_score
                    # y_true=y_test,
                    # y_score=pipeline_class_obj.pipe.named_steps["clf"].predict_proba(X_test),
                    average="macro",
                    multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                    # multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
                )
            )
        )
        self.base_tuning_setup.logger.info(
            "Area Under the Receiver Operating Characteristic Curve (ROC AUC), (NB: calculated average='macro' and multiclass='ovo'): {:.5f}".format(
                roc_auc_score(
                    y_true=self.base_tuning_setup.y_test,  # y_true
                    y_score=selected_rfc.predict_proba(
                        self.base_tuning_setup.X_test
                    ),  # y_score
                    average="macro",
                    # multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                    multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
                )
            )
        )

        classification_rep = metrics.classification_report(
            y_true=self.base_tuning_setup.le.inverse_transform(self.y_true),  # y_true
            y_pred=self.base_tuning_setup.le.inverse_transform(y_pred),  # y_pred
            zero_division=0,  # in later versions of sklearn options inc 0.0 or np.nan, here it's int.
            digits=5,
            # output_dict=True,  # default=False
        )
        self.base_tuning_setup.logger.info("\n")
        self.base_tuning_setup.logger.info(
            classification_rep
        )  # try this to avoid logger error with formatting of report
        self.base_tuning_setup.logger.info("Returning final results now:")
        return (
            selected_rfc,  # this is the actual model, but currently not using this output
            f1_score(
                y_true=self.base_tuning_setup.y_test, y_pred=y_pred, average="macro"
            ),
            precision_score(
                y_true=self.base_tuning_setup.y_test, y_pred=y_pred, average="macro"
            ),
            selected_rfc.score(
                self.base_tuning_setup.X_test, self.base_tuning_setup.y_test
            ),
            best_params,
            # feature_imp,
        )

    # next function would apply selected_rfc to a dataset to predict RSE Personas with it.


parser = argparse.ArgumentParser()
parser.add_argument(
    "-n",
    "--n-observations",
    metavar="SAMPLES",
    help="number of samples to run on (e.g. 10000)",
    type=int,
    default=10000,
)
parser.add_argument(
    "-i",
    "--n-iterations",
    metavar="ITERATIONS",
    help="number of iterations for RandomizedSearchCV (e.g. 1000)",
    type=int,
    default=100,
)
parser.add_argument(
    "-c",
    "--classifier-type",
    metavar="CLASSIFIER",
    help="type of classfier to test with (e.g. RF, default; HGBT; GBT)",
    type=str,
    default="RF",
)

parser.add_argument(
    "-r",
    "--random-state",
    metavar="RANDOM",
    help="random seed to set (e.g. 42)",
    type=int,
    default=42,
)
parser.add_argument(
    "-s",
    "--search-method",
    metavar="SEARCH",
    help="which search method to use: GridSearchCV or RandomizedSearchCV or HalvingGridSearchCV (default)",
    type=str,
    default="RandomizedSearchCV",
)
parser.add_argument(
    "-j",
    "--job-number",
    metavar="JOBS",
    help="number of jobs (~cores) to run this script with (ie 7 for EIDF VM, 8 for cirrus)",
    type=int,
    default=7,
)


def main():
    """
    $ time python githubanalysis/analysis/ML_tuning.py -c RF -n 10000 -i 50 -r 69 -j 7
    """
    args = parser.parse_args()
    class_arg: str = args.classifier_type
    nobs_arg: int = args.n_observations
    niter_arg: int = args.n_iterations
    rand_arg: int = args.random_state
    search_arg: str = args.search_method
    jobs_arg: int = args.job_number

    tuning_setup = BaseTuningSetup(
        dataset_name="ML_tune",
        in_notebook=False,
        exists_ok=True,
        logger=None,
        ML_CLASS=class_arg,
        N_OBS=nobs_arg,
        N_ITER=niter_arg,
        RANDOM_STATE=rand_arg,
        SEARCH_METHOD=search_arg,
        N_JOBS=jobs_arg,
    )

    tuning_setup.logger.info(
        ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> new paramsearch running <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    )

    tuning_setup.logger.info("prepping dataset")
    tuning_setup.prep_data()

    tuning_setup.logger.info("splitting dataset")
    tuning_setup.setup_test_train()

    tuning_setup.logger.info(
        f"searching for params using search method {search_arg} on ML classifier {class_arg}"
    )

    if tuning_setup.ML_CLASS == "RF":
        rfparamsearch = RFParamSearch(base_tuning_setup=tuning_setup)
        # this does the searching, and fits final set of params to classifier model:
        rfparamsearch.searched_params_fit_to_classifier()

    elif tuning_setup.ML_CLASS == "HGBT":
        # thing B
        hgbtparamsearch = HGBTParamSearch(base_tuning_setup=tuning_setup)
        hgbtparamsearch.searched_params_fit_to_classifier()

    elif tuning_setup.ML_CLASS == "GBT":
        # thing C
        gbtparamsearch = GBTParamSearch(base_tuning_setup=tuning_setup)
        gbtparamsearch.searched_params_fit_to_classifier()

    else:
        print("WHELP D:")
        # this oughtn't happen, because there's an assert somewhere
        # preventing ML_CLASS being NOT those three things, but nevertheless...

    tuning_setup.logger.info(
        ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> paramsearch complete <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    )

    tuning_setup.logger.info("\n")
    print("\n paramater search complete.\n")


if __name__ == "__main__":
    main()
