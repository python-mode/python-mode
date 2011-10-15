from rope.base import exceptions


def resources(project, rules):
    """Find python files in the `project` matching `rules`

    `rules` is a multi-line `str`; each line starts with either a '+'
    or '-'.  Each '+' means include the file (or its children if it's
    a folder) that comes after it.  '-' has the same meaning for
    exclusion.

    """
    all = set(project.pycore.get_python_files())
    files = None
    for line in rules.splitlines():
        if not line.strip():
            continue
        first, path = (line[0], line[1:])
        if first not in '+-':
            continue
        try:
            resource = project.get_resource(path.strip())
        except exceptions.ResourceNotFoundError:
            continue
        if resource.is_folder():
            matches = set(filter(lambda item: resource.contains(item), all))
        else:
            matches = set([resource])
        if first == '+':
            if files is None:
                files = set()
            files.update(matches)
        if first == '-':
            if files is None:
                files = set(all)
            files -= matches
    if files is None:
        return all
    return files
