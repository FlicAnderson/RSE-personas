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
from sklearn.metrics import roc_auc_score
from sklearn.tree import plot_tree, export_graphviz
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
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
                f"confusion_matrix_normalise{normalize}_N{self.X_test_size[0]}_{self.current_date_info}.pdf",
            )
            plt.savefig(
                saveout_name,
                **saveout_args,
            )
            plt.show()


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
    depth: int = 5,
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

    # plot decision tree for training dataset and save to image file
    ml_pipeline_dt.plot_decision_tree(depth)

    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_dt.run_predictor(
        X_test,
        y_test,
    )

    # Model Accuracy, how often is the classifier correct?
    print(
        f"""
        For DECISION TREE model trained on: \n
          datafile: {datafile} \n
          training-set size: N={ml_pipeline_dt.X_train_size[0]} \n
          and evaluated using test-set size: N={ml_pipeline_dt.X_test_size[0]} repo-individuals \n
          using N={ml_pipeline_dt.X_test_size[1]} features \n 
          at {ml_pipeline_dt.current_date_info}
        """
    )

    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html#sklearn.metrics.accuracy_score
    print(
        "Accuracy: {:.2f} (percent of correctly classified samples)".format(
            metrics.accuracy_score(ml_pipeline_dt.y_true, ml_pipeline_dt.y_pred),
        )
    )
    print(
        "Non-Normalised Accuracy: {:.2f} (number of correctly classified samples)".format(
            metrics.accuracy_score(
                ml_pipeline_dt.y_true, ml_pipeline_dt.y_pred, normalize=False
            ),
        )
    )
    print(
        "Balanced Accuracy: {:.2f} (the average of recall obtained on each class)".format(
            metrics.balanced_accuracy_score(
                ml_pipeline_dt.y_true,
                ml_pipeline_dt.y_pred,
                adjusted=False,
            )
        )
    )
    print(
        "F1 Score: {:.2f} (harmonic mean of the precision and recall, both equally weighted)".format(
            metrics.f1_score(
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_true),  # y_true
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_pred),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            )
        )
    )
    print(
        "Precision: {:.2f} (Ratio of correctly predicted positive classes to total of positive predictions)".format(
            metrics.precision_score(
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_true),  # y_true
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_pred),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            )
        )
    )
    print(
        "Recall: {:.2f} (Ratio of correctly predicted positive classes to all actual 'real' positive classes)".format(
            metrics.recall_score(
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_true),  # y_true
                ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_pred),  # y_pred
                average="macro",  # metrics for each label with the unweighted means. (doesn't account for label imbalance)
                # labels=ml_pipeline_dt.RSE_info["target"],
                # target_names=ml_pipeline_dt.RSE_info["target"],
            ),
        )
    )
    print(
        "Classification Report: \n",
        metrics.classification_report(
            ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_true),  # y_true
            ml_pipeline_dt.le.inverse_transform(ml_pipeline_dt.y_pred),  # y_pred
            # labels=ml_pipeline_dt.RSE_info["target"],
            # target_names=ml_pipeline_dt.RSE_info["target"],
        ),
    )
    # multiclass means you can only be in one category only e.g. media format (film or tv-show)
    # multilabel means you can have multiple labels applying to the same observation e.g. genre of media (horror, shark movie, animals)
    print(
        "Area Under the Receiver Operating Characteristic Curve (ROC AUC): {:.2f}".format(
            roc_auc_score(
                y_true=y_test,
                y_score=ml_pipeline_dt.pipe.named_steps["clf"].predict_proba(X_test),
                average="macro",
                multi_class="ovr",  # one-vs-rest: Computes the AUC of each class against the rest (sensitive to class imbalance)
                # multi_class="ovo",  # one-vs-one: SLOWER; Computes the AUC of each class against all possible pairwise combos of class (INsensitive to class imbalance)
            )
        )
    )

    # decision trees:

    ml_pipeline_RF = ML_Pipeline_Random_Forest(
        dataset_name=dataset_name,
        in_notebook=in_notebook,
        exists_ok=exists_ok,
        logger=logger,
        forest_size=100,
        input_data=ml_pipeline_dt,
    )

    # run decision tree and apply to test/training datasets (splitting happens within do_decision_tree())
    X_test, y_test = ml_pipeline_RF.do_model_fit(
        train_pc=train_pc,
        test_pc=test_pc,
        stratify_state=stratify_state,
        shuffle_state=shuffle_state,
    )

    # predict classifications for test dataset, plot confusion matrices
    ml_pipeline_RF.run_predictor(
        X_test,
        y_test,
    )

    # RandomForestClassifier.decision_path(X_test)

    # Model Accuracy, how often is the classifier correct?
    print(
        f"""
        For RANDOM FOREST model trained on: \n
          datafile: {datafile} \n
          training-set size: N={ml_pipeline_RF.X_train_size[0]} \n
          and evaluated using test-set size: N={ml_pipeline_RF.X_test_size[0]} repo-individuals \n
          using N={ml_pipeline_RF.X_test_size[1]} features \n 
          with N={ml_pipeline_RF.forest_size} trees in forest  \n
          at {ml_pipeline_RF.current_date_info}
        """
    )


class ML_Pipeline_Random_Forest(ML_Pipeline_Decision_Tree):
    def __init__(
        self,
        dataset_name,
        in_notebook: bool,
        input_data: ML_Pipeline_Decision_Tree,
        exists_ok: bool = False,
        logger: None | Logger = None,
        forest_size: int = 100,
    ) -> None:
        super().__init__(dataset_name, in_notebook, exists_ok, logger)
        self.__dict__.update(  # THIS IS VERY BAD BUT WAS DONE TO PULL THE DATA OBJECTS THROUGH NICELY
            input_data.__dict__
        )  # pull in contents of input_data (RSE_info, X_test, Y_test, X_train, y_train, etc)
        self.y_pred = None
        self.y_true = None
        self.le = LabelEncoder()
        # create a pipeline object
        self.forest_size = (int(forest_size),)
        if self.RSE_info:
            # calculate F: number of predictors used to select the best split
            # F = log2(M+1) # M is number total predictors; # F
            # Leo Breiman. 2001. Random Forests. Machine Learning 45, 1 (Oct. 2001), 5–32.
            # doi:10.1023/A:1010933404324
            self.candidate_feats_Nplusone = round(
                math.log2(
                    len(self.RSE_info["feature_names"])
                    + 1  # F = log2(M+1) # M is number total predictors;
                )
            )
            assert isinstance(self.candidate_feats_Nplusone, int), (
                "somehow candidate_feats_Nplusone is not an integer; fix this as floats would lead to a fraction being used in Random Forest candidate feature splitting..."
            )
        else:
            self.candidate_feats_Nplusone = (
                "sqrt"  # default in RandomForestClassifier(max_features=) param
            )
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
                        max_features=self.candidate_feats_Nplusone,  #'int', 'float', 'sqrt':sqrt(n_features), 'log2':log2(n_features), 'None':(max_features=n_features)
                        bootstrap=True,
                        max_samples=None,  # controls sub-sampling for bootstrapping
                        oob_score=True,  # Whether to use out-of-bag samples to estimate the generalization score. By default, accuracy_score is used.# can use custom metric.
                        n_jobs=None,  # how many to run in paralell... None~=use 1.
                        # verbose=0, # verbosity
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


if __name__ == "__main__":
    main()
