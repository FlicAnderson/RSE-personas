"""Function which splits things into chunks."""


def chunker(iterable, size=10):
    """
    :param iterable: the thing to split (iterable thing)
    :type: str or int
    :param size: size of block to chunk seq into/
    :type: int
    :returns: 'chunk'
    :type: ???

    """
    for pos in range(0, len(iterable), size):
        yield iterable.iloc[pos : pos + size]


# via Andrei Krivoshei at SO: https://stackoverflow.com/a/61798585


# this bit
if __name__ == "__main__":
    try:
        chunker(iterable, size=10)
    except Exception as e:
        print(f"Exception issue with chunker(): {e}")
