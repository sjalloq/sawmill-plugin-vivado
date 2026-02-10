"""Tests for Vivado log file detection (can_handle)."""

from __future__ import annotations

from pathlib import Path


class TestCanHandle:
    """Tests for the can_handle hook."""

    def test_detects_vivado_header(self, plugin, tmp_path):
        """Plugin should detect Vivado logs with high confidence via header."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("# Vivado v2025.2 (64-bit)\nINFO: [Synth 8-6157] test")
        confidence = plugin.can_handle(log_file)
        assert confidence >= 0.9

    def test_detects_by_message_ids(self, plugin, tmp_path):
        """Plugin should detect logs with Vivado message IDs."""
        log_file = tmp_path / "build.log"
        log_file.write_text(
            "INFO: [Synth 8-6157] message 1\n"
            "WARNING: [Vivado 12-3523] message 2\n"
            "INFO: [IP_Flow 19-234] message 3\n"
        )
        confidence = plugin.can_handle(log_file)
        assert confidence >= 0.8

    def test_non_matching_file_returns_low_confidence(self, plugin, tmp_path):
        """A non-Vivado file should return confidence < 0.5."""
        other_file = tmp_path / "other.log"
        other_file.write_text("Some random log file content\nWith no Vivado patterns")
        confidence = plugin.can_handle(other_file)
        assert confidence < 0.5

    def test_missing_file_returns_zero(self, plugin, tmp_path):
        """A non-existent file should return 0.0."""
        missing = tmp_path / "nonexistent.log"
        assert plugin.can_handle(missing) == 0.0

    def test_low_confidence_for_name_only(self, plugin, tmp_path):
        """Plugin should have low confidence based only on filename."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("plain text without any patterns")
        confidence = plugin.can_handle(log_file)
        assert 0.0 < confidence < 0.5

    def test_detects_real_log(self, plugin, vivado_log):
        """Plugin should detect real Vivado log with high confidence."""
        confidence = plugin.can_handle(vivado_log)
        assert confidence >= 0.9
