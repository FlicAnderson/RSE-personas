#!/usr/bin/bash

# Configuration stuff

fspec= data/sample_repo_names_list_2025-03-31_x2632.txt
num_files=14

# Work out lines per file.

total_lines=$(wc -l <${fspec})
((lines_per_file = (total_lines + num_files - 1) / num_files))

# Split the actual file, maintaining lines.

split --lines=${lines_per_file} ${fspec} data/sample_repo_names_list_2025-03-31_x2632

# Debug information

echo "Total lines     = ${total_lines}"
echo "Lines  per file = ${lines_per_file}"    
wc -l  data/sample_repo_names_list_2025-03-31_x2632.*
