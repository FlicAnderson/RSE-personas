from logging import Logger
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cmx

# from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn import tree
from sklearn.tree import plot_tree

from sklearn.metrics import ConfusionMatrixDisplay

from githubanalysis.setup_classes import DatasetSetup
from githubanalysis.processing.predict_persona_MRC import (
    persona_tester,
    makeRSE_persona_ranges,
)


class ML_pipeline_decision_tree(DatasetSetup):
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
        super().__init__(dataset_name, in_notebook, exists_ok, logger)

    def get_data(self, data_file, small_vers=True, small_N_appx: int | None = 20):
        dataset_df = pd.read_csv(
            Path(
                self.data_read_location,
                "sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv",
            ),
            header=0,
            low_memory=False,
        )

        if "pc_DC" in dataset_df.columns:
            dataset_df = dataset_df.rename(
                columns={"pc_DC": "MRC", "breadth_interactions": "UIT"}
            )

        if small_vers:
            n_per_persona = round(small_N_appx / 7)
            dataset_df = dataset_df.groupby(by="RSE_persona").sample(
                n=n_per_persona, weights="MRC"
            )

        RSE_persona_ranges = makeRSE_persona_ranges(
            file=Path(
                self.data_read_location,
                "sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv",
            )
        )

        classification_results_MRC = dataset_df[
            "MRC"
        ].apply(
            lambda x: persona_tester(
                x, RSE_persona_ranges, "median"
            )  # classify repo-individual (row) based on MRC value against inter-quartile range match.
        )

        MRCclass = list(zip(*classification_results_MRC))
        dataset_df["MRC_classification"] = MRCclass[0]
        # dataset_df["MRC_classification_pickone"] = dataset_df[
        #     "MRC_classification"
        # ].apply(
        #     lambda x: x[0]  # take items out of list
        # )  # TAKE FIRST IN LIST (THIS IS VERY BROKEN BUT MRC IS NOT ESPECIALLY USEFUL METRIC)
        dataset_df["MRC_distances_to_median"] = MRCclass[1]
        dataset_df["MRC_classification_nearest_one"] = dataset_df[
            "MRC_distances_to_median"
        ].apply(
            lambda x: x[min(x)]
        )  # select the item in the sorted dictionary with smallest 'key' aka nearest distance

        classified_df = dataset_df

        return classified_df

    def create_sklearn_format_data(self, classified_df: pd.DataFrame):
        clustering_variables = [  # THIS IS IMPORTANT: THESE WILL BE USED FOR CLUSTERING AND PCA VARIABLE FEATURE RANKING
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

        self.RSE_info = {
            "data": classified_df[
                clustering_variables
            ].to_numpy(),  # data w/o labels, list per row
            "target": self.le.fit_transform(
                classified_df["RSE_persona"]
            ),  # numerical version of class assignment
            "feature_names": clustering_variables,
            "target_names": classified_df["RSE_persona"].unique(),
        }

        return self.RSE_info

    def test_train_data(self):
        X, y = self.RSE_info["data"], self.RSE_info["target"]

        # returning the function which creates a tuple of 4x:
        #  X_train, X_test, y_train, y_test
        return train_test_split(X, y, random_state=42)

    def do_decision_tree(self, RSE_info):
        X_train, X_test, y_train, y_test = self.test_train_data(RSE_info)

        clf = (
            tree.DecisionTreeClassifier()
        )  # creates classifier obj with decision tree method
        clf = clf.fit(X_train, y_train)  # updates classifier by fitting to data
        return clf, X_train, X_test, y_train, y_test

    def plot_decision_tree(self, clf):
        plot_tree(
            clf,
            filled=True,
            feature_names=self.RSE_info["feature_names"],
            class_names=self.RSE_info["target_names"],
        )
        plt.title("Decision tree trained on all RSE Persona clustering features")
        plt.savefig(
            Path(DatasetSetup.image_write_location, "decision_tree_initial.pdf")
        )

        print(
            f'attempted to save out to : {Path(DatasetSetup.image_write_location, "decision_tree_initial.pdf")}'
        )
        # plt.show()

    def run_predictor(
        self,
        clf,
        X_test,
        y_test,
        classified_df,
    ):
        y_pred = clf.predict(X_test)
        y_true = y_test

        # savefig kwargs
        saveout_args = dict(
            dpi=400,
            format="pdf",
            bbox_inches="tight",
        )
        dataset_size = len(classified_df)

        # Plot non-normalized confusion matrix
        titles_options = [
            (
                f"confusion matrix, no normalization (N={dataset_size})",
                None,
            ),
            (
                f"normalized confusion matrix (N={dataset_size})",
                "true",
            ),  # normalise on True value pcs
        ]

        for title, normalize in titles_options:
            disp = ConfusionMatrixDisplay.from_predictions(
                self.le.inverse_transform(y_true),  # y_true
                self.le.inverse_transform(y_pred),  # y_pred
                labels=self.le.inverse_transform(clf.classes_),
                sample_weight=None,
                normalize=None,  # 'all': total N samples; 'pred': over predictions; 'true': over true; None: default
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

            plt.savefig(
                Path(
                    self.image_write_location,
                    f"confusion_matrix_MRC_tinytestset_normalise{normalize}_{self.current_date_info}.pdf",
                )
                ** saveout_args,
            )
