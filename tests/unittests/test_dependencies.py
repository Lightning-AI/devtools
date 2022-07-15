from pathlib import Path

from pl_devtools.dependencies import replace_oldest_ver, prune_pkgs_in_requirements

_PATH_ROOT = Path(__file__).parent.parent.parent


def test_prune_packages(tmpdir):
    req_file = tmpdir / "requirements.txt"
    with open(req_file, "w") as fp:
        fp.writelines(["fire\n", "abc>=0.1\n"])
    prune_pkgs_in_requirements("abc", req_files=[str(req_file)])
    with open(req_file) as fp:
        lines = fp.readlines()
    assert lines == ["fire\n"]


def test_oldest_packages(tmpdir):
    req_file = tmpdir / "requirements.txt"
    with open(req_file, "w") as fp:
        fp.writelines(["fire>0.2\n", "abc>=0.1\n"])
    replace_oldest_ver(req_files=[str(req_file)])
    with open(req_file) as fp:
        lines = fp.readlines()
    assert lines == ["fire>0.2\n", "abc==0.1\n"]
