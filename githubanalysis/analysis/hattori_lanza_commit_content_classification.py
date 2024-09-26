"""Hattori Lanza commit content classification method implementation on GH API commit data from Research Software repositories."""

main_categories = ["Development", "Maintenance"]
detail_categories = [
    "Forward_Engineering",
    "Reengineering",
    "Corrective_Engineering",
    "Management",
]

fwd_eng = [  # Development: forward engineering
    "implement",
    "add",
    "request",
    "new",
    "start",
    "includ",
    "initial",
    "introduc",
    "creat",
    "increas",
]

re_eng = [
    "optimiz",
    "adjust",
    "updat",  # changed from 'update' in paper: table 2
    "delet",
    "remov",
    "chang",
    "replac",
    "modif",
    # "(is, are) now", # removed for now until figure out how to require is/are beforehand
    "enhanc",
    "improv",
    "design change",
    "renam",
    "eliminat",
    "duplicat",
    "restructur",
    "simplif",
    "obsolete",
    "rearrang",
    "miss",
    "enhanc",
    "improv",
]

cor_eng = ["bug", "fix", "issue", "error", "proper", "deprecat", "broke"]

mgmt = [
    "clean",
    "licens",  # changed from 'license' in paper: table2
    "merg",  # changed from 'merge' in paper: table2
    "release",
    "structure",
    "integrat",
    "copyright",
    "documentation",
    "manual",
    "javadoc",
    "comment",
    "migrat",
    "code review",
    "polish",
    "upgrade",
    "style",
    "formatting",
    "organiz",
    "TODO",
    "docs",  # added by @FlicAnderson
]
