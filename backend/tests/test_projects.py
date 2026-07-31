"""Tests for project-related utility functions — formatting, status labels, source labels."""

from app.services.projects import format_bytes, source_status_label, source_type_label


class TestFormatBytes:
    """Test byte size formatting for display."""

    def test_none(self):
        assert format_bytes(None) == "Pending"

    def test_bytes(self):
        assert format_bytes(500) == "500 B"

    def test_kilobytes(self):
        assert format_bytes(2048) == "2.0 KB"

    def test_megabytes(self):
        result = format_bytes(3_500_000)
        assert "MB" in result
        assert "3" in result

    def test_zero(self):
        assert format_bytes(0) == "0 B"


class TestSourceStatusLabel:
    """Test mapping of DB status enums to display labels."""

    def test_processed(self):
        assert source_status_label("PROCESSED") == "processed"

    def test_processing(self):
        assert source_status_label("PROCESSING") == "processing"

    def test_failed(self):
        assert source_status_label("FAILED") == "failed"

    def test_cancelled(self):
        assert source_status_label("CANCELLED") == "cancelled"

    def test_queued(self):
        assert source_status_label("QUEUED") == "queued"

    def test_unknown_defaults_to_queued(self):
        assert source_status_label("SOME_OTHER") == "queued"


class TestSourceTypeLabel:
    """Test mapping of DB source type to display labels."""

    def test_pdf(self):
        assert source_type_label("PDF") == "pdf"

    def test_url(self):
        assert source_type_label("URL") == "url"

    def test_unknown(self):
        assert source_type_label("OTHER") == "url"