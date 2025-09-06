"""Pseudonymisation of research data outputs for publication"""

# Files requiring this for ECEASST publication:
# orig_data_file = "../../data/merged-data-per-dev_x2868-repos_2025-05-10.csv"
# analysis_dataset_file = "../../data/analysis_run_sample_45pc_2025-05-12/clustered_sample_data_with_labels__2025-05-12.csv"
# # via:  "../../data/merged-data-per-dev_x2868-repos_2025-05-10.csv" and merged-interactions-data-per-dev_x2946-repos_2025-05-12.csv
# repo_stats_file = "../../data/summarised_SAMPLE_repos_stats_2025-05-09.csv"
# study_repos_file = "../../data/study-sample-repo-names_2025-05-01_x2981.txt"


# functions/scripts requiring this:
# MANY MANY SCRIPTS, see issue ticket RSE-personas/issues/2:  #2


# Get info and hash those
# Fields to hash: (repo_name; gh_username)
# fields to drop: sanitised_repo_name? issue body? commit body?

import pandas as pd
from pathlib import Path

orig_data_file = "merged-data-per-dev_x2868-repos_2025-05-10.csv"
analysis_dataset_file = "analysis_run_sample_45pc_2025-05-12/clustered_sample_data_with_labels__2025-05-12.csv"
merged_interactions = "merged-interactions-data-per-dev_x2946-repos_2025-05-12.csv"
repo_stats_file = "summarised_SAMPLE_repos_stats_2025-05-09.csv"

study_repos_file = "study-sample-repo-names_2025-05-01_x2981.txt"


file_locat = "data/"

read_files = [
    orig_data_file,
    analysis_dataset_file,
    merged_interactions,
    repo_stats_file,
]
write_names = [
    "hashed_merged_data",
    "hashed_clustered_analysis_data",
    "hashed_merged_interactions_data",
    "hashed_summarised_repo_stats_data",
]


repo_name_hashes = []
gh_username_hashes = []

column_names = []
all_repo_names = []
all_gh_usernames = []

for file in read_files:
    df = pd.read_csv(Path(file_locat, file), header=0, low_memory=False)
    column_names = column_names + list(df.columns)

    if "repo_name" in list(df.columns):
        all_repo_names = all_repo_names + sorted(set(df.repo_name))
    if "gh_username" in list(df.columns):
        all_gh_usernames = all_gh_usernames + sorted(set(df.gh_username))
    # print(set(column_names))
    print(len(set(all_repo_names)))
    print(len(set(all_gh_usernames)))

print("loop complete")
print(set(column_names))
print(len(set(all_repo_names)))
print(len(set(all_gh_usernames)))


all_repo_names = list(set(all_repo_names))
all_gh_usernames = list(set(all_gh_usernames))

repo_name_hashes = [hash(w) for w in all_repo_names]
gh_username_hashes = [hash(w) for w in all_gh_usernames]

print(len(repo_name_hashes))
print(len(gh_username_hashes))


repo_name_hashes: list[int]
gh_username_hashes: list[int]

assert len(repo_name_hashes) == len(all_repo_names)
assert len(gh_username_hashes) == len(all_gh_usernames)

drop_columns = [
    "author_username",
    "issue_author_username",
    "issue_username",
    "devs",
]

for file in read_files:
    filename = file

    print(filename)
    write_out_name = "hashed_" + filename
    print(write_out_name)

    df = pd.read_csv(Path(file_locat, file), header=0, low_memory=False)

    print(len(df.columns))
    if "repo_name" in list(df.columns):
        df.repo_name.replace(
            to_replace=all_repo_names, value=repo_name_hashes, inplace=True
        )  # replace repo_name

    if "gh_username" in list(df.columns):
        df.gh_username.replace(
            to_replace=all_gh_usernames, value=gh_username_hashes, inplace=True
        )  # replace gh_username

    if "assigned_devs" in list(df.columns):
        df.assigned_devs.replace(
            to_replace=all_gh_usernames, value=gh_username_hashes, inplace=True
        )  # replace gh_usernames in ASSIGNED DEVS

    for col in drop_columns:
        if col in list(df.columns):
            df.drop(columns=[col], inplace=True)
    print(len(df.columns))

    save_out = Path(file_locat, write_out_name)
    print(save_out)
    df.to_csv(path_or_buf=save_out, header=True, index=False)
    print(f"saved out {file}")

print("completed")
