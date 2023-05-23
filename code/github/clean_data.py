import sys

#import bits

import repo_name_clean as name_clean


# other stuff

# loop over github urls to do cleaning  

def main():
    repo_name = sys.argv[1] # TODO: remove this once debugged and running at commandline
    name_clean.repo_name_clean(repo_name)

# this bit
if __name__ == "__main__":
    main()

