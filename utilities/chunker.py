"""Function which splits things into chunks."""

def chunker(seq, size=10):
    """
    :param seq: the thing to split (iterable thing)
    :type: str
    :param size: size of block to chunk seq into/
    :type: int
    :returns: 'chunk'
    :type: ???
    
    """
    for pos in range(0, len(seq), size):
        yield seq.iloc[pos:pos + size] 
# via Andrei Krivoshei at SO: https://stackoverflow.com/a/61798585  
        

# this bit
if __name__ == "__main__":
    try: 
        chunker(seq, size)
    except Exception as e:
        print(f"Exception issue with chunker(): {e}")
