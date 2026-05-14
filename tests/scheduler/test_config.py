"""Tests for scheduler configuration loading."""

import tempfile

import pytest

from ryushi.scheduler.config import (
    get_category_slugs,
    load_config,
    parse_config,
    validate_cron_expression,
)
from ryushi.scheduler.exceptions import ConfigurationError


class TestValidateCronExpression:
    """Tests for cron expression validation."""

    def test_valid_daily_expression(self):
        """Test valid daily cron expression."""
        assert validate_cron_expression("0 6 * * *") is True

    def test_valid_weekly_expression(self):
        """Test valid weekly cron expression."""
        assert validate_cron_expression("0 8 * * 1") is True

    def test_valid_hourly_expression(self):
        """Test valid hourly cron expression."""
        assert validate_cron_expression("0 * * * *") is True

    def test_valid_complex_expression(self):
        """Test valid complex cron expression."""
        assert validate_cron_expression("30 6,18 * * 1-5") is True

    def test_invalid_expression_too_few_fields(self):
        """Test invalid expression with too few fields."""
        assert validate_cron_expression("0 6 *") is False

    def test_invalid_expression_bad_syntax(self):
        """Test invalid expression with bad syntax."""
        assert validate_cron_expression("invalid") is False

    def test_invalid_expression_out_of_range(self):
        """Test invalid expression with out of range value."""
        assert validate_cron_expression("60 6 * * *") is False


class TestLoadConfig:
    """Tests for loading config from file."""

    def test_load_valid_config(self):
        """Test loading a valid config file."""
        config_content = """
categories:
  technology:
    schedule: "0 6 * * *"
  science:
    schedule: "0 8 * * 1"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            config = load_config(f.name)

        assert len(config.categories) == 2
        assert config.categories["technology"].schedule == "0 6 * * *"
        assert config.categories["science"].schedule == "0 8 * * 1"

    def test_load_missing_file_returns_empty(self):
        """Test loading from nonexistent file returns empty config."""
        config = load_config("/nonexistent/config.yaml")
        assert len(config.categories) == 0

    def test_load_empty_file_returns_empty(self):
        """Test loading empty file returns empty config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            config = load_config(f.name)

        assert len(config.categories) == 0

    def test_load_invalid_yaml_raises_error(self):
        """Test loading invalid YAML raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            with pytest.raises(ConfigurationError):
                load_config(f.name)


class TestParseConfig:
    """Tests for parsing raw config dictionaries."""

    def test_parse_valid_config(self):
        """Test parsing valid configuration."""
        raw = {
            "categories": {
                "tech": {"schedule": "0 6 * * *"},
            }
        }
        config = parse_config(raw)
        assert len(config.categories) == 1
        assert config.categories["tech"].schedule == "0 6 * * *"

    def test_parse_empty_categories(self):
        """Test parsing config with no categories."""
        raw = {"categories": {}}
        config = parse_config(raw)
        assert len(config.categories) == 0

    def test_parse_missing_categories_key(self):
        """Test parsing config without categories key."""
        raw = {"other": "value"}
        config = parse_config(raw)
        assert len(config.categories) == 0

    def test_parse_skips_invalid_category_config(self):
        """Test parsing skips categories with invalid config format."""
        raw = {
            "categories": {
                "valid": {"schedule": "0 6 * * *"},
                "invalid": "not a dict",
            }
        }
        config = parse_config(raw)
        assert len(config.categories) == 1
        assert "valid" in config.categories
        assert "invalid" not in config.categories

    def test_parse_skips_missing_schedule(self):
        """Test parsing skips categories without schedule."""
        raw = {
            "categories": {
                "valid": {"schedule": "0 6 * * *"},
                "no_schedule": {"other": "value"},
            }
        }
        config = parse_config(raw)
        assert len(config.categories) == 1
        assert "valid" in config.categories

    def test_parse_skips_invalid_cron(self):
        """Test parsing skips categories with invalid cron."""
        raw = {
            "categories": {
                "valid": {"schedule": "0 6 * * *"},
                "invalid_cron": {"schedule": "invalid"},
            }
        }
        config = parse_config(raw)
        assert len(config.categories) == 1
        assert "valid" in config.categories
        assert "invalid_cron" not in config.categories

    def test_parse_invalid_categories_type(self):
        """Test parsing handles non-dict categories value."""
        raw = {"categories": "not a dict"}
        config = parse_config(raw)
        assert len(config.categories) == 0


class TestGetCategorySlugs:
    """Tests for get_category_slugs helper."""

    def test_get_slugs_from_config(self):
        """Test getting category slugs from config."""
        raw = {
            "categories": {
                "tech": {"schedule": "0 6 * * *"},
                "science": {"schedule": "0 8 * * *"},
            }
        }
        config = parse_config(raw)
        slugs = get_category_slugs(config)

        assert len(slugs) == 2
        assert "tech" in slugs
        assert "science" in slugs

    def test_get_slugs_empty_config(self):
        """Test getting slugs from empty config."""
        raw = {"categories": {}}
        config = parse_config(raw)
        slugs = get_category_slugs(config)

        assert slugs == []
