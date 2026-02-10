"""Tests for Vivado log parsing (load_and_parse)."""

from __future__ import annotations

from pathlib import Path

from sawmill.models.message import Message


class TestLoadAndParse:
    """Tests for the load_and_parse hook."""

    def test_returns_list(self, plugin, sample_log):
        """load_and_parse should return a list."""
        result = plugin.load_and_parse(sample_log)
        assert isinstance(result, list)

    def test_items_are_messages(self, plugin, sample_log):
        """Each item should be a Message instance."""
        messages = plugin.load_and_parse(sample_log)
        for msg in messages:
            assert isinstance(msg, Message), f"Expected Message, got {type(msg)}"

    def test_messages_have_required_fields(self, plugin, sample_log):
        """Each message should have start_line, raw_text, and content populated."""
        messages = plugin.load_and_parse(sample_log)
        for msg in messages:
            assert msg.start_line >= 1, "start_line should be >= 1"
            assert msg.raw_text, "raw_text should not be empty"
            assert msg.content, "content should not be empty"

    def test_parses_basic_messages(self, plugin, tmp_path):
        """Plugin should parse basic Vivado messages."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text(
            "WARNING: [Vivado 12-3523] Component name change\n"
            "INFO: [Synth 8-1] Done\n"
        )
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 2
        assert messages[0].severity == "warning"
        assert messages[0].message_id == "Vivado 12-3523"
        assert messages[1].severity == "info"

    def test_parses_critical_warning(self, plugin, tmp_path):
        """Plugin should correctly parse critical warnings."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("CRITICAL WARNING: [Constraints 18-4427] Override warning\n")
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 1
        assert messages[0].severity == "critical_warning"
        assert messages[0].message_id == "Constraints 18-4427"

    def test_parses_error(self, plugin, tmp_path):
        """Plugin should correctly parse errors."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("ERROR: [Route 35-9] Routing failed\n")
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 1
        assert messages[0].severity == "error"
        assert messages[0].message_id == "Route 35-9"

    def test_multiline_message(self, plugin, tmp_path):
        """Plugin should group multi-line messages into single Message objects."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text(
            "WARNING: [Vivado 12-3523] Some warning\n"
            "  with continuation line\n"
            "  and another line\n"
            "INFO: [Synth 8-1] Next message\n"
        )
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 2
        assert messages[0].start_line == 1
        assert messages[0].end_line >= 3
        assert "continuation" in messages[0].raw_text

    def test_extracts_category(self, plugin, tmp_path):
        """Plugin should extract category from message ID."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("INFO: [Synth 8-6157] synthesizing module\n")
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 1
        assert messages[0].category == "synth"

    def test_extracts_content_without_prefix(self, plugin, tmp_path):
        """Plugin should extract message content without prefix."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text("WARNING: [Vivado 12-3523] Component name change attempted\n")
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 1
        assert "Component name change attempted" in messages[0].content
        assert not messages[0].content.startswith("WARNING")

    def test_skips_non_message_lines(self, plugin, tmp_path):
        """Plugin should skip non-message lines."""
        log_file = tmp_path / "vivado.log"
        log_file.write_text(
            "# Comment line\n"
            "Some random text\n"
            "INFO: [Synth 8-6157] First message\n"
            "Plain text between messages\n"
            "WARNING: [Vivado 12-3523] Second message\n"
        )
        messages = plugin.load_and_parse(log_file)
        assert len(messages) == 2
        assert messages[0].severity == "info"
        assert messages[1].severity == "warning"

    def test_empty_file_returns_empty_list(self, plugin, tmp_path):
        """An empty file should return an empty list."""
        empty = tmp_path / "empty.log"
        empty.write_text("")
        assert plugin.load_and_parse(empty) == []

    def test_missing_file_returns_empty_list(self, plugin, tmp_path):
        """A non-existent file should return an empty list."""
        missing = tmp_path / "nonexistent.log"
        assert plugin.load_and_parse(missing) == []

    def test_parses_real_log(self, plugin, vivado_log):
        """Plugin should parse the real Vivado log file."""
        messages = plugin.load_and_parse(vivado_log)
        assert len(messages) > 100
        severities = {m.severity for m in messages}
        assert "info" in severities
        assert "warning" in severities

    def test_extracts_file_refs_from_real_log(self, plugin, vivado_log):
        """Plugin should extract file references from real log."""
        messages = plugin.load_and_parse(vivado_log)
        messages_with_refs = [m for m in messages if m.file_ref is not None]
        assert len(messages_with_refs) > 0
        for m in messages_with_refs[:5]:
            assert m.file_ref is not None
            assert m.file_ref.path
            assert m.file_ref.line is not None
            assert m.file_ref.line > 0
