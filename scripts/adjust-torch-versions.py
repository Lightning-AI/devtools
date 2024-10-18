# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
"""Adjusting version across PTorch ecosystem."""

import logging
import os
import re
import sys
from typing import Dict, List, Optional


def _determine_torchaudio(torch_version : str) -> str:
    """Determine the torchaudio version based on the torch version.

    >>> _determine_torchaudio("1.9.0")
    '0.9.0'
    >>> _determine_torchaudio("2.4.1")
    '2.4.1'
    >>> _determine_torchaudio("1.8.2")
    '0.9.1'
    """
    _VERSION_EXCEPTIONS = {
        "1.8.2": "0.9.1",
    }
    # drop all except semantic version
    torch_ver = re.search(r"([\.\d]+)", torch_version).groups()[0]
    if torch_ver in _VERSION_EXCEPTIONS:
        return _VERSION_EXCEPTIONS[torch_ver]
    ver_major, ver_minor, ver_bugfix= map(int, torch_ver.split("."))
    ta_ver_array = [ver_major, ver_minor, ver_bugfix]
    if ver_major == 1:
        ta_ver_array[0] = 0
    ta_ver_array[2] = ver_bugfix
    return ".".join(map(str, ta_ver_array))


def _determine_torchtext(torch_version : str) -> str:
    """Determine the torchtext version based on the torch version.

    >>> _determine_torchtext("1.9.0")
    '0.10.0'
    >>> _determine_torchtext("2.4.1")
    '0.18.0'
    >>> _determine_torchtext("1.8.2")
    '0.9.1'
    """
    _VERSION_EXCEPTIONS = {
        "2.0.1": "0.15.2",
        "2.0.0": "0.15.1",
        "1.8.2": "0.9.1",
    }
    # drop all except semantic version
    torch_ver = re.search(r"([\.\d]+)", torch_version).groups()[0]
    if torch_ver in _VERSION_EXCEPTIONS:
        return _VERSION_EXCEPTIONS[torch_ver]
    ver_major, ver_minor, ver_bugfix= map(int, torch_ver.split("."))
    tt_ver_array = [0, 0, 0]
    if ver_major == 1:
        tt_ver_array[1] = ver_minor + 1
        tt_ver_array[2] = ver_bugfix
    elif ver_major == 2:
        if ver_minor >= 3:
            tt_ver_array[1] = 18
        else:
            tt_ver_array[1] = ver_minor + 15
            tt_ver_array[2] = ver_bugfix
    else:
        raise ValueError(f"Invalid torch version: {torch_version}")
    return ".".join(map(str, tt_ver_array))


def _determine_torchvision(torch_version : str) -> str:
    """Determine the torchvision version based on the torch version.

    >>> _determine_torchvision("1.9.0")
    '0.10.0'
    >>> _determine_torchvision("2.4.1")
    '0.19.1'
    >>> _determine_torchvision("2.0.1")
    '0.15.2'
    """
    _VERSION_EXCEPTIONS = {
        "2.0.1": "0.15.2",
        "2.0.0": "0.15.1",
        "1.10.2": "0.11.3",
        "1.10.1": "0.11.2",
        "1.10.0": "0.11.1",
        "1.8.2": "0.9.1",
    }
    # drop all except semantic version
    torch_ver = re.search(r"([\.\d]+)", torch_version).groups()[0]
    if torch_ver in _VERSION_EXCEPTIONS:
        return _VERSION_EXCEPTIONS[torch_ver]
    ver_major, ver_minor, ver_bugfix= map(int, torch_ver.split("."))
    tv_ver_array = [0, 0, 0]
    if ver_major == 1:
        tv_ver_array[1] = ver_minor + 1
    elif ver_major == 2:
        tv_ver_array[1] = ver_minor + 15
    else:
        raise ValueError(f"Invalid torch version: {torch_version}")
    tv_ver_array[2] = ver_bugfix
    return ".".join(map(str, tv_ver_array))


def find_latest(ver: str) -> Dict[str, str]:
    """Find the latest version.

    >>> from pprint import pprint
    >>> pprint(find_latest("2.1.0"))
    {'torch': '2.1.0',
     'torchaudio': '2.1.0',
     'torchtext': '0.16.0',
     'torchvision': '0.16.0'}
    """
    # drop all except semantic version
    ver = re.search(r"([\.\d]+)", ver).groups()[0]
    # in case there remaining dot at the end - e.g "1.9.0.dev20210504"
    ver = ver[:-1] if ver[-1] == "." else ver
    logging.debug(f"finding ecosystem versions for: {ver}")

    # find first match
    return {
        "torch": ver,
        "torchvision": _determine_torchvision(ver),
        "torchtext": _determine_torchtext(ver),
        "torchaudio": _determine_torchaudio(ver),
    }


def adjust(requires: List[str], pytorch_version: Optional[str] = None) -> List[str]:
    """Adjust the versions to be paired within pytorch ecosystem.

    >>> from pprint import pprint
    >>> pprint(adjust(["torch>=1.9.0", "torchvision>=0.10.0", "torchtext>=0.10.0", "torchaudio>=0.9.0"], "2.1.0"))
    ['torch==2.1.0',
     'torchvision==0.16.0',
     'torchtext==0.16.0',
     'torchaudio==2.1.0']
    """
    if not pytorch_version:
        import torch

        pytorch_version = torch.__version__
    if not pytorch_version:
        raise ValueError(f"invalid torch: {pytorch_version}")

    requires_ = []
    options = find_latest(pytorch_version)
    logging.debug(f"determined ecosystem alignment: {options}")
    for req in requires:
        req_split = req.strip().split("#", maxsplit=1)
        # anything before fst # shall be requirements
        req = req_split[0].strip()
        # anything after # in the line is comment
        comment = "" if len(req_split) < 2 else "  #" + req_split[1]
        if not req:
            # if only comment make it short
            requires_.append(comment.strip())
            continue
        for lib, version in options.items():
            replace = f"{lib}=={version}" if version else ""
            req = re.sub(rf"\b{lib}(?![-_\w]).*", replace, req)
        requires_.append(req + comment.rstrip())

    return requires_


def _offset_print(reqs: List[str], offset: str = "\t|\t") -> str:
    """Adding offset to each line for the printing requirements.

    >>> _offset_print(["torch==2.1.0", "torchvision==0.16.0", "torchtext==0.16.0", "torchaudio==2.1.0"])
    '\t|\ttorch==2.1.0\n\t|\ttorchvision==0.16.0\n\t|\ttorchtext==0.16.0\n\t|\ttorchaudio==2.1.0'
    """
    reqs = [offset + r for r in reqs]
    return os.linesep.join(reqs)


def main(requirements_path: str, torch_version: Optional[str] = None) -> None:
    """The main entry point with mapping to the CLI for positional arguments only."""
    # rU - universal line ending - https://stackoverflow.com/a/2717154/4521646
    with open(requirements_path, encoding="utf8") as fopen:
        requirements = fopen.readlines()
    requirements = adjust(requirements, torch_version)
    logging.info(
        f"requirements_path='{requirements_path}' with arg torch_version='{torch_version}' >>\n"
        f"{_offset_print(requirements)}"
    )
    with open(requirements_path, "w", encoding="utf8") as fopen:
        fopen.writelines([r + os.linesep for r in requirements])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        from fire import Fire

        Fire(main)
    except (ModuleNotFoundError, ImportError):
        main(*sys.argv[1:])
