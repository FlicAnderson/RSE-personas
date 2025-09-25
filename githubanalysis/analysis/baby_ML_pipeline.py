from logging import Logger
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import graphviz

from sklearn.pipeline import (
    Pipeline,
)  # diff twixt make_pipeline()/Pipeline(): https://stackoverflow.com/a/40708448
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# from sklearn import tree
from sklearn.tree import plot_tree, export_graphviz
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import ConfusionMatrixDisplay

from githubanalysis.setup_classes import DatasetSetup


class ML_pipeline_decision_tree(
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
                # ("le", OneHotEncode()),
                ("clf", DecisionTreeClassifier()),
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

    def test_train_data(
        self,
        train_pc=0.75,
        test_pc=0.25,
        shuffle_state=True,
        stratify_state=True,
    ):
        X, y = self.RSE_info["data"], self.RSE_info["target"]

        assert (
            (1 - train_pc) == test_pc
        ), f"Values for train_pc and test_pc must total 1; test_pc is currently set to {test_pc}"
        # returning the function which creates a tuple of 4x:
        #  X_train, X_test, y_train, y_test
        if stratify_state:
            return train_test_split(
                X,
                y,
                test_size=test_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 25%
                train_size=train_pc,  # by (sklearn) default if int: N of samples; if float: proportion of sample; if None and train_size=None also, it uses 75%
                random_state=42,
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
                random_state=42,
                shuffle=shuffle_state,
            )

    def do_decision_tree(self, train_pc, test_pc, shuffle_state, stratify_state):
        X_train, X_test, y_train, y_test = self.test_train_data(
            train_pc=train_pc,
            test_pc=test_pc,
            shuffle_state=shuffle_state,
            stratify_state=stratify_state,
        )

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
            class_names=self.RSE_info["target_names"],
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
            class_names=self.RSE_info["target_names"],
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
        saveout_name = Path(self.image_write_location, "decision_tree_initial.pdf")
        plt.savefig(saveout_name, **saveout_args)

        print(
            f'attempted to save out to : {Path(self.image_write_location, "decision_tree_initial.pdf")}'
        )
        plt.show()

    def run_predictor(
        self,
        X_test,
        y_test,
    ):
        y_pred = self.pipe.predict(X_test)
        y_true = y_test

        # savefig kwargs
        saveout_args = dict(
            dpi=400,
            format="pdf",
            bbox_inches="tight",
        )
        dataset_size = len(X_test)

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
                self.le.inverse_transform(y_true),  # y_true
                self.le.inverse_transform(y_pred),  # y_pred
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
                f"confusion_matrix_MRC_tinytestset_normalise{normalize}_{self.current_date_info}.pdf",
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
    ml_pipeline_dt = ML_pipeline_decision_tree(
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

    # run decision tree and apply to test/training datasets (splitting happens within do_decision_tree())
    X_test, y_test = ml_pipeline_dt.do_decision_tree(
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


if __name__ == "__main__":
    main()
