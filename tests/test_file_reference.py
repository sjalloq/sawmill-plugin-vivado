"""Tests for Vivado file reference extraction (extract_file_reference)."""

from __future__ import annotations


class TestExtractFileReference:
    """Tests for the extract_file_reference hook."""

    def test_extracts_bracketed_file_reference(self, plugin):
        """Plugin should extract file:line from bracketed format."""
        ref = plugin.extract_file_reference("synthesizing module 'top' [/path/to/file.v:53]")
        assert ref is not None
        assert ref.path == "/path/to/file.v"
        assert ref.line == 53

    def test_extracts_inline_file_reference(self, plugin):
        """Plugin should extract inline file:line references."""
        ref = plugin.extract_file_reference(
            "INFO: [Synth 8-6157] synthesizing module /home/user/design.v:100"
        )
        assert ref is not None
        assert ref.path == "/home/user/design.v"
        assert ref.line == 100

    def test_no_file_reference(self, plugin):
        """Plugin should return None when no file reference exists."""
        ref = plugin.extract_file_reference("WARNING: [Vivado 12-3523] some message")
        assert ref is None

    def test_file_reference_with_spaces_in_path(self, plugin):
        """Plugin should handle paths with spaces (bracketed format)."""
        ref = plugin.extract_file_reference("[/path/to/my file.v:42]")
        assert ref is not None
        assert ref.path == "/path/to/my file.v"
        assert ref.line == 42
