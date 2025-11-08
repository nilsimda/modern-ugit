import hashlib
import pathlib

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


def update_ref(ref: str, oid: str) -> None:
    path = pathlib.Path(GIT_DIR, ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(oid)


def get_ref(ref: str) -> str | None:
    path = pathlib.Path(GIT_DIR, ref)
    if path.is_file():
        return path.read_text()
    return None
