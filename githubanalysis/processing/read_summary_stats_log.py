"""Pull Summarised Repo Stats Data out of logs from lots/summarise_repo_stats_logs.txt to usable pandas df in csv."""

import datetime
import pandas as pd

current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")

with open("./logs/summarise_repo_stats_logs.txt", "r") as file:
    content = file.readlines()
items = []

for line in content:
    if "INFO:Stats for" in line:
        line_ = line[line.index("INFO:Stats for") + len("INFO:Stats for") :]
        a, b = map(str.strip, line_.split(":", 1))
        items.append(b)

for i in range(len(items)):
    item = items[i]
    if "dict_keys" in item:
        part_1 = item[: item.index("dict_keys")]
        part_2 = item[item.index("dict_keys") :]
        part_3 = part_2[part_2.index("])") + 2 :]
        part_2 = part_2[
            part_2.index("dict_keys(") + len("dict_keys(") : part_2.index(")")
        ]
        items[i] = eval(part_1 + part_2 + part_3)
    elif "'None'" in item:
        items[i] = eval(item.replace("'None'", "None"))

repo_stats = pd.DataFrame.from_records(items)
saveas = f"summarised_repo_stats_{current_date_info}.csv"
repo_stats.to_csv(f"./data/{saveas}", index=False)
