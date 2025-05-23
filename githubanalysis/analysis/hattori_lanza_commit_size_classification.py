"""Hattori Lanza commit size classification method implementation pre-obtained on GH API commit data from Research Software repositories."""

# Hattori-Lanza commit classification method referenced from research paper:
# L. P. Hattori and M. Lanza, ‘On the nature of commits’,
# in 2008 23rd IEEE/ACM International Conference on Automated Software Engineering - Workshops, Sep. 2008, pp. 63–71.
# doi: 10.1109/ASEW.2008.4686322.


def hattori_lanza_commit_size_classification(commit_size: int | None) -> str | None:
    """
    Implementing Hattori-Lanza commit size classification method by number of files changed per commit.
    Classification returns category based on bins: (tiny: 1-5 files changed; small=6-25; medium=26-125; large=126+ files changed).

    From Hattori and Lanza (2008): "The approach we propose is to divide the commits into four groups by using an exponential scale.
    Although the exponential scaling parameter for power law distributions typically lies in the range 2 < α < 3,
    we choose 5 as exponential scaling parameter. Otherwise the last group would range from 16 or 81 up, which would
    still be a small number compared to some commits with hundreds of files in it"
    doi: 10.1109/ASEW.2008.4686322.

    :param commit_size:  Number of unique files changed per single commit hash 'change'. Includes deletions/additions.
    :type commit_size: int

    :return commit_cat: classification category name from: "tiny", "small", "medium", "large" or None.
    :rtype: str

    """

    if commit_size is None or commit_size == 0:
        return None

    if not isinstance(commit_size, int):
        raise RuntimeError("Must be integer type or None")

    assert commit_size >= 0, "Warning! Cannot process negative numbers: {commit_size}"

    if 1 <= commit_size <= 5:  # tiny:1-5
        return "tiny"
    elif 6 <= commit_size <= 25:
        return "small"
    elif 26 <= commit_size <= 125:
        return "medium"
    elif commit_size > 125:
        return "large"
    else:
        return None
