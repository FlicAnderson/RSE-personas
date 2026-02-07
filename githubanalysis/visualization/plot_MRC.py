import datetime
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")
print(current_date_info)


set1data = pd.read_csv(
    "data/sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv",
    header=0,
    low_memory=False,
)
# set1data = pd.read_csv("../../data/hashed_sample_45pc_all_subclusters_named_personas_dataset_2025-09-16.csv", header=0, low_memory=False)
set1data = set1data.rename(columns={"pc_DC": "MRC", "breadth_interactions": "UIT"})


all_personas_sample_data = set1data

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

all_personas_sample_data.sort_values(by="RSE_persona")
cat_labels = [
    "Ephemeral Contributor",
    "Occasional Contributor",
    "Project Organiser",
    "Moderate Contributor",
    "Low-Process Closer",
    "Low-Coding Closer",
    "Active Contributor",
]

persona_palette = {
    "Ephemeral Contributor": "#FDBC42",
    "Occasional Contributor": "#FDBC42",
    "Project Organiser": "#D50032",
    "Moderate Contributor": "#D50032",
    "Low-Process Closer": "#1D2A3D",
    "Low-Coding Closer": "#1D2A3D",
    "Active Contributor": "#1D2A3D",
}

hatches = [
    "..",  # low ephem
    "//",  # low occas
    "//",  # mod proje
    "..",  # mod moder
    "x",  # hi loproc
    "//",  # hi locode
    "..",  # hi activ
]
box_line_col = [
    "#000000",
    "#000000",  # low: black
    "#000000",
    "#000000",  # moderate: black
    "#FFFFFF",
    "#FFFFFF",
    "#FFFFFF",  # high: white
]

ax = sns.boxplot(
    all_personas_sample_data,
    x="RSE_persona",
    y="MRC",
    hue="RSE_persona",
    dodge=False,
    # legend=True,
    order=cat_labels,
    hue_order=cat_labels,
    palette=persona_palette,
)
ax.set(xticklabels=[])
ax.set(ylabel="Mean MRC %")
ax.set_title("RSE Personas: MRC means")
ax.set_xlabel("RSE Persona")
# label_color_dict = {0:'#D50032', 1:'#1D2A3D', 2:'#FDBC42'} # universityred, epccnavy, dandelion,

patches = [patch for patch in ax.patches if type(patch) == mpl.patches.PathPatch]
# the number of patches should be evenly divisible by the number of hatches
h = hatches * (len(patches) // len(hatches))
# dg = edgescol * (len(patches) // len (edgescol))
# iterate through the patches for each subplot
for patch, hatch, box_col in zip(patches, h, box_line_col):
    patch.set_hatch(hatch)
    fc = patch.get_facecolor()
    ec = patch.set_edgecolor(box_col)
#     patch.set_facecolor('#D50032')

leg = ax.legend()

for lp, hatch, box_col in zip(leg.get_patches(), hatches, box_line_col):
    lp.set_hatch(hatch)
    fc = lp.get_facecolor()
    ec = lp.set_edgecolor(box_col)
    # lp.set_facecolor('#FFFFFF')

cat_labels = [
    "Ephemeral Contributor",
    "Occasional Contributor",
    "Project Organiser",
    "Moderate Contributor",
    "Low-Process Closer",
    "Low-Coding Closer",
    "Active Contributor",
]
# sns.move_legend(ax, "upper right", bbox_to_anchor=(1, 1))

leg.set_label(cat_labels)
sns.move_legend(
    ax,
    "upper left",
    title=None,
    frameon=False,
    bbox_to_anchor=(1, 1),
)

plt.savefig(
    f"images/45pc_RSE-Personas_MRC_{current_date_info}.pdf", bbox_inches="tight"
)
plt.savefig(
    f"images/45pc_RSE-Personas_MRC_{current_date_info}.png", bbox_inches="tight"
)
