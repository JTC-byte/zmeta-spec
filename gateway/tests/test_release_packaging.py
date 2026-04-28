import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_MVP_PATH = ROOT / "release" / "build_mvp_packages.py"
spec = importlib.util.spec_from_file_location("zmeta_build_mvp_packages", BUILD_MVP_PATH)
build_mvp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_mvp)


def test_mvp_bundles_include_self_test_dependencies():
    required = {
        "conformance",
        "release/sign_release_artifacts.py",
    }

    assert required.issubset(set(build_mvp.COMMON_PATHS))
