import hashlib
import pathlib

GIT_DIR = ".ugit"


def init() -> None:
    pathlib.Path(f"{pathlib.Path.cwd()}/{GIT_DIR}/objects").mkdir(
        exist_ok=True, parents=True
    )


def hash_object(data: bytes, type_dec: str = "blob") -> str:
    obj = type_dec.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    pathlib.Path(f"{GIT_DIR}/objects/{oid}").write_bytes(obj)
    return oid


def get_object(oid: str, expected: str = "blob") -> bytes:
    obj = pathlib.Path(f"{GIT_DIR}/objects/{oid}").read_bytes()
    type_enc, _, content = obj.partition(b"\x00")
    type_dec = type_enc.decode()

    if expected is not None:
        assert type_dec == expected, f"Expected {expected}, got {type_dec}"

    return content


def set_HEAD(oid: str) -> None:
    with open(f"{GIT_DIR}/HEAD", "w") as f:
        f.write(oid)


def get_HEAD() -> str | None:
    path = pathlib.Path(f"{GIT_DIR}/HEAD")
    if path.is_file():
        return path.read_text()
    return None
