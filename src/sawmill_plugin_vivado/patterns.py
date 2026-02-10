"""Regex patterns for Vivado log parsing.

Patterns extracted from the Vivado plugin for detecting severity levels,
message IDs, file references, and multi-line message continuation.
"""

from __future__ import annotations

import re

# Standard message format: TYPE: [Category ID-Number] message [file:line]

SEVERITY_PATTERNS = {
    "critical_warning": re.compile(r"^CRITICAL WARNING:\s*"),
    "error": re.compile(r"^ERROR:\s*"),
    "warning": re.compile(r"^WARNING:\s*"),
    "info": re.compile(r"^INFO:\s*"),
}

# Message ID pattern: [Category Number-ID]
MESSAGE_ID_PATTERN = re.compile(r"\[([A-Za-z_]+ \d+-\d+)\]")

# File reference pattern: [/path/to/file.ext:line] or [file.ext:line]
FILE_REF_PATTERN = re.compile(r"\[([^\]]+):(\d+)\]\s*$")

# Alternative file reference: /path/to/file.v:53 (without brackets, at end)
FILE_REF_INLINE_PATTERN = re.compile(r"(/[^\s\[\]]+\.\w+):(\d+)")

# Vivado header detection (MULTILINE for searching in joined content)
VIVADO_HEADER_PATTERN = re.compile(r"^#.*Vivado v\d+\.\d+", re.MULTILINE)

# Continuation patterns - lines that are part of a multi-line message
CONTINUATION_PATTERNS = [
    re.compile(r"^\s+"),  # Indented lines
    re.compile(r"^\|"),  # Table rows
    re.compile(r"^-+$"),  # Separator lines
    re.compile(r"^=+$"),  # Separator lines
]

# Vivado-specific message categories for detection
VIVADO_CATEGORIES = {
    "Synth",
    "Vivado",
    "IP_Flow",
    "Common",
    "DRC",
    "Timing",
    "Route",
    "Opt",
    "Physopt",
    "Power",
    "Device",
    "Project",
    "Constraints",
}
