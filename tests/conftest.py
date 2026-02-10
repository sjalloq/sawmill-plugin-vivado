"""Shared fixtures for vivado plugin tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from sawmill_plugin_vivado.plugin import VivadoPlugin


@pytest.fixture
def plugin():
    """Return an instance of the vivado plugin."""
    return VivadoPlugin()


@pytest.fixture
def sample_log(tmp_path: Path) -> Path:
    """Create a sample log file for testing using the real vivado log."""
    log_file = tmp_path / "sample.log"
    log_file.write_text(
        (Path(__file__).parent.parent / "examples" / "sample.log").read_text()
    )
    return log_file


@pytest.fixture
def vivado_log() -> Path:
    """Full Vivado log file for integration tests."""
    return Path(__file__).parent.parent / "examples" / "sample.log"


@pytest.fixture
def small_log(tmp_path: Path) -> Path:
    """Minimal multi-format log for unit tests."""
    content = """\
INFO: [Synth 8-6157] synthesizing module 'top' [/path/file.v:10]
WARNING: [Vivado 12-3523] Component name change
  Additional detail line
  Another detail line
CRITICAL WARNING: [Constraints 18-4427] Override warning
ERROR: [Route 35-9] Routing failed
Plain text line with no format
"""
    f = tmp_path / "test.log"
    f.write_text(content)
    return f
