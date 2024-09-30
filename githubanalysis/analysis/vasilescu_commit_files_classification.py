"""Application of Vasilescu et al. 2014 method of classifying commits by filetypes of files changed, using pre-obtained github commit data for Research Software repositories"""

import logging
import datetime

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
            "unknown",  # Unknown
            "code",  # Coding
            "devdoc",  # Development Documentation
            "doc",  # Documentation
            "img",  # Images
            "l10n",  # Localization
            "media",  # Multimedia
            "ui",  # User Interface
            "meta",  # Meta
            "build",  # Building
            "test",  # Testing
            "lib",  # Library
            "db",  # Database
            "config",  # Configuration
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
            ".*\.c((\.swp)?)(~?)",
            ".*\.py((\.swp)?)(~?)",
            ".*\.r((\.swp)?)(~?)",
            ".*\.java((\.swp)?)(~?)",
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
        ]
        self.cat_config = [
            ".*\.vcxproj((\.filters)?)( ̃?)",  # Milewicz et al. addition
            ".*\.qpg",  # Milewicz et al. addition
            ".*\.dsp",  # Milewicz et al. addition
            ".*\.epf",  # Milewicz et al. addition
            ".*\.config",
            ".*\.conf",
            ".*\.cfg",
        ]
        self.cat_img = [
            ".*\.graffle",  # Milewicz et al. addition
            ".*\.eps",
            ".*\.jpg",
            ".*\.jpeg",
            ".*\.gif",
            ".*\.bmp",
        ]
        self.cat_meta = [
            ".*\.svn(.*)",
            ".*\.git(.*)",
        ]
        self.cat_l10n = [
            ".*/.potfiles\.in(~?)",
            ".*/locale(s?)/.*",
            ".*\.linguas",
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
        ]
        self.cat_ui = [
            ".*\.ui",
            ".*\.theme",
            ".*\.desktop",
        ]

    def vasilescu_commit_files_classification(self, commit_changes_df):
        """
        Function to classify commit based on filetypes according to method in Vasilescu et al. 2014,
        with additions by Milewicz, Pinto and Rodeghero 2019 (https://doi.org/10.1109/MSR.2019.00069)

        Uses file types of files changed per commit to assign to categories.
        """

        # get files changed info as pandas dataframe `commit_changes_df` generated by get_commit_changes( ) when running: `commit_changes_df = commitchanges.get_commit_changes(commit_hash = commit)`

        # if there are NO files, or filename is empty:
        v_cat = None

        # for each filename, check type and assign to matching category, or "no_categorisation" if no matches.

        # for filename in commit_changes_df['filename']:
        # check v_cat 1

        return v_cat
