def simple_read_repos_from_file(filename) -> list[str]:
    with open(filename, "r") as f:
        repos = [txtline.strip() for txtline in f.readlines()]
        return repos
