#!/bin/bash

# Command format: bash filesorter.sh "filename_glob_to_match" "existing_older_files_folder_name/" 
#
# Example run: bash filesorter.sh "all-PR-reviews_json_main-reviews" "older_PR-reviews/"
#
# Script to go through folder, find files matching name pattern specified on commandline, then for all files matching 
# the pattern per 'reponame', move all except the most-recent file to a folder specified by commandline argument.
#
# via Jakub Adamski :D and David Katz 


pattern=${1:-"all-PR-reviews"}
dest_dir=${2:-older_PR-reviews/}

REPOS=$(find . -maxdepth 1 -mindepth 1 -name "${pattern}_*.json" | sed 's/.\{16\}$//' | uniq)
for r in $REPOS; do
    mapfile -t ALL < <(find . -maxdepth 1 -mindepth 1 -wholename "$r*" |sort -r)
    [ ${#ALL[@]} -gt 1 ] && mv "${ALL[@]:1}" "${dest_dir}"
done
