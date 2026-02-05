#!/usr/bin/bash

# Configuration stuff

fspec=data/set2_sample_55pc_subsample_repo_names_list_2026-02-05_x1697.txt
num_files=16

# Work out lines per file.

total_lines=$(wc -l <${fspec})
((lines_per_file = (total_lines + num_files - 1) / num_files))

# Split the actual file, maintaining lines.

split --lines=${lines_per_file} ${fspec} data/set2_sample_55pc_subsample_repo_names_list_2026-02-05_x1697

# Debug information

echo "Total lines     = ${total_lines}"
echo "Lines  per file = ${lines_per_file}"    
wc -l  data/set2_sample_55pc_subsample_repo_names_list_2026-02-05_x1697*
