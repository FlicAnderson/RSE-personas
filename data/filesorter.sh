#!/bin/bash

# via Jakub Adamski :D

REPOS=$(ls processed-commits_*.csv | sed 's/.\{15\}$//' | uniq)
for r in $REPOS
do
    ALL=($(ls $r* | sort -r))
    [ ${#ALL[@]} -gt 1 ] && mv "${ALL[@]:1}" older_processed_commits/
done

REPOS=$(ls processed-commits_*_2024*.csv)
mv $REPOS older_processed_commits/

REPOS=$(ls processed-issues_*.csv | sed 's/.\{15\}$//' | uniq)
for r in $REPOS
do
    ALL=($(ls $r* | sort -r))
    [ ${#ALL[@]} -gt 1 ] && mv "${ALL[@]:1}" older_processed_issues/
done

REPOS=$(ls processed-issues_*_2024*.csv)
mv $REPOS older_processed_issues/

REPOS=$(ls commits_changes_*.csv | sed 's/.\{15\}$//' | uniq)
for r in $REPOS
do
    ALL=($(ls $r* | sort -r))
    [ ${#ALL[@]} -gt 1 ] && mv "${ALL[@]:1}" older_commits_changes/
done

REPOS=$(ls commits_changes_*_2024*.csv)
mv $REPOS older_commits_changes/

REPOS=$(ls commits_cats_stats_*.csv | sed 's/.\{15\}$//' | uniq)
for r in $REPOS
do
    ALL=($(ls $r* | sort -r))
    [ ${#ALL[@]} -gt 1 ] && mv "${ALL[@]:1}" older_commits_cats_stats/
done

REPOS=$(ls commits_cats_stats_*_2024*.csv)
mv $REPOS older_commits_cats_stats/

