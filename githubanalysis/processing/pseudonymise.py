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
import gc

orig_data_file = "merged-data-per-dev_x2868-repos_2025-05-10.csv"
analysis_dataset_initial_clusters_file = "analysis_run_sample_45pc_2025-05-12/clustered_sample_data_with_labels__2025-05-12.csv"
analysis_dataset_cluster0_file = "analysis_run_sample_45pc_cluster0_2025-05-13/clustered_sample_data_with_labels__2025-05-13.csv"
analysis_dataset_cluster1_file = "analysis_run_sample_45pc_cluster1_2025-05-13/clustered_sample_data_with_labels__2025-05-13.csv"
analysis_dataset_cluster2_file = "analysis_run_sample_45pc_cluster2_2025-05-13/clustered_sample_data_with_labels__2025-05-13.csv"
merged_interactions = "merged-interactions-data-per-dev_x2946-repos_2025-05-12.csv"
repo_stats_file = "summarised_SAMPLE_repos_stats_2025-05-09.csv"
analysis_dataset_all_named_personas = (
    "sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv"
)

study_repos_file = "study-sample-repo-names_2025-05-01_x2981.txt"


file_locat = "data/"

read_files = [
    orig_data_file,
    analysis_dataset_initial_clusters_file,
    analysis_dataset_cluster0_file,
    analysis_dataset_cluster1_file,
    analysis_dataset_cluster2_file,
    merged_interactions,
    repo_stats_file,
    analysis_dataset_all_named_personas,
]
write_names = [
    "hashed_merged_data",
    "hashed_clustered_analysis_initial_clusters_data",
    "hashed_clustered_analysis_cluster0_data",
    "hashed_clustered_analysis_cluster1_data",
    "hashed_clustered_analysis_cluster2_data",
    "hashed_merged_interactions_data",
    "hashed_summarised_repo_stats_data",
    "hashed_analysis_dataset_all_named_personas",
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

    del df
    gc.collect()

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


repo_name_hashes_df = pd.DataFrame(
    {"repo_name": all_repo_names, "hashed_repo_names": repo_name_hashes}
)
repo_name_hashes_df.to_csv(
    Path(file_locat, "repo_names_hash_mapping.csv"), header=True, index=False
)

gh_username_hashes_df = pd.DataFrame(
    {"gh_username": all_gh_usernames, "hashed_gh_username": gh_username_hashes}
)
gh_username_hashes_df.to_csv(
    Path(file_locat, "gh_username_hash_mapping.csv"), header=True, index=False
)


print("written hashes and repo_names and gh_usernames out to csv")

drop_columns = [
    "author_username",
    "issue_author_username",
    "issue_username",
    "devs",
]


repo_name_matches = {}
for i in range(len(all_repo_names)):
    repo_name_matches[all_repo_names[i]] = repo_name_hashes[i]

gh_usernames_matches = {}
for i in range(len(all_gh_usernames)):
    gh_usernames_matches[all_gh_usernames[i]] = gh_username_hashes[i]


for file in read_files:
    filename = file

    print(filename)
    filename = filename.replace("/", "__")
    write_out_name = "hashed_" + filename
    print(write_out_name)

    df = pd.read_csv(Path(file_locat, file), header=0, low_memory=False)

    print(len(df.columns))

    if "repo_name" in list(df.columns):
        # df.repo_name = df.repo_name.replace(
        #     to_replace=all_repo_names,
        #     value=repo_name_hashes,  # inplace=True
        # )  # replace repo_name
        # df.repo_name = df.repo_name.replace(repo_name_matches)
        df.repo_name = df.repo_name.map(lambda x: repo_name_matches.get(x, x))

    if "gh_username" in list(df.columns):
        # df.gh_username = df.gh_username.replace(
        #     to_replace=all_gh_usernames,
        #     value=gh_username_hashes,  # inplace=True
        # )  # replace gh_username
        df.gh_username = df.gh_username.map(lambda x: gh_usernames_matches.get(x, x))

    if "assigned_devs" in list(df.columns):
        # df.assigned_devs = df.assigned_devs.replace(
        #     to_replace=all_gh_usernames,
        #     value=gh_username_hashes,  # inplace=True
        # )  # replace gh_usernames in ASSIGNED DEVS
        # df.assigned_devs = df.assigned_devs.replace(gh_usernames_matches)
        df.assigned_devs = df.assigned_devs.map(
            lambda x: gh_usernames_matches.get(x, x)
        )

    for col in drop_columns:
        if col in list(df.columns):
            df = df.drop(
                columns=[col],
            )  # inplace=True)
    print(len(df.columns))

    save_out = Path(file_locat, write_out_name)
    print(save_out)
    df.to_csv(path_or_buf=save_out, header=True, index=False)
    print(f"saved out {save_out}")
    del df
    gc.collect()

print("completed")


# study_repos_file

with open(Path(file_locat, study_repos_file), "r") as f:
    study_repos = [txtline.strip() for txtline in f.readlines()]

study_repos = [repo_name_matches[repo] for repo in study_repos]

with open(
    Path(file_locat, "hashed_study-sample-repo-names_2025-05-01_x2981.txt"), "w"
) as file:
    for repo in study_repos:
        if repo is not None:
            file.write(f"{repo}\n")
        else:
            continue
