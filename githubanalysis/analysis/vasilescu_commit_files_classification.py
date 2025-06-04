"""Application of Vasilescu et al. 2014 method of classifying commits by filetypes of files changed, using pre-obtained github commit data for Research Software repositories"""

import logging
import pandas as pd
import re
from githubanalysis.setup_classes import LocationSetup


class Vasilescu_Commit_Classifier(LocationSetup):
    def _log_name(self) -> str:
        return "vasilescu_commit_files_classification"

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: None | logging.Logger = None,
    ) -> None:
        super().__init__(in_notebook=in_notebook, logger=logger)
        self.config_path = config_path
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
            r".*\.md",  # Milewicz et al. addition
            r".*\.((s|x|g|p|(gt))?)htm(l?)",
            r".*/translators",
            r".*/contributors",
            r".*/doc(-?)book(s?)/.*",
            r".*\.page",
            r".*/info",
            r".*\.l",
            r".*\.zabw",
            r".*/potfiles",
            r".*/install",
            r".*\.wml",
            r".*\.chm",
            r".*\.ods",
            r".*/copyright",
            r".*/version",
            r".*\.css",
            r".*\.vcard(~?)",
            r".*/plan",
            r".*/feature(s?)",
            r".*\.txt((\.bak)?)",
            r".*/credits",
            r".*/notes",
            r".*/licence",
            r".*\.txt((\.old)?)",
            r".*\.man",
            r".*/howto",
            r".*/license",
            r".*\.rtf",
            r".*\.ics",
            r".*/faq",
            r".*/maintainers",
            r".*\.tex",
            r".*/documenters",
            r".*copying",
            r".*/copying",
            r".*\.sgml",
            r".*\.gnumeric",
            r".*/copying.*",
            r".*/committers",
            r".*\.eps",
            r".*\.vcf",
            r".*/doc(s?)/.*",
            r".*/thanks",
            r".*\.xsd",
            r".*\.schemas",
            r".*/help(s?)/.*",
            r".*/authors",
            r".*\.texi",
            r".*\.doc",
            r".*/bugs",
            r".*\.docx",
        ]
        self.cat_code = [
            r".*\.pas((\.swp)?)( ̃?)",  # Milewicz et al. addition
            r".*\.pxd((\.swp)?)( ̃?)",  # Milewicz et al. addition
            r".*\.ads((\.swp)?)( ̃?)",  # Milewicz et al. addition
            r".*\.adb((\.swp)?)( ̃?)",  # Milewicz et al. addition
            r".*\.bin",  # Milewicz et al. addition
            r".*/src/.*",
            r".*\.exe(~?)",
            r".*\.dmg(~?)",
            r".*\.swg(~?)",
            r".*\.so(~?)",
            r".*\.i(~?)",
            r".*\.o(~?)",
            r".*\.exe(~?)",
            r".*\.oafinfo(~?)",
            r".*\.pyd(~?)",
            r".*\.c((\.swp)?)(~?)",
            r".*\.py((\.swp)?)(~?)",
            r".*\.r((\.swp)?)(~?)",
            r".*\.java((\.swp)?)(~?)",
            r".*\.awk(~?)",
            r".*\.scm(~?)",
            r".*\.glsl(~?)",
            r".*\.patch(~?)",
            r".*\.c((\.swp)?)(~?)",
            r".*/script(s?)/.*",
            r".*\.jar(~?)",
            r".*/src/.*",
            r".*\.m((\.swp)?)(~?)",
            r".*\.cs(~?)",
            r".*\.idl(~?)",
            r".*\.s(~?)",
            r".*\.r((\.swp)?)(~?)",
            r".*\.cxx(~?)",
            r".*\.pyc(~?)",
            r".*\.asm(x?)(~?)",
            r".*\.py((\.swp)?)(~?)",
            r".*\.y((\.swp)?)(~?)",
            r".*\.gi((\.swp)?)(~?)",
            r".*\.t((\.swp)?)(~?)",
            r".*\.dll(~?)",
            r".*\.htemplate((\.swp)?)(~?)",
            r".*\.js((\.swp)?)(~?)",
            r".*\.rb((\.swp)?)(~?)",
            r".*\.ctemplate((\.swp)?)(~?)",
            r".*\.hg((\.swp)?)(~?)",
            r".*\.pm((\.swp)?)(~?)",
            r".*\.php((\.swp)?)(\d?)(~?)",
            r".*\.cc((\.swp)?)(~?)",
            r".*\.sh((\.swp)?)(~?)",
            r".*\.php((\.swp)?)(\d?)(~?)",
            r".*\.el((\.swp)?)(~?)",
            r".*\.hh((\.swp)?)(~?)",
            r".*\.h((pp)?)((\.swp)?)(~?)",
            r".*\.xs((\.swp)?)(~?)",
            r".*\.pl((\.swp)?)(~?)",
            r".*\.h\.tmpl((\.swp)?)(~?)",
            r".*\.mm((\.swp)?)(~?)",
            r".*\.idl((\.swp)?)(~?)",
            r".*\.h.win32((\.swp)?)(~?)",
            r".*\.xpt((\.swp)?)(~?)",
            r".*\.ccg((\.swp)?)(~?)",
            r".*\.ctmpl((\.swp)?)(~?)",
            r".*\.snk((\.swp)?)(~?)",
            r".*\.inc((\.swp)?)(~?)",
            r".*\.asp(x?)((\.swp)?)(~?)",
            r".*\.cpp((\.swp)?)(~?)",
            r".*\.gob((\.swp)?)(~?)",
            r".*\.vapi((\.swp)?)(~?)",
            r".*\.giv((\.swp)?)(~?)",
            r".*\.dtd((\.swp)?)(~?)",
            r".*\.gidl((\.swp)?)(~?)",
            r".*\.giv((\.swp)?)(~?)",
            r".*\.ada((\.swp)?)(~?)",
            r".*\.defs((\.swp)?)(~?)",
            r".*\.tcl((\.swp)?)(~?)",
            r".*\.vbs((\.swp)?)(~?)",
            r".*\.java((\.swp)?)(~?)",
            r".*\.nib((\.swp)?)(~?)",
            r".*\.sed((\.swp)?)(~?)",
            r".*\.vala((swp)?)(~?)",
        ]
        self.cat_devdoc = [
            r".*\.pdf",  # Milewicz et al. addition
            r".*citation.*",  # Milewicz et al. addition
            r".*license.*",  # Milewicz et al. addition
            r".*doxyfile.*",  # Milewicz et al. addition
            r".*\.wiki",  # Milewicz et al. addition
            r".*\.tex",  # Milewicz et al. addition
            r".*\.bib",  # Milewicz et al. addition
            r".*\.dox",  # Milewicz et al. addition
            r".*authors",  # Milewicz et al. addition
            r".*readme.*",
            r".*/changelog.*",
            r".*/todo.*",
            r".*\.dia(~?)",
            r".*\.ical",
            r".*/changes",
            r".*/status",
            r".*/fixme",
            r".*\.doxi",
            r".*/hacking.*",
            r".*/news.*",
            r".*/roadmap",
            r".*\.rst",
            r".*/devel(-?)doc(s?)/.*",
        ]
        self.cat_db = [
            r".*\.csv",  # Milewicz et al. addition
            r".*\.xml",  # Milewicz et al. addition
            r".*\.fa",  # Milewicz et al. addition
            r".*\.xlsx",  # Milewicz et al. addition
            r".*\.zip",  # Milewicz et al. addition
            r".*\.h5",  # Milewicz et al. addition
            r".*\.bz2",  # Milewicz et al. addition
            r".*\.tar(\.gz)?",  # Milewicz et al. addition
            r".*\.fq(\.gz)?",  # Milewicz et al. addition
            r".*\.pts",  # Milewicz et al. addition
            r".*\.pdb",  # Milewicz et al. addition
            r".*\.pqr",  # Milewicz et al. addition
            r".*\.vert",  # Milewicz et al. addition
            r".*\.node",  # Milewicz et al. addition
            r".*\.edge",  # Milewicz et al. addition
            r".*\.param(eters)?",  # Milewicz et al. addition
            r".*\.phi0",  # Milewicz et al. addition
            r".*\.prototext(\.bve)?",  # Milewicz et al. addition
            r".*\.pkl",  # Milewicz et al. addition
            r".*\.pbs",  # Milewicz et al. addition
            r".*\.sql",
            r".*\.sqlite",
            r".*\.mdb",
            r".*\.yaml",
            r".*\.sdb",
            r".*\.dat",
            r".*\.yaml",
            r".*\.json",
            r".*\.db",
            r".*/berkeleydb.*/.*",
        ]
        self.cat_build = [
            r".*\.build",  # Milewicz et al. addition
            r".*dockerfile",  # Milewicz et al. addition
            r".*\.gradle",  # Milewicz et al. addition
            r".*/install-sh",
            r".*/build/.*",
            r".*\.make",
            r".*makefile.*",
            r".*/pkg-info",
            r".*\.cmake",
            r".*\.ezt",
            r".*\.cbp",
            r".*\.pch",
            r".*\.wxilib",
            r".*\.m4(~?)",
            r".*\.prj",
            r".*\.plo",
            r".*\.mk",
            r".*\.deps",
            r".*\.wxiproj",
            r".*\.am(~?)",
            r".*\.mp4",
            r".*\.builder",
            r".*\.lo",
            r".*\.target",
            r".*\.iss",
            r".*\.nsi",
            r".*\.wxi",
            r".*/configure((\..+)?)",
            r".*\.wxs",
            r".*/mkbundle\..+",
            r".*\.in",
            r".*/autogen\.((.+\.)?)sh",
            r".*\.wpj",
            r".*\.vc(x?)proj(i?)n((\.filters((in)?))?)",
            r".*\.vcproj((\.filters((in)?))?)",
        ]
        self.cat_config = [
            r".*\.vcxproj((\.filters)?)( ̃?)",  # Milewicz et al. addition
            r".*\.qpg",  # Milewicz et al. addition
            r".*\.dsp",  # Milewicz et al. addition
            r".*\.epf",  # Milewicz et al. addition
            r".*\.config",
            r".*\.conf",
            r".*\.cfg",
            r".*\.anjuta",
            r".*\.dsw",
            r".*\.gnorba",
            r".*\.project",
            r".*\.pgp(~?)",
            r".*\.ini",
            r".*\.prefs",
            r".*\.vsprops",
            r".*\.gpg(~?)",
            r".*\.vmrc",
            r".*\.csproj",
            r".*\.gpg\.pub(~?)",
            r".*\.xml",
            r".*\.cproj",
            r".*\.cbproj",
            r".*\.pgp\.pub(~?)",
            r".*\.dsp",
            r".*\.emacs",
            r".*\.groupproj",
            r".*\.xcconfig",
            r".*\.plist",
            r".*\.pbxproj",
            r".*anjuta\.session",
            r".*\.*setting(s?).*/.*\.jp",
            r".*\.*config(s?).*/.*\.jp",
        ]
        self.cat_img = [
            r".*\.graffle",  # Milewicz et al. addition
            r".*\.eps",
            r".*\.jpg",
            r".*\.jpeg",
            r".*\.gif",
            r".*\.bmp",
            r".*\.ppm",
            r".*\.icns",
            r".*\.chm",
            r".*\.xbm",
            r".*\.pgm",
            r".*\.vdx",
            r".*\.sgv(z?)",
            r".*\.nsh",
            r".*\.ico",
            r".*\.xcf",
        ]
        self.cat_meta = [
            r".*\.svn(.*)",
            r".*\.git(.*)",
            r".*\.doap",
            r".*\.mdp",
            r".*\.cvs(.*)",
            r".*\.bzr(.*)",
            r".*\.mds",
            r".*\.vbg",
            r".*\.sln",
        ]
        self.cat_l10n = [
            r".*/.potfiles\.in(~?)",
            r".*/locale(s?)/.*",
            r".*\.linguas",
            r".*\.i18ns(~?)",
            r".*\.pot(~?)",
            r"/po/.*",
            r"/strings.properties",
            r".*\.mo(~?)",
            r".*\.wxl",
            r".*\.gmo(~?)",
            r".*\.resx(~?)",
            r".*\.po(~?)",
            r".*\.charset(~?)",
        ]
        self.cat_test = [
            r".*\.test(s?)/.*",
            r".*/.*test\..*",
            r".*/test.*\..*",
        ]
        self.cat_lib = [
            r".*/library/.*",
            r".*/libraries/.*",
        ]
        self.cat_media = [
            r".*\.mp3",
            r".*\.mp4",
            r".*\.ps",
            r".*\.avi",
            r".*\.ogg",
            r".*\.ogv",
            r".*/icon(s?)/.*",
            r".*\.shape",
            r".*\.wav",
            r".*\.au",
            r".*\.otf(~?)",
            r".*\.gnl",
            r".*\.mov",
            r".*\.avi",
            r".*\.sfd(~?)",
            r" .*\.pgn",
            r".*\.mid",
            r".*\.xspf",
            r".*\.ttf(~?)",
            r".*\.cdf",
            r".*\.m4f",
            r".*\.ps",
            r".*\.afm",
            r".*\.bse",
            r".*\.pls",
            r".*\.omf",
            r".*\.pfb",
            r".*\.cur",
        ]
        self.cat_ui = [
            r".*\.glade(\d?)((\.bak)?)(~?)",
            r".*\.xul(~?)",
            r".*\.ui",
            r".*\.gladed(\d?)((\.bak)?)(~?)",
            r".*\.xpm",
            r".*\.gladep(\d?)((\.bak)?)(~?)",
            r".*\.theme",
            r".*\.desktop",
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
        self, commit_changes_df: pd.DataFrame | None, commit_hash: str
    ) -> tuple[str, str]:
        """
        Function to classify commit based on filetypes according to method in Vasilescu et al. 2014,
        with additions by Milewicz, Pinto and Rodeghero 2019 (https://doi.org/10.1109/MSR.2019.00069)

        Method Uses file types of files changed per commit to assign to categories.
        For each filename, check type and assign to matching category, or "no_categorisation" if no matches.

        REQUIRES: files-changed info as pandas dataframe `commit_changes_df`. This is generated by
        get_commit_changes( ) when running: `commit_changes_df = commitchanges.get_commit_changes(commit_hash = commit)`
        """
        assert isinstance(
            commit_hash, str
        ), "commit hash is not string type, check this."

        if commit_changes_df is None or len(commit_changes_df) == 0:
            v_cat = "no_categorisation [EMPTY]"
            return v_cat, commit_hash

        elif len(commit_changes_df) == 1:  # only single file change to check
            filestr = commit_changes_df["filename"][0]
            v_cat = self.vasilescu_check_category(category="any", filestr=filestr)
            assert (
                v_cat is not None
            ), "v_cat is None: check this and improve handling of code"
            return v_cat, commit_hash

        elif len(commit_changes_df) > 1:  # check multiple files from one commit hash
            files_results = []
            for file in commit_changes_df["filename"]:
                # this_filestr = file
                rslt = self.vasilescu_check_category(category="any", filestr=file)
                files_results.append(rslt)

            unique_categories = set(files_results)
            if len(unique_categories) == 1:
                v_cat = files_results[0]
                assert (
                    v_cat is not None
                ), "v_cat is None: check this and improve handling of code"
                return v_cat, commit_hash
            else:
                # print("TIE-BREAKER REQUIRED")
                v_cat = sorted(
                    unique_categories,
                    key=lambda x: list(self.cat_list_dict.keys()).index(x),
                )[0]  # get lowest index'd category returned
                assert (
                    v_cat is not None
                ), "v_cat is None: check this and improve handling of code"
                return v_cat, commit_hash
        else:
            raise RuntimeError(
                f"Unreachable: {commit_changes_df = }, {commit_hash = }."
            )
