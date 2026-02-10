"""Vivado log parser plugin for sawmill.

This plugin parses Xilinx Vivado log files and extracts structured messages
including severity, message IDs, and file references.
"""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

from sawmill.models.filter_def import FilterDefinition
from sawmill.models.message import FileRef, Message
from sawmill.plugin import SawmillPlugin, hookimpl

from sawmill_plugin_vivado.patterns import (
    CONTINUATION_PATTERNS,
    FILE_REF_INLINE_PATTERN,
    FILE_REF_PATTERN,
    MESSAGE_ID_PATTERN,
    SEVERITY_PATTERNS,
    VIVADO_CATEGORIES,
    VIVADO_HEADER_PATTERN,
)


class VivadoPlugin(SawmillPlugin):
    """Parser for Xilinx Vivado log files.

    Detects and parses Vivado synthesis, implementation, and bitstream logs.
    Handles multi-line messages including tables and continuation lines.

    Attributes:
        name: Plugin identifier ("vivado")
        version: Plugin version
        description: Human-readable description
    """

    name = "vivado"
    version = version("sawmill-plugin-vivado")
    description = "Parser for Xilinx Vivado synthesis and implementation logs"

    @hookimpl
    def can_handle(self, path: Path) -> float:
        """Determine if this is a Vivado log file.

        Checks for Vivado header signature and message patterns.

        Args:
            path: Path to the log file to check.

        Returns:
            Confidence score (0.0 to 1.0).
        """
        if not path.exists():
            return 0.0

        try:
            # Read first 50 lines to check for Vivado signature
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= 50:
                        break
                    lines.append(line)

            content = "".join(lines)

            # High confidence: Vivado header found
            if VIVADO_HEADER_PATTERN.search(content):
                return 0.95

            # Medium-high confidence: Multiple Vivado-style message IDs
            message_ids = MESSAGE_ID_PATTERN.findall(content)
            vivado_matches = sum(
                1 for mid in message_ids if mid.split()[0] in VIVADO_CATEGORIES
            )

            if vivado_matches >= 3:
                return 0.85

            # Medium confidence: Has severity patterns typical of Vivado
            severity_count = 0
            for line in lines:
                for pattern in SEVERITY_PATTERNS.values():
                    if pattern.match(line):
                        severity_count += 1
                        break

            if severity_count >= 5:
                return 0.6

            # Low confidence: filename suggests Vivado
            if "vivado" in path.name.lower():
                return 0.4

            return 0.0

        except Exception:
            return 0.0

    @hookimpl
    def load_and_parse(self, path: Path) -> list[Message]:
        """Load and parse a Vivado log file.

        Parses the log file, extracting messages with severity, IDs, and
        file references. Groups multi-line messages appropriately.

        Args:
            path: Path to the Vivado log file.

        Returns:
            List of Message objects.
        """
        if not path.exists():
            return []

        messages: list[Message] = []

        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            return []

        if not lines:
            return []

        i = 0
        while i < len(lines):
            line = lines[i]
            severity = self._detect_severity(line)

            if severity:
                # Found a message start
                start_line = i + 1  # 1-indexed
                raw_lines = [line]

                # Look for continuation lines
                j = i + 1
                while j < len(lines) and self._is_continuation(lines[j]):
                    raw_lines.append(lines[j])
                    j += 1

                end_line = j  # 1-indexed (exclusive becomes inclusive)
                raw_text = "".join(raw_lines).rstrip("\n")

                # Extract message components
                message_id = self._extract_message_id(line)
                content = self._extract_content(line, severity)
                file_ref = self.extract_file_reference(raw_text)
                category = self._extract_category(message_id)

                messages.append(
                    Message(
                        start_line=start_line,
                        end_line=end_line,
                        raw_text=raw_text,
                        content=content,
                        severity=severity,
                        message_id=message_id,
                        category=category,
                        file_ref=file_ref,
                    )
                )

                i = j
            else:
                i += 1

        return messages

    @hookimpl
    def get_severity_levels(self) -> list[dict]:
        """Get Vivado severity levels.

        Vivado uses: CRITICAL WARNING, ERROR, WARNING, INFO

        Returns:
            List of severity level definitions.
        """
        return [
            {
                "id": "error",
                "name": "Error",
                "level": 3,
                "style": "red bold",
            },
            {
                "id": "critical_warning",
                "name": "Critical Warning",
                "level": 2,
                "style": "red",
            },
            {
                "id": "warning",
                "name": "Warning",
                "level": 1,
                "style": "yellow",
            },
            {
                "id": "info",
                "name": "Info",
                "level": 0,
                "style": "cyan",
            },
        ]

    @hookimpl
    def get_grouping_fields(self) -> list[dict]:
        """Get available grouping fields for Vivado logs.

        Vivado logs can be grouped by standard fields plus category.

        Returns:
            List of grouping field definitions.
        """
        return [
            {
                "id": "severity",
                "name": "Severity",
                "field_type": "builtin",
                "description": "Group by message severity (Error, Warning, Info)",
            },
            {
                "id": "id",
                "name": "Message ID",
                "field_type": "builtin",
                "description": "Group by Vivado message ID (e.g., Synth 8-6157)",
            },
            {
                "id": "category",
                "name": "Category",
                "field_type": "builtin",
                "description": "Group by message category (synth, timing, drc, etc.)",
            },
            {
                "id": "file",
                "name": "Source File",
                "field_type": "file_ref",
                "description": "Group by source file path",
            },
        ]

    @hookimpl
    def get_filters(self) -> list[FilterDefinition]:
        """Get filter definitions for Vivado logs.

        Returns:
            List of pre-defined filter definitions.
        """
        return [
            FilterDefinition(
                id="timing-issues",
                name="Timing Issues",
                pattern=r"(timing|slack|WNS|TNS|setup|hold)",
                source="plugin:vivado",
                description="Timing-related messages",
            ),
            FilterDefinition(
                id="synthesis",
                name="Synthesis",
                pattern=r"\[Synth \d+-\d+\]",
                source="plugin:vivado",
                description="Synthesis messages",
            ),
            FilterDefinition(
                id="drc",
                name="DRC",
                pattern=r"\[DRC \d+-\d+\]",
                source="plugin:vivado",
                description="Design Rule Check messages",
            ),
            FilterDefinition(
                id="constraints",
                name="Constraints",
                pattern=r"\[Constraints \d+-\d+\]",
                source="plugin:vivado",
                description="Constraint-related messages",
            ),
            FilterDefinition(
                id="ip-flow",
                name="IP Flow",
                pattern=r"\[IP_Flow \d+-\d+\]",
                source="plugin:vivado",
                description="IP core generation messages",
            ),
            FilterDefinition(
                id="routing",
                name="Routing",
                pattern=r"\[Route \d+-\d+\]",
                source="plugin:vivado",
                description="Routing messages",
            ),
        ]

    @hookimpl
    def extract_file_reference(self, content: str) -> FileRef | None:
        """Extract a file reference from message content.

        Vivado logs include file references in formats like:
        - [/path/to/file.v:53]
        - /path/to/file.v:53

        Args:
            content: The message content to search.

        Returns:
            FileRef if found, None otherwise.
        """
        # Try bracketed format first: [/path/file.v:53]
        match = FILE_REF_PATTERN.search(content)
        if match:
            path_str = match.group(1)
            line_num = int(match.group(2))
            return FileRef(path=path_str, line=line_num)

        # Try inline format: /path/file.v:53
        match = FILE_REF_INLINE_PATTERN.search(content)
        if match:
            path_str = match.group(1)
            line_num = int(match.group(2))
            return FileRef(path=path_str, line=line_num)

        return None

    def _detect_severity(self, line: str) -> str | None:
        """Detect the severity level of a log line."""
        for severity, pattern in SEVERITY_PATTERNS.items():
            if pattern.match(line):
                return severity
        return None

    def _is_continuation(self, line: str) -> bool:
        """Check if a line is a continuation of a previous message."""
        if not line.strip():
            return False
        if any(pattern.match(line) for pattern in SEVERITY_PATTERNS.values()):
            return False
        return any(pattern.match(line) for pattern in CONTINUATION_PATTERNS)

    def _extract_message_id(self, line: str) -> str | None:
        """Extract the message ID from a log line."""
        match = MESSAGE_ID_PATTERN.search(line)
        return match.group(1) if match else None

    def _extract_content(self, line: str, severity: str) -> str:
        """Extract the message content without severity prefix."""
        pattern = SEVERITY_PATTERNS.get(severity)
        if pattern:
            line = pattern.sub("", line)
        line = MESSAGE_ID_PATTERN.sub("", line)
        line = FILE_REF_PATTERN.sub("", line)
        return line.strip()

    def _extract_category(self, message_id: str | None) -> str | None:
        """Extract the category from a message ID."""
        if not message_id:
            return None
        parts = message_id.split()
        return parts[0].lower() if parts else None
