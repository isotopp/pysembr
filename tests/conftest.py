"""Shared subprocess seam for the installed CLI."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest


type CliRunner = Callable[..., subprocess.CompletedProcess[bytes]]


@pytest.fixture
def run_cli(tmp_path: Path) -> CliRunner:
    """Run the installed entry point in an isolated working directory."""
    executable = Path(sys.executable).parent / "pysembr"

    def run(*arguments: str, input: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [str(executable), *arguments],
            input=input,
            capture_output=True,
            cwd=tmp_path,
            check=False,
        )

    return run
