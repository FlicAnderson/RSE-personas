from logging import Logger
import pandas as pd
from pathlib import Path
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import graphviz

from sklearn.pipeline import (
    Pipeline,
)  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# from sklearn.model_selection import cross_validate
from sklearn.model_selection import LearningCurveDisplay, learning_curve
from sklearn.metrics import roc_auc_score
from sklearn.tree import plot_tree, export_graphviz
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
    GradientBoostingClassifier,
)
from sklearn import metrics
from sklearn.metrics import ConfusionMatrixDisplay

from githubanalysis.setup_classes import DatasetSetup

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


def update_candidate_features(
    n_features,
):
    """
    calculate F: number of predictors used to select the best split
    F = log2(M+1) # M is number total predictors; # F
    Leo Breiman. 2001. Random Forests. Machine Learning 45, 1 (Oct. 2001), 5–32.
    doi:10.1023/A:1010933404324
    """
    assert isinstance(n_features, int), "require integer n_features to calculate F"
    candidate_feats_Nplusone = round(
        math.log2(
            n_features + 1  # F = log2(M+1) # M is number total predictors;
        )
    )
    assert isinstance(candidate_feats_Nplusone, int), (
        "somehow candidate_feats_Nplusone is not an integer; fix this as floats would lead to a fraction being used in Random Forest candidate feature splitting..."
    )
    return candidate_feats_Nplusone


class ML_Pipeline_Decision_Tree(
    DatasetSetup
):  # wrapper around my ML pipeline, also holds additional helpful info.
    def _log_name(self) -> str:
        return "baby_ML_pipeline"

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
    ) -> None:
        self.model_type = "decision_tree"
        self.le = LabelEncoder()
        # create a pipeline object
        self.pipe = Pipeline(
            steps=[  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
                (
                    "clf",
                    DecisionTreeClassifier(
                        criterion="gini",  # options: 'gini', 'entropy', 'log_loss' # measures split quality; gini for node purity, log_loss/entropy for Shannon info gain
                        splitter="best",  # 'best' for best split, or 'random' for best random split
                        max_depth=None,  # integer or None
                        random_state=RANDOM_STATE,  # controls the randomness of the estimator during splitting
                        # min_samples_split=2,
                        # min_samples_leaf=1,
                        max_features=None,  #'int', 'float', 'sqrt', 'log2', 'None'
                        # bunch more args... #
                        # max_leaf_nodes=None, #set max leaf nodes based on 'best' relative reduction in impurity; None: unlimited leaf nodes
                        # ccp_alpha=0.0, # complexity parameter used for Minimal Cost-Complexity Pruning.
                    ),
                ),
            ],
            memory=None,
            # transform_input=None, # I maybe don't have the updated package version for this (1.6?)
            verbose=True,
        )
        super().__init__(dataset_name, in_notebook, exists_ok, logger)

    def get_data(self, data_file, small_vers=True, small_N_appx: int | None = 50):
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

        if small_vers is True and small_N_appx is not None:
            n_per_persona = round(small_N_appx / 7)
            classified_df = classified_df.groupby(by="RSE_persona").sample(
                n=n_per_persona, weights="MRC"
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

    def test_train_data(
        self,
        train_pc=0.75,
        test_pc=0.25,
        shuffle_state=True,
        stratify_state=True,
    ):
        X, y = self.RSE_info["data"], self.RSE_info["target"]

        assert (1 - train_pc) == test_pc, (
            f"Values for train_pc and test_pc must total 1; test_pc is currently set to {test_pc}"
        )
        # returning the function which creates a tuple of 4x:
        #  X_train, X_test, y_train, y_test
        if stratify_state:
            return train_test_split(
                X,
                y,
                test_size=test_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 25%
                train_size=train_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 75%
                random_state=RANDOM_STATE,
                shuffle=shuffle_state,  # True by (sklearn) default
                stratify=self.RSE_info[
                    "target"
                ],  # same as y; None by (sklearn) default
            )
        else:
            return train_test_split(
                X,
                y,
                test_size=test_pc,  # by default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 25%
                train_size=train_pc,  # by default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 75%
                random_state=RANDOM_STATE,
                shuffle=shuffle_state,
            )

    def do_model_fit(self, train_pc, test_pc, shuffle_state, stratify_state):
        X_train, X_test, y_train, y_test = self.test_train_data(
            train_pc=train_pc,
            test_pc=test_pc,
            shuffle_state=shuffle_state,
            stratify_state=stratify_state,
        )
        # add size info from test and training datasets to self for future reporting.
        self.X_train_size = X_train.shape
        self.y_train_size = y_train.shape
        self.X_test_size = X_test.shape
        self.y_test_size = y_test.shape

        self.pipe.fit(X_train, y_train)
        return X_test, y_test

    def plot_decision_tree(self, depth):
        saveout_args = dict(
            dpi=400,
            format="pdf",
            bbox_inches="tight",
        )

        # plot the decision tree
        plot_tree(
            self.pipe.named_steps[
                "clf"
            ],  # use fitted pipe obj created by 'decision_tree step'
            max_depth=depth,
            filled=True,
            feature_names=self.RSE_info["feature_names"],
            class_names=list(self.RSE_info["target_names"]),
        )
        # export to graphviz format
        # graphviz_out_file = Path(
        #     self.image_write_location, "decision_tree_graphviz.pdf"
        # )
        dot_data = export_graphviz(
            self.pipe.named_steps[
                "clf"
            ],  # use fitted pipe obj created by 'decision_tree step'
            out_file=None,  # "graphviz_out_file",
            feature_names=self.RSE_info["feature_names"],
            class_names=list(self.RSE_info["target_names"]),
            filled=True,
            rounded=True,
            special_characters=True,
        )
        graph = graphviz.Source(dot_data)  # , format="pdf")
        graph.render(
            directory=self.image_write_location,
            filename="RSE_personas_decision_tree_graphviz",
            format="pdf",
        )

        plt.title("Decision tree trained on all RSE Persona clustering features")
        saveout_name = Path(
            self.image_write_location,
            f"decision_tree_N{self.X_train_size[0]}_{self.current_date_info}.pdf",
        )
        plt.savefig(saveout_name, **saveout_args)

        print(
            f"attempted to save out to : {Path(self.image_write_location, 'decision_tree_initial.pdf')}"
        )
        plt.show()

    def run_predictor(
        self,
        X_test,
        y_test,
    ):
        self.y_pred = self.pipe.predict(X_test)
        self.y_true = y_test

        # savefig kwargs
        saveout_args = dict(
            dpi=400,
            format="pdf",
            bbox_inches="tight",
        )

        # Plot non-normalized confusion matrix
        titles_options = [
            (
                f"confusion matrix, no normalization (N={self.X_test_size[0]})",
                None,
            ),
            (
                f"normalized confusion matrix (N={self.X_test_size[0]})",
                "true",
            ),  # normalise on True value pcs
        ]

        persona_order = [
            "Ephemeral Contributor",
            "Occasional Contributor",
            "Project Organiser",
            "Moderate Contributor",
            "Low-Process Closer",
            "Low-Coding Closer",
            "Active Contributor",
        ]

        for title, normalize in titles_options:
            disp = ConfusionMatrixDisplay.from_predictions(
                self.le.inverse_transform(self.y_true),  # y_true
                self.le.inverse_transform(self.y_pred),  # y_pred
                labels=persona_order,  # personas listed in increasing MRC order
                sample_weight=None,
                normalize=normalize,  # 'all': total N samples; 'pred': over predictions; 'true': over true; None: default
                display_labels=None,
                include_values=True,
                xticks_rotation="vertical",
                values_format=None,
                cmap=cmx.Blues,
                ax=None,
                colorbar=False,
                im_kw=None,
                text_kw=None,
            )
            disp.ax_.set_title(title)
            saveout_name = Path(
                self.image_write_location,
                f"{self.model_type}_confusion_matrix_normalise{normalize}_N{self.X_test_size[0]}_{self.current_date_info}.pdf",
            )
            plt.savefig(
                saveout_name,
                **saveout_args,
            )
            plt.show()


class ML_Pipeline_Random_Forest(ML_Pipeline_Decision_Tree):
    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
        forest_size: int = 100,
        candidate_feats: int | None = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.model_type = "random_forest"
        self.le = LabelEncoder()
        # create a pipeline object
        self.forest_size = int(forest_size)
        if candidate_feats is not None:
            self.max_feats = update_candidate_features(n_features=candidate_feats)
        else:
            self.max_feats = "sqrt"
        self.pipe = Pipeline(
            steps=[  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=forest_size,  # number of trees in forest
                        criterion="gini",  # options: 'gini', 'entropy', 'log_loss' # measures split quality; gini for node purity, log_loss/entropy for Shannon info gain
                        max_depth=None,  # integer or None # maximum dept of tree; if None, nodes expanded until all nodes pure or all leaves have less than min_samples_split samples.
                        # max_leaf_nodes=None, #set max leaf nodes based on 'best' relative reduction in impurity; None: unlimited leaf nodes
                        min_samples_split=2,  # min number samples for splitting if int; if float it's a fraction
                        min_samples_leaf=1,  # nodes must have this many samples (may smooth regression models); int/float as min_samples_split.
                        max_features=self.max_feats,  #'int', 'float', 'sqrt':sqrt(n_features), 'log2':log2(n_features), 'None':(max_features=n_features)
                        bootstrap=True,
                        max_samples=None,  # controls sub-sampling for bootstrapping
                        oob_score=True,  # Whether to use out-of-bag samples to estimate the generalization score. By default, accuracy_score is used.# can use custom metric.
                        n_jobs=None,  # how many to run in paralell... None~=use 1.
                        verbose=1,  # verbosity
                        warm_start=False,
                        class_weight=None,  # if not given, all classes have weight 1.
                        # bunch more args... #
                        ccp_alpha=0.0,  # complexity parameter used for Minimal Cost-Complexity Pruning
                        random_state=RANDOM_STATE,  # controls the randomness of the estimator during splitting
                    ),
                ),
            ],
            memory=None,
            # transform_input=None, # I maybe don't have the updated package version for this (1.6?)
            verbose=True,
        )


class ML_Pipeline_HistGradientBoosting(ML_Pipeline_Decision_Tree):
    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
        forest_size: int = 100,
        candidate_feats: int | None = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.model_type = "hist_gradient_boosting"
        self.le = LabelEncoder()
        # create a pipeline object
        self.forest_size = int(forest_size)
        if candidate_feats is not None:
            self.max_feats = update_candidate_features(n_features=candidate_feats)
        else:
            self.max_feats = "sqrt"
        self.pipe = Pipeline(
            steps=[  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
                (
                    "clf",
                    HistGradientBoostingClassifier(
                        loss="log_loss",  # default
                        learning_rate=0.01,  # can also use 0.01; # shrinkage param (lambda)
                        max_iter=forest_size,  # number of iterations/trees to generate
                        max_leaf_nodes=None,  # None= no max; default=31 for some reason?
                        max_depth=None,
                        l2_regularization=0,  # L2 regularization parameter penalizing leaves with small hessians. Use 0 for no regularization (default)
                        # max_features = 1.0, # added in v1.4 # float in latest docs, interaction_cst can be used
                        max_bins=255,  # N bins for non-missing values; more = better? max=255.
                        categorical_features=None,  # None:no feats categorical; boolean array; integer array of indices of cat feats; str array: cat names of training data if it has them; "from_dtype": use columns with dtype 'category' (default)
                        monotonic_cst=None,  # BINARY ONLY; constant to inforce on each feature; 1:monotonic incr; 0: no constraint; -1:monotonic decrease
                        interaction_cst=None,  # specify sets of feats which can interact in child node splits # "pairwise" "no_interactions", None, or seq of lists/tuples/sets of ints for indices
                        warm_start=False,  # if True reuse previous solution to fit/add esimators (True req retrain on same data only for validity!)
                        early_stopping=False,  # if sample > 10k this is enabled w/ 'auto'
                        scoring="loss",  # scoring to use w/ early stopping: 'str':*; a scorer callable; None:'accuracy' is used; 'loss'(default): checked with loss value; *=https://scikit-learn.org/stable/modules/model_evaluation.html#scoring-string-names;
                        validation_fraction=0.1,  # proportion(float)/size(int) of training data to set aside for validation of early stopping; None=uses training data.
                        n_iter_no_change=10,  # determines early stopping (if it's used)
                        tol=1e-7,  # 'absolute tolerance' to use comparing scores. higher = more likely to early stop aaro harder to consider subsq iterations improvements on prev
                        verbose=1,  # verbosity: 1:summary info only; 2=per-iteration info;
                        class_weight=None,  # dict / 'balanced' / None (where all classess weight=1) # TODO: consider this more...
                        random_state=RANDOM_STATE,  # controls the randomness of the estimator during splitting
                    ),
                ),
            ],
            memory=None,
            # transform_input=None, # I maybe don't have the updated package version for this (1.6?)
            verbose=True,
        )


class ML_Pipeline_GradientBoosting(ML_Pipeline_Decision_Tree):
    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
        forest_size: int = 100,
        candidate_feats: int | None = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.model_type = "gradient_boosting"
        self.le = LabelEncoder()
        # create a pipeline object
        self.forest_size = int(forest_size)
        if candidate_feats is not None:
            self.max_feats = update_candidate_features(n_features=candidate_feats)
        else:
            self.max_feats = "sqrt"
        self.pipe = Pipeline(
            steps=[  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
                (
                    "clf",
                    GradientBoostingClassifier(
                        loss="log_loss",  # default
                        learning_rate=0.01,  # can also use 0.01; # shrinkage param (lambda)
                        n_estimators=forest_size,  # number of boosting stages to perform
                        subsample=1.0,  # <1=Stochastic gradient boosting; bootstrapping if <1; <1 => >variance but <bias
                        criterion="friedman_mse",  # split quality measurement; ‘friedman_mse’ ~=best cf 'squared_error'
                        min_samples_split=2,  # min number samples for splitting if int; if float it's a fraction
                        min_samples_leaf=1,  # nodes must have this many samples (may smooth regression models); int/float as min_samples_split.
                        min_weight_fraction_leaf=0.0,  # min weighted fraction of sum of total weights (input samples) req for a leaf node; equal when sample_weight not provided.
                        max_depth=None,  # default=3 # TODO: tune for best performance. If none, expanded until leaves are pure
                        min_impurity_decrease=0.0,  # default. Node split if induces decrease of impurity >= this.
                        init=None,  # 'zero'(raw predictions set to 0) or None (default, preducts classes' priors) or estimator object
                        max_features="sqrt",  # added in v1.4 # float in latest docs, interaction_cst can be used; max_features < n_features reduces variance and increases bias.
                        max_leaf_nodes=None,  # Grow trees with max_leaf_nodes in best-first fashion; best==relative reduction in impurity; None=unlimited
                        warm_start=False,  # TODO: check this in tuning; if True reuse previous solution to fit/add esimators (True req retrain on same data only for validity!)
                        validation_fraction=0.1,  # proportion(float)/size(int) of training data to set aside for validation of early stopping; None=uses training data.
                        n_iter_no_change=None,  # 10 for hgbt, # determines early stopping (if it's used)
                        tol=1e-4,  # 1e-7 default for HistGradBoost, # 'absolute tolerance' to use comparing scores. higher = more likely to early stop aaro harder to consider subsq iterations improvements on prev
                        verbose=0,  # verbosity: 1:summary info only; 2=per-iteration info;
                        ccp_alpha=0.0,  # TODO FOR PRUNING # complexity parameter used for Minimal Cost-Complexity Pruning
                        random_state=RANDOM_STATE,  # controls the randomness of the estimator during splitting
                    ),
                ),
            ],
            memory=None,
            # transform_input=None, # I maybe don't have the updated package version for this (1.6?)
            verbose=True,
        )


class ML_Utils(DatasetSetup):
    def _log_name(self) -> str:
        return "baby_ML_pipeline_utils"

    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        exists_ok: bool = False,
        logger: None | Logger = None,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)

    def plot_learning_curves(
        self,
        model,
        X,
        y,
        # train_size,
    ):
        train_sizes, train_scores, test_scores = learning_curve(model, X, y)
        display = LearningCurveDisplay(
            train_sizes=train_sizes,
            train_scores=train_scores,
            test_scores=test_scores,
            score_name=None,
        )
        display.plot()
        LearningCurveDisplay.from_estimator(
            estimator=model,
            X=X,
            y=y,
            groups=None,
            train_sizes=train_sizes,
            cv=None,
            scoring=None,
            exploit_incremental_learning=False,
            n_jobs=1,
            pre_dispatch="all",
            verbose=0,
            random_state=RANDOM_STATE,
            error_score="raise",
            fit_params=None,  # dict of params to pass to the fit method of the estimator
            ax=display.ax_,  # axes to plot on; if None, new figure and axes created
            negate_score=False,  # negate the scores or not from learning_curve?
            score_name=None,
            score_type="both",  # 'test', 'train', or 'both
            std_display_style="fill_between",  # how to display the std around the mean
            line_kw=None,
            fill_between_kw=None,
            errorbar_kw=None,
        )
        plt.show()
        saveout_name = Path(
            self.image_write_location,
            f"{model}_LearningCurve_{self.current_date_info}.pdf",
        )
        plt.savefig(
            saveout_name,
            # **saveout_args,
        )


def run_scoring_printouts(
    pipeline_class_obj: ML_Pipeline_Decision_Tree
    | ML_Pipeline_Random_Forest
    | ML_Pipeline_HistGradientBoosting
    | ML_Pipeline_GradientBoosting,
    X_test,
    y_test,
    datafile: Path,
):
    assert (
        pipeline_class_obj.model_type == "decision_tree"
        or pipeline_class_obj.model_type == "random_forest"
        or pipeline_class_obj.model_type == "hist_gradient_boosting"
        or pipeline_class_obj.model_type == "gradient_boosting"
    ), (
        "model_type not recognised: must be one of 'decision_tree' or 'random_forest' or 'hist_gradient_boosting' or 'gradient_boosting'."
    )

    # Model Accuracy, how often is the classifier correct?
    if pipeline_class_obj.model_type != "random_forest":
        print(
            f"""
            For {pipeline_class_obj.model_type} model trained on: \n
            datafile: {datafile} \n
            training-set size: N={pipeline_class_obj.X_train_size[0]} \n
            and evaluated using test-set size: N={pipeline_class_obj.X_test_size[0]} repo-individuals \n
            using N={pipeline_class_obj.X_test_size[1]} features \n 
            at {pipeline_class_obj.current_date_info}
            """
        )
    else:
        print(
            f"""
            For {pipeline_class_obj.model_type} model trained on: \n
            datafile: {datafile} \n
            training-set size: N={pipeline_class_obj.X_train_size[0]} \n
            and evaluated using test-set size: N={pipeline_class_obj.X_test_size[0]} repo-individuals \n
            using N={pipeline_class_obj.X_test_size[1]} features \n 
            with N={pipeline_class_obj.forest_size} trees in forest  \n
            at {pipeline_class_obj.current_date_info}
        """
        )

    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score
    print(
        "Accuracy: {:.3f} (percent of correctly classified samples)".format(
            metrics.accuracy_score(
                pipeline_class_obj.y_true, pipeline_class_obj.y_pred
            ),
        )
    )
    print(
        "Non-Normalised Accuracy: {:.0f} (number of correctly classified samples)".format(
            metrics.accuracy_score(
                pipeline_class_obj.y_true, pipeline_class_obj.y_pred, normalize=False
            ),
        )
    )
    print(
        "Balanced Accuracy: {:.3f} (the average of recall obtained on each class)".format(
            metrics.balanced_accuracy_score(
                pipeline_class_obj.y_true,
                pipeline_class_obj.y_pred,
                adjusted=False,
            )
        )
    )
    print(
        "F1 Score: {:.3f} (harmonic mean of the precision and recall, both equally weighted)".format(
            metrics.f1_score(
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_true
                ),  # y_true
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_pred
                ),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            )
        )
    )
    print(
        "Precision: {:.3f} (Ratio of correctly predicted positive classes to total of positive predictions)".format(
            metrics.precision_score(
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_true
                ),  # y_true
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_pred
                ),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            )
        )
    )
    print(
        "Recall: {:.3f} (Ratio of correctly predicted positive classes to all actual 'real' positive classes)".format(
            metrics.recall_score(
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_true
                ),  # y_true
                pipeline_class_obj.le.inverse_transform(
                    pipeline_class_obj.y_pred
                ),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            ),
        )
    )
    # multiclass means you can only be in one category only e.g. media format (film or tv-show)
    # multilabel means you can have multiple labels applying to the same observation e.g. genre of media (horror, shark movie, animals)
    print(
        "Area Under the Receiver Operating Characteristic Curve (ROC AUC): {:.3f}".format(
            roc_auc_score(
                y_true=y_test,
                y_score=pipeline_class_obj.pipe.named_steps["clf"].predict_proba(
                    X_test
                ),
                average="macro",
                multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                # multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
            )
        )
    )
    if pipeline_class_obj.model_type == "random_forest":
        print(
            "Out of Bag Error: {:.3f}".format(
                # 1-oob_score_ via https://scikit-learn.org/stable/auto_examples/ensemble/plot_ensemble_oob.html#id2
                1 - pipeline_class_obj.pipe.named_steps["clf"].oob_score_
            )
        )

    if (
        pipeline_class_obj.model_type == "gradient_boosting"
        or "feature_importances_" in dir(pipeline_class_obj)
    ):
        print(
            pd.DataFrame(
                {
                    "feat_name": pipeline_class_obj.RSE_info["feature_names"],
                    "feat_importance": pipeline_class_obj.pipe.named_steps[
                        "clf"
                    ].feature_importances_,
                }
            ).sort_values(by="feat_importance", ascending=False)
        )

    print(
        "Classification Report: \n",
        metrics.classification_report(
            pipeline_class_obj.le.inverse_transform(
                pipeline_class_obj.y_true
            ),  # y_true
            pipeline_class_obj.le.inverse_transform(
                pipeline_class_obj.y_pred
            ),  # y_pred
            zero_division=0,  # in later versions of sklearn options inc 0.0 or np.nan, here it's int.
            digits=3,
            # labels=ml_pipeline_dt.RSE_info["target"],
            # target_names=ml_pipeline_dt.RSE_info["target"],
        ),
    )

    # def run_cross_validation(pipeline_class_obj, X_train, y_train):
    #     cross_val_scores = cross_validate(pipeline_class_obj, X_train, y_train)
    #     print(f"{pipeline_class_obj.model_type} Cross Validation values for: model; X\n {cross_val_scores = }")


def main(
    dataset_name="ML",
    in_notebook=False,
    exists_ok=True,
    logger=None,
    datafile="sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv",
    small_vers=True,
    small_N_appx=50,
    train_pc=0.75,
    test_pc=0.25,
    shuffle_state: bool = True,
    stratify_state: bool = True,
    plot_dt_depth: int = 5,
    forest_size_rf=100,
    forest_size_hgbt=100,
    forest_size_gbt=100,
):
    # initialise class
    ml_pipeline_dt = ML_Pipeline_Decision_Tree(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
    )

    # read in dataset
    # AND format data to sklearn shapes/types/terminology
    datafile = Path(
        ml_pipeline_dt.data_location,
        datafile,
    )
    ml_pipeline_dt.get_data(
        data_file=datafile, small_vers=small_vers, small_N_appx=small_N_appx
    )

    # run decision tree and apply to test/training datasets (splitting happens within do_model_fit())
    X_test, y_test = ml_pipeline_dt.do_model_fit(
        train_pc=train_pc,
        test_pc=test_pc,
        stratify_state=stratify_state,
        shuffle_state=shuffle_state,
    )

    # CalibrationDisplay.from_estimator(clf, ml_pipeline_dt.X_test, ml_pipeline_dt.y_test)

    # plot decision tree for training dataset and save to image file
    ml_pipeline_dt.plot_decision_tree(plot_dt_depth)

    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_dt.run_predictor(
        X_test,
        y_test,
    )

    run_scoring_printouts(
        pipeline_class_obj=ml_pipeline_dt,
        X_test=X_test,
        y_test=y_test,
        datafile=datafile,
    )

    # random forests:

    ml_pipeline_rf = ML_Pipeline_Random_Forest(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
        forest_size=forest_size_rf,
        candidate_feats=ml_pipeline_dt.X_test_size[
            1
        ],  # number of features for RF and DT is same
    )

    # read in dataset
    # AND format data to sklearn shapes/types/terminology

    ml_pipeline_rf.get_data(
        data_file=datafile, small_vers=small_vers, small_N_appx=small_N_appx
    )

    # run random forest and apply to test/training datasets (splitting happens within do_model_fit())
    X_test, y_test = ml_pipeline_rf.do_model_fit(
        train_pc=train_pc,
        test_pc=test_pc,
        stratify_state=stratify_state,
        shuffle_state=shuffle_state,
    )
    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_rf.run_predictor(
        X_test,
        y_test,
    )

    run_scoring_printouts(
        pipeline_class_obj=ml_pipeline_rf,
        X_test=X_test,
        y_test=y_test,
        datafile=datafile,
    )

    # Histogram Gradient Boosting Classifier Tree:

    ml_pipeline_hgbt = ML_Pipeline_HistGradientBoosting(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
        forest_size=forest_size_hgbt,
        candidate_feats=ml_pipeline_dt.X_test_size[
            1
        ],  # number of features for HGBT and DT is same
    )

    ml_pipeline_hgbt.get_data(
        data_file=datafile, small_vers=small_vers, small_N_appx=small_N_appx
    )

    # run random forest and apply to test/training datasets (splitting happens within do_model_fit())
    X_test, y_test = ml_pipeline_hgbt.do_model_fit(
        train_pc=train_pc,
        test_pc=test_pc,
        stratify_state=stratify_state,
        shuffle_state=shuffle_state,
    )
    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_hgbt.run_predictor(
        X_test,
        y_test,
    )

    run_scoring_printouts(
        pipeline_class_obj=ml_pipeline_hgbt,
        X_test=X_test,
        y_test=y_test,
        datafile=datafile,
    )

    # Gradient Boosting Classifier Tree:

    ml_pipeline_gbt = ML_Pipeline_GradientBoosting(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
        forest_size=forest_size_gbt,
        candidate_feats=ml_pipeline_dt.X_test_size[
            1
        ],  # number of features for GBT and DT is same
    )

    ml_pipeline_gbt.get_data(
        data_file=datafile, small_vers=small_vers, small_N_appx=small_N_appx
    )

    # run random forest and apply to test/training datasets (splitting happens within do_model_fit())
    X_test, y_test = ml_pipeline_gbt.do_model_fit(
        train_pc=train_pc,
        test_pc=test_pc,
        stratify_state=stratify_state,
        shuffle_state=shuffle_state,
    )
    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_gbt.run_predictor(
        X_test,
        y_test,
    )

    run_scoring_printouts(
        pipeline_class_obj=ml_pipeline_gbt,
        X_test=X_test,
        y_test=y_test,
        datafile=datafile,
    )

    ml_utils = ML_Utils(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
    )

    models = [ml_pipeline_dt, ml_pipeline_rf, ml_pipeline_hgbt, ml_pipeline_gbt]
    for model in models:
        ml_utils.plot_learning_curves(
            model=model.pipe.named_steps["clf"],
            X=model.RSE_info["data"],
            y=model.RSE_info["target"],
            # train_size=train_pc,
        )


if __name__ == "__main__":
    main()
