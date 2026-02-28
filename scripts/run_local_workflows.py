"""Run local equivalents of GitHub workflows before committing.

Workflows mirrored from .github/workflows:
- pylint.yml
- pytest.yml
- container_build.yml
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> int:
    """Run a command and stream output to the terminal."""
    printable = " ".join(command)
    print(f"\n>>> {printable}")
    completed = subprocess.run(command, env=env, check=False)
    return completed.returncode


def git_tracked_python_files(repo_root: Path) -> list[str]:
    """Return tracked Python files based on git ls-files."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("[error] Could not list tracked Python files via git.")
        if result.stderr:
            print(result.stderr.strip())
        return []

    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files


def run_pylint(repo_root: Path) -> int:
    """Run pylint with the same settings as CI."""
    py_files = git_tracked_python_files(repo_root)
    if not py_files:
        print("[error] No tracked Python files found. Skipping pylint with failure.")
        return 1

    command = [
        sys.executable,
        "-m",
        "pylint",
        "--rcfile=.pylintrc",
        *py_files,
    ]
    return run_command(command)


def run_pytest(repo_root: Path) -> int:
    """Run pytest with coverage like CI."""
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    repo_str = str(repo_root)
    env["PYTHONPATH"] = (
        f"{repo_str}{os.pathsep}{current_pythonpath}" if current_pythonpath else repo_str
    )

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=xml",
    ]
    return run_command(command, env=env)


def run_container_build(repo_root: Path) -> int:
    """Run a local container build check equivalent to the container workflow."""
    if shutil.which("docker") is None:
        print("[error] Docker is not available in PATH.")
        return 1

    dockerfile = repo_root / "Dockerfile"
    if not dockerfile.exists():
        print("[error] Dockerfile not found.")
        return 1

    image_tag = "ua4machinery2aas-client:local-check"

    command = [
        "docker",
        "build",
        "--file",
        "Dockerfile",
        "--tag",
        image_tag,
        ".",
    ]
    print("[info] Running local Docker build (single-platform validation).")
    return run_command(command)


def main() -> int:
    """Parse arguments and execute selected local workflow checks."""
    parser = argparse.ArgumentParser(
        description="Run local equivalents of CI workflows before commit."
    )
    parser.add_argument(
        "--skip-pylint",
        action="store_true",
        help="Skip pylint workflow check.",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip pytest workflow check.",
    )
    parser.add_argument(
        "--skip-container",
        action="store_true",
        help="Skip container build workflow check.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    checks: list[tuple[str, int]] = []

    print(f"Repository root: {repo_root}")
    print(f"Python executable: {sys.executable}")

    if not args.skip_pylint:
        checks.append(("pylint workflow", run_pylint(repo_root)))
    if not args.skip_pytest:
        checks.append(("pytest workflow", run_pytest(repo_root)))
    if not args.skip_container:
        checks.append(("container build workflow", run_container_build(repo_root)))

    if not checks:
        print("[error] No checks selected.")
        return 1

    print("\n=== Summary ===")
    has_failure = False
    for name, rc in checks:
        status = "OK" if rc == 0 else f"FAILED ({rc})"
        print(f"- {name}: {status}")
        if rc != 0:
            has_failure = True

    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
