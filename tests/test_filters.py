"""Tests for Vivado filter definitions (get_filters)."""

from __future__ import annotations

import re


class TestGetFilters:
    """Tests for the get_filters hook."""

    def test_returns_only_domain_specific_filters(self, plugin):
        """Plugin should only provide domain-specific filters, not severity mirrors."""
        filters = plugin.get_filters()
        filter_ids = [f.id for f in filters]
        # Severity-mirror filters should NOT be present
        assert "errors" not in filter_ids
        assert "critical-warnings" not in filter_ids
        assert "warnings" not in filter_ids
        assert "info" not in filter_ids

    def test_has_required_fields(self, plugin):
        """All filters should have required fields."""
        for f in plugin.get_filters():
            assert f.id
            assert f.name
            assert f.pattern
            assert f.source == "plugin:vivado"

    def test_includes_category_filters(self, plugin):
        """Plugin should provide category-specific filters."""
        filters = plugin.get_filters()
        filter_ids = [f.id for f in filters]
        assert "synthesis" in filter_ids
        assert "drc" in filter_ids
        assert "timing-issues" in filter_ids
        assert "constraints" in filter_ids
        assert "ip-flow" in filter_ids
        assert "routing" in filter_ids

    def test_filter_count(self, plugin):
        """Plugin should provide exactly 6 domain-specific filters."""
        filters = plugin.get_filters()
        assert len(filters) == 6

    def test_patterns_are_valid_regex(self, plugin):
        """All filter patterns should be valid regex."""
        for f in plugin.get_filters():
            re.compile(f.pattern)
