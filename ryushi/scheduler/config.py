"""Configuration loading for scheduler.

This module provides functionality to load and validate schedule
configurations from config.yaml.
"""

import logging
from pathlib import Path

import yaml
from croniter import croniter

from ryushi.scheduler.exceptions import ConfigurationError
from ryushi.scheduler.models import CategoryConfig, ScheduleConfig

logger = logging.getLogger(__name__)


def validate_cron_expression(expression: str) -> bool:
    """Validate a cron expression.

    Args:
        expression: A 5-field cron expression.

    Returns:
        True if valid, False otherwise.
    """
    try:
        croniter(expression)
        return True
    except (ValueError, KeyError):
        return False


def load_config(config_path: str | Path) -> ScheduleConfig:
    """Load schedule configuration from a YAML file.

    Args:
        config_path: Path to the config.yaml file.

    Returns:
        ScheduleConfig with validated category schedules.

    Raises:
        ConfigurationError: If the file cannot be read or parsed.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.warning("Config file not found at %s, using empty config", config_path)
        return ScheduleConfig()

    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse config file: {e}") from e
    except OSError as e:
        raise ConfigurationError(f"Failed to read config file: {e}") from e

    if raw_config is None:
        logger.info("Config file is empty, using empty config")
        return ScheduleConfig()

    return parse_config(raw_config)


def parse_config(raw_config: dict) -> ScheduleConfig:
    """Parse raw configuration dictionary into ScheduleConfig.

    Args:
        raw_config: Dictionary from YAML parsing.

    Returns:
        ScheduleConfig with validated category configurations.
    """
    categories: dict[str, CategoryConfig] = {}

    raw_categories = raw_config.get("categories", {})
    if not isinstance(raw_categories, dict):
        logger.warning("Invalid 'categories' format, expected dict")
        return ScheduleConfig()

    for category_slug, category_config in raw_categories.items():
        if not isinstance(category_config, dict):
            logger.warning(
                "Invalid config for category '%s', expected dict, skipping",
                category_slug,
            )
            continue

        schedule = category_config.get("schedule")
        if not schedule:
            logger.warning(
                "No schedule defined for category '%s', skipping",
                category_slug,
            )
            continue

        if not validate_cron_expression(schedule):
            logger.error(
                "Invalid cron expression '%s' for category '%s', skipping",
                schedule,
                category_slug,
            )
            continue

        # Create CategoryConfig with optional fields (language, prompt, favicon, gist)
        try:
            gist_enabled = category_config.get("gist_enabled", False)
            gist_id = category_config.get("gist_id")

            # Warn if gist is enabled but ID is missing
            if gist_enabled and not gist_id:
                logger.warning(
                    "Category '%s' has gist_enabled=true but no gist_id provided, skipping Gist publishing",
                    category_slug,
                )

            config = CategoryConfig(
                schedule=schedule,
                language=category_config.get("language", "German"),
                prompt=category_config.get("prompt"),
                favicon=category_config.get("favicon"),
                gist_enabled=gist_enabled,
                gist_id=gist_id,
            )
            categories[category_slug] = config
            logger.info(
                "Loaded config for '%s': schedule=%s, language=%s, gist_enabled=%s",
                category_slug,
                schedule,
                config.language,
                config.gist_enabled,
            )
        except Exception as e:
            logger.error(
                "Failed to parse config for category '%s': %s, skipping",
                category_slug,
                str(e),
            )
            continue

    return ScheduleConfig(categories=categories)


def get_category_slugs(config: ScheduleConfig) -> list[str]:
    """Get list of category slugs from config.

    Args:
        config: The schedule configuration.

    Returns:
        List of category slugs with schedules.
    """
    return list(config.categories.keys())
