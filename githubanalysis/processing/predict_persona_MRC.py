"""Predict / Classify RSE Personas based on MRC (mean repository contribution)"""

import pandas as pd
from pathlib import Path
from typing import Literal


def makeRSE_persona_ranges(
    file: Path = Path(
        "data/sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv"
    ),
):
    all_personas_sample_data = pd.read_csv(file, header=0, low_memory=False)
    all_personas_sample_data = all_personas_sample_data.rename(
        columns={"pc_DC": "MRC", "breadth_interactions": "UIT"}
    )
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("ephemeral_contributor", "Ephemeral Contributor")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("occasional_contributor", "Occasional Contributor")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("project_organiser", "Project Organiser")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("moderate_contributor", "Moderate Contributor")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("low-process_closer", "Low-Process Closer")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("low-coding_closer", "Low-Coding Closer")
    all_personas_sample_data["RSE_persona"] = all_personas_sample_data[
        "RSE_persona"
    ].str.replace("active_contributor", "Active Contributor")

    def theIQR(column):
        q25, q75 = column.quantile([0.25, 0.75])
        return (q25, q75)

    def IQrange(column):
        q25, q75 = column.quantile([0.25, 0.75])
        return q75 - q25

    stats_list = [
        "min",
        "max",
        "mean",
        "median",
        "std",
        "var",
        IQrange,
        theIQR,
    ]

    RSE_persona_ranges = (
        all_personas_sample_data.groupby(by="RSE_persona")["MRC"]
        .agg(func=stats_list)
        .reset_index()
    )

    return RSE_persona_ranges


def persona_tester(
    MRC_value: float,
    RSE_persona_ranges: pd.DataFrame,
    average: Literal["mean", "median"] = "mean",
) -> tuple[list[str], dict[float, str]]:
    """
    Take MRC value, compare against RSE Persona inter-quartile range (25%-75%)
    and return tuple where:
       0) is a list of personas where MRC fits within the IQ range
       1) is a sorted dictionary of differences between MRC_value and the average ("mean" or "median") of each RSE Persona

    Examples:

    > persona_tester(45.0, RSE_persona_ranges, "mean")
    ... output:
    (['Low-Coding Closer', 'Low-Process Closer'],
    {2.4580644317688396: 'Low-Process Closer',
    5.08418544897836: 'Low-Coding Closer',
    13.676645879598695: 'Moderate Contributor',
    24.104012114479488: 'Active Contributor',
    30.146688410594322: 'Project Organiser',
    41.58819362993757: 'Occasional Contributor',
    44.85046864671744: 'Ephemeral Contributor'})


    > persona_tester(7, RSE_persona_ranges, "mean")
    ... output:
    (['Unclassified'],
    {3.5881936299375705: 'Occasional Contributor',
    6.85046864671744: 'Ephemeral Contributor',
    7.853311589405676: 'Project Organiser',
    24.323354120401305: 'Moderate Contributor',
    35.54193556823116: 'Low-Process Closer',
    43.08418544897836: 'Low-Coding Closer',
    62.10401211447949: 'Active Contributor'})

    > persona_tester(67.563268, RSE_persona_ranges, "mean")
    ... output:
    (['Active Contributor'],
    {1.5407441144794944: 'Active Contributor',
    17.479082551021634: 'Low-Coding Closer',
    25.021332431768833: 'Low-Process Closer',
    36.23991387959869: 'Moderate Contributor',
    52.709956410594316: 'Project Organiser',
    64.15146162993756: 'Occasional Contributor',
    67.41373664671744: 'Ephemeral Contributor'})

    """

    comparers = {}
    prediction = []

    for (
        _,  # the underscore is an iterator thing. LEAVE IT ALONE
        personarow,
    ) in RSE_persona_ranges.iterrows():
        compar_val = abs(personarow[average] - MRC_value)
        comparers[compar_val] = personarow["RSE_persona"]

        _25q, _75q = personarow["theIQR"]
        if MRC_value > _25q and MRC_value < _75q:
            prediction.append(personarow["RSE_persona"])

    diffs = {diff: comparers[diff] for diff in sorted(comparers.keys())}

    if not prediction:
        prediction = ["Unclassified"]

    return (prediction, diffs)
