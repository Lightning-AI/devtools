import operator
import re
from unittest.mock import patch

import pytest

from lightning_utilities.core.imports import (
    compare_version,
    get_dependency_min_version_spec,
    lazy_import,
    module_available,
    RequirementCache,
    requires,
)

try:
    from importlib.metadata import PackageNotFoundError
except ImportError:
    # Python < 3.8
    from importlib_metadata import PackageNotFoundError


def test_module_exists():
    assert module_available("_pytest")
    assert module_available("_pytest.mark.structures")
    assert not module_available("_pytest.mark.asdf")
    assert not module_available("asdf")
    assert not module_available("asdf.bla.asdf")


def testcompare_version(monkeypatch):
    import pytest

    monkeypatch.setattr(pytest, "__version__", "1.8.9")
    assert not compare_version("pytest", operator.ge, "1.10.0")
    assert compare_version("pytest", operator.lt, "1.10.0")

    monkeypatch.setattr(pytest, "__version__", "1.10.0.dev123")
    assert compare_version("pytest", operator.ge, "1.10.0.dev123")
    assert not compare_version("pytest", operator.ge, "1.10.0.dev124")

    assert compare_version("pytest", operator.ge, "1.10.0.dev123", use_base_version=True)
    assert compare_version("pytest", operator.ge, "1.10.0.dev124", use_base_version=True)

    monkeypatch.setattr(pytest, "__version__", "1.10.0a0+0aef44c")  # dev version before rc
    assert compare_version("pytest", operator.ge, "1.10.0.rc0", use_base_version=True)
    assert not compare_version("pytest", operator.ge, "1.10.0.rc0")
    assert compare_version("pytest", operator.ge, "1.10.0", use_base_version=True)
    assert not compare_version("pytest", operator.ge, "1.10.0")


def test_requirement_cache():
    import pytest

    assert RequirementCache(f"pytest>={pytest.__version__}")
    assert not RequirementCache(f"pytest<{pytest.__version__}")
    assert "pip install -U '-'" in str(RequirementCache("-"))


def test_get_dependency_min_version_spec():
    attrs_min_version_spec = get_dependency_min_version_spec("pytest", "attrs")
    assert re.match(r"^>=[\d.]+$", attrs_min_version_spec)

    with pytest.raises(ValueError, match="'invalid' not found in package 'pytest'"):
        get_dependency_min_version_spec("pytest", "invalid")

    with pytest.raises(PackageNotFoundError, match="invalid"):
        get_dependency_min_version_spec("invalid", "invalid")


def test_lazy_import():
    def callback_fcn():
        raise ValueError

    with pytest.raises(ValueError):
        math = lazy_import("math", callback=callback_fcn)
        math.floor(5.1)
    with pytest.raises(ModuleNotFoundError):
        module = lazy_import("asdf")
        print(module)
    os = lazy_import("os")
    assert os.getcwd()


@requires("torch")
def my_torch_func(i: int):
    import torch  # noqa

    return i


def test_torch_func_raised():
    with pytest.raises(
        ModuleNotFoundError, match="Required dependencies not available. Please run `pip install torch`"
    ):
        my_torch_func(42)


@patch("torch", autospec=True)
def test_torch_func_passed():
    assert my_torch_func(42) == 42


class MyTorchClass:
    @requires("torch", "random")
    def __init__(self):
        from random import randint

        import torch  # noqa

        self._rnd = randint(1, 9)


def test_torch_class_raised():
    with pytest.raises(
        ModuleNotFoundError, match="Required dependencies not available. Please run `pip install torch`"
    ):
        MyTorchClass()


@patch("torch", autospec=True)
def test_torch_class_passed():
    cls = MyTorchClass()
    assert isinstance(cls._rnd, int)
