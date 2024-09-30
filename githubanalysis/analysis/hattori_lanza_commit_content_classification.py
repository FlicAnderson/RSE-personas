"""Hattori Lanza commit content classification method implementation on GH API commit data from Research Software repositories."""

import re
import logging

import utilities.get_default_logger as loggit


# Hattori-Lanza commit classification method referenced from research paper:
# L. P. Hattori and M. Lanza, ‘On the nature of commits’,
# in 2008 23rd IEEE/ACM International Conference on Automated Software Engineering - Workshops, Sep. 2008, pp. 63–71.
# doi: 10.1109/ASEW.2008.4686322.


class Hattori_Lanza_Content_Classification:
    logger: logging.Logger

    def __init__(
        self,
        logger: logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/hattori_lanza_commit_content_classification_logs.txt",
            )
        else:
            self.logger = logger

        self.hattori_lanza_categories = [
            "forward_engineering",  # "activities related to incorporation of new features and implementation of new requirements"
            "reengineering",  # "activities related to refactoring, redesign and other actions to enhance the quality of the code without properly adding new features"
            "corrective_engineering",  # "handles defects, errors and bug[s] in the software"
            "management",  # "activities are those unrelated to codification, such as formatting code, cleaning up, and updating documentation"
            "empty_message",  # "there is theoretically a fifth category of commit comments, the empty ones, which of course cannot be classified using our approach"
            "no_categorisation",  # added by @FlicAnderson to represent commits not categorised by this method
        ]

        self.hattori_lanza_categories_hierarchy = {
            "Development": ["forward_engineering"],
            "Maintenance": ["reengineering", "corrective_engineering", "management"],
            "Empty": ["empty_message"],
            "NotCategorised": ["no_categorisation"],
        }

        self.fwd_eng = [  # Development: Forward Engineering
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

        self.re_eng = [  # Maintenance: Re-engineering
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

        self.cor_eng = [  # Maintenance: Corrective Engineering
            "bug",
            "fix",
            "issue",
            "error",
            "proper",
            "deprecat",
            "broke",
        ]

        self.mgmt = [  # Maintenance: Management
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
        ]

    def hattori_lanza_commit_content_classification(self, commit_message: str) -> str:
        """
        Implementing method of Hattori-Lanza commit message content classification.

        Searches commit message for matching keywords from categories in
        the following category order: 1) empty messages, 2) management,
        3) reengineering, 4) corrective engineering, 5) forward engineering.
        Return  the 'first' category match in that order, or, if NO matches:
        then return "no_categorisation".
        doi: 10.1109/ASEW.2008.4686322.

        :param commit_message: text in string format to compare for keyword matches
        :type: str
        :return: str word indicating which category has been matched to the commit, or none.
        :rtype: str
        """

        if commit_message is None or commit_message == "":
            self.logging.info("commit message matches None or empty string.")
            return "empty_message"

        else:
            for keyword in self.mgmt:
                match_result = re.search(keyword, commit_message, flags=re.IGNORECASE)
                if match_result is not None:
                    self.logging.info(
                        f"match for {keyword} in management: {match_result}."
                    )
                    return "management"
                    break
                else:
                    continue

            for keyword in self.re_eng:
                match_result = re.search(keyword, commit_message, flags=re.IGNORECASE)
                if match_result is not None:
                    self.logging.info(
                        f"match for {keyword} in reengineering: {match_result}."
                    )
                    return "reengineering"
                    break
                else:
                    continue

            for keyword in self.cor_eng:
                match_result = re.search(keyword, commit_message, flags=re.IGNORECASE)
                if match_result is not None:
                    self.logging.info(
                        f"match for {keyword} in corrective engineering: {match_result}."
                    )
                    return "corrective_engineering"
                    break
                else:
                    continue

            for keyword in self.fwd_eng:
                match_result = re.search(keyword, commit_message, flags=re.IGNORECASE)
                if match_result is not None:
                    self.logging.info(
                        f"match for {keyword} in fwdforward engineering: {match_result}."
                    )
                    return "forward_engineering"
                    break

                else:
                    continue
            self.logging.info("No match, uncategorised commit")
            return "no_categorisation"
