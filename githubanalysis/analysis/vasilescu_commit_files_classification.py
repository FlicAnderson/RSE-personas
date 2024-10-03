"""Application of Vasilescu et al. 2014 method of classifying commits by filetypes of files changed, using pre-obtained github commit data for Research Software repositories"""

import logging
import pandas as pd
import re

import utilities.get_default_logger as loggit


class Vasilescu_Commit_Classifier:
    logger: logging.Logger

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/vasilescu_commit_files_classification_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.config_path = config_path
        self.in_notebook = in_notebook
        # # write-out file setup
        # self.current_date_info = datetime.datetime.now().strftime(
        #     "%Y-%m-%d"
        # )  # run this at start of script not in loop to avoid midnight/long-run commits
        # self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name

        # ALL CATEGORY TYPES:
        self.v_cats = [  # category acronyms, and their Activity Type (t):
            "doc",  # Documentation
            "img",  # Images
            "l10n",  # Localization
            "ui",  # User Interface
            "media",  # Multimedia
            "code",  # Coding
            "meta",  # Meta
            "config",  # Configuration
            "build",  # Building
            "devdoc",  # Development Documentation
            "db",  # Databases / Data
            "test",  # Testing
            "lib",  # Library
            "unknown",  # Unknown
        ]

        # REGULAR EXPRESSIONS FOR CATEGORIES:
        self.cat_unknown = [".*"]
        self.cat_doc = [
            ".*\.md",  # Milewicz et al. addition
            ".*\.((s|x|g|p|(gt))?)htm(l?)",
            ".*/translators",
            ".*/contributors",
            ".*/doc(-?)book(s?)/.*",
            ".*\.page",
            ".*/info",
            ".*\.l",
            ".*\.zabw",
            ".*/potfiles",
            ".*/install",
            ".*\.wml",
            ".*\.chm",
            ".*\.ods",
            ".*/copyright",
            ".*/version",
            ".*\.css",
            ".*\.vcard(~?)",
            ".*/plan",
            ".*/feature(s?)",
            ".*\.txt((\.bak)?)",
            ".*/credits",
            ".*/notes",
            ".*/licence",
            ".*\.txt((\.old)?)",
            ".*\.man",
            ".*/howto",
            ".*/license",
            ".*\.rtf",
            ".*\.ics",
            ".*/faq",
            ".*/maintainers",
            ".*\.tex",
            ".*/documenters",
            ".*copying",
            ".*/copying",
            ".*\.sgml",
            ".*\.gnumeric",
            ".*/copying.*",
            ".*/committers",
            ".*\.eps",
            ".*\.vcf",
            ".*/doc(s?)/.*",
            ".*/thanks",
            ".*\.xsd",
            ".*\.schemas",
            ".*/help(s?)/.*",
            ".*/authors",
            ".*\.texi",
            ".*\.doc",
            ".*/bugs",
            ".*\.docx",
        ]
        self.cat_code = [
            ".*\.pas((\.swp)?)( ̃?)",  # Milewicz et al. addition
            ".*\.pxd((\.swp)?)( ̃?)",  # Milewicz et al. addition
            ".*\.ads((\.swp)?)( ̃?)",  # Milewicz et al. addition
            ".*\.adb((\.swp)?)( ̃?)",  # Milewicz et al. addition
            ".*\.bin",  # Milewicz et al. addition
            ".*/src/.*",
            ".*\.exe(~?)",
            ".*\.dmg(~?)",
            ".*\.swg(~?)",
            ".*\.so(~?)",
            ".*\.i(~?)",
            ".*\.o(~?)",
            ".*\.exe(~?)",
            ".*\.oafinfo(~?)",
            ".*\.pyd(~?)",
            ".*\.c((\.swp)?)(~?)",
            ".*\.py((\.swp)?)(~?)",
            ".*\.r((\.swp)?)(~?)",
            ".*\.java((\.swp)?)(~?)",
            ".*\.awk(~?)",
            ".*\.scm(~?)",
            ".*\.glsl(~?)",
            ".*\.patch(~?)",
            ".*\.c((\.swp)?)(~?)",
            ".*/script(s?)/.*",
            ".*\.jar(~?)",
            ".*/src/.*",
            ".*\.m((\.swp)?)(~?)",
            ".*\.cs(~?)",
            ".*\.idl(~?)",
            ".*\.s(~?)",
            ".*\.r((\.swp)?)(~?)",
            ".*\.cxx(~?)",
            ".*\.pyc(~?)",
            ".*\.asm(x?)(~?)",
            ".*\.py((\.swp)?)(~?)",
            ".*\.y((\.swp)?)(~?)",
            ".*\.gi((\.swp)?)(~?)",
            ".*\.t((\.swp)?)(~?)",
            ".*\.dll(~?)",
            ".*\.htemplate((\.swp)?)(~?)",
            ".*\.js((\.swp)?)(~?)",
            ".*\.rb((\.swp)?)(~?)",
            ".*\.ctemplate((\.swp)?)(~?)",
            ".*\.hg((\.swp)?)(~?)",
            ".*\.pm((\.swp)?)(~?)",
            ".*\.php((\.swp)?)(\d?)(~?)",
            ".*\.cc((\.swp)?)(~?)",
            ".*\.sh((\.swp)?)(~?)",
            ".*\.php((\.swp)?)(\d?)(~?)",
            ".*\.el((\.swp)?)(~?)",
            ".*\.hh((\.swp)?)(~?)",
            ".*\.h((pp)?)((\.swp)?)(~?)",
            ".*\.xs((\.swp)?)(~?)",
            ".*\.pl((\.swp)?)(~?)",
            ".*\.h\.tmpl((\.swp)?)(~?)",
            ".*\.mm((\.swp)?)(~?)",
            ".*\.idl((\.swp)?)(~?)",
            ".*\.h.win32((\.swp)?)(~?)",
            ".*\.xpt((\.swp)?)(~?)",
            ".*\.ccg((\.swp)?)(~?)",
            ".*\.ctmpl((\.swp)?)(~?)",
            ".*\.snk((\.swp)?)(~?)",
            ".*\.inc((\.swp)?)(~?)",
            ".*\.asp(x?)((\.swp)?)(~?)",
            ".*\.cpp((\.swp)?)(~?)",
            ".*\.gob((\.swp)?)(~?)",
            ".*\.vapi((\.swp)?)(~?)",
            ".*\.giv((\.swp)?)(~?)",
            ".*\.dtd((\.swp)?)(~?)",
            ".*\.gidl((\.swp)?)(~?)",
            ".*\.giv((\.swp)?)(~?)",
            ".*\.ada((\.swp)?)(~?)",
            ".*\.defs((\.swp)?)(~?)",
            ".*\.tcl((\.swp)?)(~?)",
            ".*\.vbs((\.swp)?)(~?)",
            ".*\.java((\.swp)?)(~?)",
            ".*\.nib((\.swp)?)(~?)",
            ".*\.sed((\.swp)?)(~?)",
            ".*\.vala((swp)?)(~?)",
        ]
        self.cat_devdoc = [
            ".*\.pdf",  # Milewicz et al. addition
            ".*citation.*",  # Milewicz et al. addition
            ".*license.*",  # Milewicz et al. addition
            ".*doxyfile.*",  # Milewicz et al. addition
            ".*\.wiki",  # Milewicz et al. addition
            ".*\.tex",  # Milewicz et al. addition
            ".*\.bib",  # Milewicz et al. addition
            ".*\.dox",  # Milewicz et al. addition
            ".*authors",  # Milewicz et al. addition
            ".*readme.*",
            ".*/changelog.*",
            ".*/todo.*",
            ".*\.dia(~?)",
            ".*\.ical",
            ".*/changes",
            ".*/status",
            ".*/fixme",
            ".*\.doxi",
            ".*/hacking.*",
            ".*/news.*",
            ".*/roadmap",
            ".*\.rst",
            ".*/devel(-?)doc(s?)/.*",
        ]
        self.cat_db = [
            ".*\.csv",  # Milewicz et al. addition
            ".*\.xml",  # Milewicz et al. addition
            ".*\.fa",  # Milewicz et al. addition
            ".*\.xlsx",  # Milewicz et al. addition
            ".*\.zip",  # Milewicz et al. addition
            ".*\.h5",  # Milewicz et al. addition
            ".*\.bz2",  # Milewicz et al. addition
            ".*\.tar(\.gz)?",  # Milewicz et al. addition
            ".*\.fq(\.gz)?",  # Milewicz et al. addition
            ".*\.pts",  # Milewicz et al. addition
            ".*\.pdb",  # Milewicz et al. addition
            ".*\.pqr",  # Milewicz et al. addition
            ".*\.vert",  # Milewicz et al. addition
            ".*\.node",  # Milewicz et al. addition
            ".*\.edge",  # Milewicz et al. addition
            ".*\.param(eters)?",  # Milewicz et al. addition
            ".*\.phi0",  # Milewicz et al. addition
            ".*\.prototext(\.bve)?",  # Milewicz et al. addition
            ".*\.pkl",  # Milewicz et al. addition
            ".*\.pbs",  # Milewicz et al. addition
            ".*\.sql",
            ".*\.sqlite",
            ".*\.mdb",
            ".*\.yaml",
            ".*\.sdb",
            ".*\.dat",
            ".*\.yaml",
            ".*\.json",
            ".*\.db",
            ".*/berkeleydb.*/.*",
        ]
        self.cat_build = [
            ".*\.build",  # Milewicz et al. addition
            ".*dockerfile",  # Milewicz et al. addition
            ".*\.gradle",  # Milewicz et al. addition
            ".*/install-sh",
            ".*/build/.*",
            ".*\.make",
            ".*makefile.*",
            ".*/pkg-info",
            ".*\.cmake",
            ".*\.ezt",
            ".*\.cbp",
            ".*\.pch",
            ".*\.wxilib",
            ".*\.m4(~?)",
            ".*\.prj",
            ".*\.plo",
            ".*\.mk",
            ".*\.deps",
            ".*\.wxiproj",
            ".*\.am(~?)",
            ".*\.mp4",
            ".*\.builder",
            ".*\.lo",
            ".*\.target",
            ".*\.iss",
            ".*\.nsi",
            ".*\.wxi",
            ".*/configure((\..+)?)",
            ".*\.wxs",
            ".*/mkbundle\..+",
            ".*\.in",
            ".*/autogen\.((.+\.)?)sh",
            ".*\.wpj",
            ".*\.vc(x?)proj(i?)n((\.filters((in)?))?)",
            ".*\.vcproj((\.filters((in)?))?)",
        ]
        self.cat_config = [
            ".*\.vcxproj((\.filters)?)( ̃?)",  # Milewicz et al. addition
            ".*\.qpg",  # Milewicz et al. addition
            ".*\.dsp",  # Milewicz et al. addition
            ".*\.epf",  # Milewicz et al. addition
            ".*\.config",
            ".*\.conf",
            ".*\.cfg",
            ".*\.anjuta",
            ".*\.dsw",
            ".*\.gnorba",
            ".*\.project",
            ".*\.pgp(~?)",
            ".*\.ini",
            ".*\.prefs",
            ".*\.vsprops",
            ".*\.gpg(~?)",
            ".*\.vmrc",
            ".*\.csproj",
            ".*\.gpg\.pub(~?)",
            ".*\.xml",
            ".*\.cproj",
            ".*\.cbproj",
            ".*\.pgp\.pub(~?)",
            ".*\.dsp",
            ".*\.emacs",
            ".*\.groupproj",
            ".*\.xcconfig",
            ".*\.plist",
            ".*\.pbxproj",
            ".*anjuta\.session",
            ".*\.*setting(s?).*/.*\.jp",
            ".*\.*config(s?).*/.*\.jp",
        ]
        self.cat_img = [
            ".*\.graffle",  # Milewicz et al. addition
            ".*\.eps",
            ".*\.jpg",
            ".*\.jpeg",
            ".*\.gif",
            ".*\.bmp",
            ".*\.ppm",
            ".*\.icns",
            ".*\.chm",
            ".*\.xbm",
            ".*\.pgm",
            ".*\.vdx",
            ".*\.sgv(z?)",
            ".*\.nsh",
            ".*\.ico",
            ".*\.xcf",
        ]
        self.cat_meta = [
            ".*\.svn(.*)",
            ".*\.git(.*)",
            ".*\.doap",
            ".*\.mdp",
            ".*\.cvs(.*)",
            ".*\.bzr(.*)",
            ".*\.mds",
            ".*\.vbg",
            ".*\.sln",
        ]
        self.cat_l10n = [
            ".*/.potfiles\.in(~?)",
            ".*/locale(s?)/.*",
            ".*\.linguas",
            ".*\.i18ns(~?)",
            ".*\.pot(~?)",
            "/po/.*",
            "/strings.properties",
            ".*\.mo(~?)",
            ".*\.wxl",
            ".*\.gmo(~?)",
            ".*\.resx(~?)",
            ".*\.po(~?)",
            ".*\.charset(~?)",
        ]
        self.cat_test = [
            ".*\.test(s?)/.*",
            ".*/.*test\..*",
            ".*/test.*\..*",
        ]
        self.cat_lib = [
            ".*/library/.*",
            ".*/libraries/.*",
        ]
        self.cat_media = [
            ".*\.mp3",
            ".*\.mp4",
            ".*\.ps",
            ".*\.avi",
            ".*\.ogg",
            ".*\.ogv",
            ".*/icon(s?)/.*",
            ".*\.shape",
            ".*\.wav",
            ".*\.au",
            ".*\.otf(~?)",
            ".*\.gnl",
            ".*\.mov",
            ".*\.avi",
            ".*\.sfd(~?)",
            " .*\.pgn",
            ".*\.mid",
            ".*\.xspf",
            ".*\.ttf(~?)",
            ".*\.cdf",
            ".*\.m4f",
            ".*\.ps",
            ".*\.afm",
            ".*\.bse",
            ".*\.pls",
            ".*\.omf",
            ".*\.pfb",
            ".*\.cur",
        ]
        self.cat_ui = [
            ".*\.glade(\d?)((\.bak)?)(~?)",
            ".*\.xul(~?)",
            ".*\.ui",
            ".*\.gladed(\d?)((\.bak)?)(~?)",
            ".*\.xpm",
            ".*\.gladep(\d?)((\.bak)?)(~?)",
            ".*\.theme",
            ".*\.desktop",
        ]

        self.cat_list_dict = {  # category acronyms, and their Activity Type (t):
            "doc": self.cat_doc,  # Documentation
            "img": self.cat_img,  # Images
            "l10n": self.cat_l10n,  # Localization
            "ui": self.cat_ui,  # User Interface
            "media": self.cat_media,  # Multimedia
            "code": self.cat_code,  # Coding
            "meta": self.cat_meta,  # Metadata
            "config": self.cat_config,  # Configuration
            "build": self.cat_build,  # Building
            "devdoc": self.cat_devdoc,  # Development Documentation
            "db": self.cat_db,  # Databases / Data
            "test": self.cat_test,  # Testing
            "lib": self.cat_lib,  # Library
            "unknown": self.cat_unknown,  # Unknown
        }

    def vasilescu_check_category(self, category: str, filestr: str) -> str:
        """
        This checks a given filename string `filestr` against a specified
        `category` or `any` to check against ALL categories.

        The rules are assessed in this order: doc, img, l10n, ui,
        media, code, meta, config, build, devdoc, db, test, lib, unknown.
        """

        assert (
            category in self.cat_list_dict.keys() or category == "any"
        ), f"WARNING! Your category must match one of the following: {self.cat_list_dict.keys()} OR 'any' to search ALL categories."
        assert isinstance(filestr, str)

        v_cat = "no_categorisation"
        search_cat = category

        if (
            search_cat == "any"
        ):  # run ALL the search categories in the order specified, using this function recursively.
            for cat in self.cat_list_dict.keys():
                check_rslt = self.vasilescu_check_category(
                    category=cat, filestr=filestr
                )
                if check_rslt != "no_categorisation":
                    v_cat = check_rslt
                    return v_cat
                    break  # break means we're returning the FIRST matching category.

        else:
            for filetype in self.cat_list_dict[search_cat]:
                if re.search(filetype, filestr, flags=re.IGNORECASE):
                    v_cat = search_cat
                    return v_cat
                    break
                else:
                    continue

        return v_cat

    def vasilescu_commit_files_classification(
        self, commit_changes_df: pd.DataFrame, commit_hash: str
    ) -> list[str]:
        """
        Function to classify commit based on filetypes according to method in Vasilescu et al. 2014,
        with additions by Milewicz, Pinto and Rodeghero 2019 (https://doi.org/10.1109/MSR.2019.00069)

        Method Uses file types of files changed per commit to assign to categories.
        For each filename, check type and assign to matching category, or "no_categorisation" if no matches.

        REQUIRES: files-changed info as pandas dataframe `commit_changes_df`. This is generated by
        get_commit_changes( ) when running: `commit_changes_df = commitchanges.get_commit_changes(commit_hash = commit)`
        """
        # if there are NO files, or filename is empty:
        # assert (
        #     len(commit_changes_df) >= 1
        # ), "WARNING! Dataframe of files changed is empty. Check if this should be the case."

        v_cat = []

        if commit_changes_df is None:
            v_cat = "no_categorisation [EMPTY]"

        elif len(commit_changes_df) == 1:  # only single file change to check
            filestr = commit_changes_df["filename"][0]
            v_cat = self.vasilescu_check_category(category="any", filestr=filestr)

        elif len(commit_changes_df) > 1:  # check multiple files from one commit hash
            files_results = []
            for file in commit_changes_df["filename"]:
                # this_filestr = file
                rslt = self.vasilescu_check_category(category="any", filestr=file)
                files_results.append(rslt)

            unique_categories = set(files_results)
            if len(unique_categories) == 1:
                v_cat = files_results[0]
                return v_cat, commit_changes_df["commit_hash"][0]
            else:
                # print("TIE-BREAKER REQUIRED")
                v_cat = sorted(
                    unique_categories,
                    key=lambda x: list(self.cat_list_dict.keys()).index(x),
                )[0]  # get lowest index'd category returned
                return v_cat, commit_hash

        return v_cat, commit_hash
