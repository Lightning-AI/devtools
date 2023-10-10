import os
import subprocess
import sys

from scripts import _PATH_SCRIPTS

REQUIREMENTS_SAMPLE = """
# This is sample requirements file
#  with multi line comments

torchvision >=0.13.0, <0.16.0  # sample # comment
gym[classic_control] >=0.17.0, <0.27.0
ipython[all] <8.15.0  # strict
torchmetrics >=0.10.0, <1.3.0
lightning-utilities >=0.8.0, <0.10.0

"""
REQUIREMENTS_EXPECTED = """
# This is sample requirements file
#  with multi line comments

torchvision==0.11.1  # sample # comment
gym[classic_control] >=0.17.0, <0.27.0
ipython[all] <8.15.0  # strict
torchmetrics >=0.10.0, <1.3.0
lightning-utilities >=0.8.0, <0.10.0

"""


def test_adjust_torch_versions_call(tmp_path) -> None:
    path_script = os.path.join(_PATH_SCRIPTS, "adjust-torch-versions.py")
    path_req_file = tmp_path / "requirements.txt"
    with open(path_req_file, "w", encoding="utf8") as fopen:
        fopen.write(REQUIREMENTS_SAMPLE)

    return_code = subprocess.call([sys.executable, path_script, path_req_file, "1.10.0"])  # noqa: S603
    assert return_code == 0
    with open(path_req_file, encoding="utf8") as fopen:
        req_result = fopen.read()
    assert req_result == REQUIREMENTS_EXPECTED
