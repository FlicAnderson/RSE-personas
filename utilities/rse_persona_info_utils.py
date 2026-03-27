"""This contains details on getting consistent parameters for plotting and visualising RSE Persona data"""

import pandas as pd
from dataclasses import dataclass


@dataclass
class RSE_personas_info:
    cat_labels = [
        "Ephemeral Contributor",
        "Occasional Contributor",
        "Project Organiser",
        "Moderate Contributor",
        "Low-Process Closer",
        "Low-Coding Closer",
        "Active Contributor",
    ]

    persona_abbrevs = [
        "Ephm",
        "Occs",
        "PrOg",
        "Modr",
        "LoPr",
        "LoCo",
        "Actv",
    ]

    persona_palette = {
        0: "#D50032",
        1: "#D50032",
        2: "#FDBC42",
        3: "#FDBC42",
        4: "#1D2A3D",
        5: "#1D2A3D",
        6: "#1D2A3D",
    }
    name_palette = {
        0: "Ephemeral Contributor",
        1: "Occasional Contributor",
        2: "Project Organiser",
        3: "Moderate Contributor",
        4: "Low-Process Closer",
        5: "Low-Coding Closer",
        6: "Active Contributor",
    }
    marks_palette = {  # https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
        0: "o",
        1: "^",
        2: "v",
        3: "s",
        4: "D",
        5: "X",
        6: "*",
    }
    fill_pallette = {  # one of these specific Literal options: https://matplotlib.org/stable/api/_as_gen/matplotlib.markers.MarkerStyle.html#matplotlib-markers-markerstyle
        0: "full",
        1: "full",
        2: "full",
        3: "full",
        4: "full",
        5: "full",
        6: "full",
    }
    edge_pallette = {
        0: None,
        1: "grey",
        2: None,
        3: "grey",
        4: "darkblue",
        5: "grey",
        6: "darkturquoise",
    }

    def get_params_based_on_cluster_info(self, cluster_labels: pd.Series):
        persona_idx = []
        persona_col = []
        persona_mark = []
        persona_fill = []
        persona_edge = []
        persona_name = []

        # determine correct params for this dataset based on RSE Persona categories present in the data cluster_labels
        for i in cluster_labels.unique():
            if i in self.persona_palette.keys():
                persona_idx.append(i)
                persona_col.append(self.persona_palette[i])
                persona_mark.append(self.marks_palette[i])
                persona_fill.append(self.fill_pallette[i])
                persona_edge.append(self.edge_pallette[i])
                persona_name.append(self.name_palette[i])

        return (
            persona_idx,
            persona_col,
            persona_mark,
            persona_fill,
            persona_edge,
            persona_name,
        )
