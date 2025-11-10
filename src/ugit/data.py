import hashlib
import pathlib
from typing import Generator, NamedTuple

GIT_DIR = ".ugit"


def init() -> None:
    (pathlib.Path.cwd() / GIT_DIR / "objects").mkdir(exist_ok=True, parents=True)


def hash_object(data: bytes, type_dec: str = "blob") -> str:
    obj = type_dec.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    pathlib.Path(GIT_DIR, "objects", oid).write_bytes(obj)
    return oid


def get_object(oid: str, expected: str | None = "blob") -> bytes:
    obj = pathlib.Path(GIT_DIR, "objects", oid).read_bytes()
    type_enc, _, content = obj.partition(b"\x00")
    type_dec = type_enc.decode()

    if expected is not None:
        assert type_dec == expected, f"Expected {expected}, got {type_dec}"

    return content


RefValue = NamedTuple("RefValue", [("symbolic", bool), ("value", str | None)])


def update_ref(ref: str, value: RefValue) -> None:
    assert not value.symbolic
    path = pathlib.Path(GIT_DIR, ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    if value.value:
        path.write_text(value.value)


def get_ref(ref: str) -> RefValue:
    path = pathlib.Path(GIT_DIR, ref)
    value = None
    if path.is_file():
        value = path.read_text()
        if value.startswith("ref:"):
            return get_ref(value.split(":", 1)[1].strip())
    return RefValue(symbolic=False, value=value)


def iter_refs() -> Generator[tuple[str, RefValue]]:
    refs = ["HEAD"]
    for root, _, filenames in pathlib.Path(GIT_DIR, "refs").walk():
        refs.extend(f"{root.relative_to(GIT_DIR)}/{name}" for name in filenames)

    for refname in refs:
        yield refname, get_ref(refname)
