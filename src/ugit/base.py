import pathlib
from typing import Generator, NamedTuple

from ugit import data

IGNORED = {
    ".ugit",
    ".git",
    "__pycache__",
    ".venv",
    ".mypy_cache",
    ".DS_Store",
    ".python-version",
}


def write_tree(directory: pathlib.Path = pathlib.Path.cwd()) -> str:
    entries = []
    for item in directory.iterdir():
        if item.name in IGNORED:
            continue

        if item.is_file():
            with open(item, "rb") as f:
                oid = data.hash_object(f.read())
            entries.append(("blob", oid, item.name))

        elif item.is_dir():
            oid = write_tree(item)
            entries.append(("tree", oid, item.name))

    tree_content = "".join(
        f"{type_} {oid} {name}\n" for type_, oid, name in sorted(entries)
    )

    return data.hash_object(tree_content.encode(), "tree")


def _iter_tree_entries(tree_oid: str) -> Generator[tuple[str, str, str]]:
    tree = data.get_object(tree_oid, expected="tree")
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(" ", 2)
        yield type_, oid, name


def get_tree(
    oid: str, base_path: pathlib.Path = pathlib.Path.cwd()
) -> dict[pathlib.Path, str]:
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        path = base_path / name
        if type_ == "blob":
            result[path] = oid
        elif type_ == "tree":
            result.update(get_tree(oid, path))
    return result


def _empty_current_directory() -> None:
    for root, dirs, files in pathlib.Path.cwd().walk(top_down=False):
        for name in files:
            path = root / name
            if not is_ignored(path):
                path.unlink()
        for name in dirs:
            path = root / name
            # remove only if empty
            if not any(path.iterdir()) and not is_ignored(path):
                path.rmdir()


def read_tree(tree_oid: str) -> None:
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, pathlib.Path.cwd()).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.get_object(oid))


def commit(message: str) -> str:
    commit_content = f"tree {write_tree()}\n"

    HEAD = data.get_HEAD()
    if HEAD:
        commit_content += f"parent {HEAD}\n"

    commit_content += "\n"
    commit_content += f"{message}\n"

    oid = data.hash_object(commit_content.encode(), "commit")
    data.set_HEAD(oid)
    return oid


def checkout(oid):
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.set_HEAD(oid)


Commit = NamedTuple("Commit", [("tree", str), ("parent", str), ("message", str)])


def get_commit(oid):
    commit = data.get_object(oid, "commit").decode()
    lines = commit.splitlines()

    blank_line_idx = lines.index("")
    headers = lines[:blank_line_idx]
    message = "\n".join(lines[blank_line_idx + 1 :])

    header_dict = dict(line.split(" ", 1) for line in headers)

    return Commit(
        tree=header_dict.get("tree"), parent=header_dict.get("parent"), message=message
    )


def is_ignored(path: pathlib.Path) -> bool:
    return any(ignored_p in path.parts for ignored_p in IGNORED)
