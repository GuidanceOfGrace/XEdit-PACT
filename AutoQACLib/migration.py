"""Migration utilities for legacy PACT configuration files."""

from __future__ import annotations

import shutil
from pathlib import Path

from AutoQACLib.logging_config import get_logger

logger = get_logger(__name__)

# Legacy file paths
LEGACY_PACT_IGNORE_PATH = Path("PACT Ignore.yaml")

# New file paths
AUTOQAC_DATA_PATH = Path("AutoQAC Data")
AUTOQAC_IGNORE_PATH = AUTOQAC_DATA_PATH / "AutoQAC Ignore.yaml"


def migrate_legacy_ignore_file() -> bool:
    """
    Migrate legacy PACT Ignore.yaml to new AutoQAC Data/AutoQAC Ignore.yaml location.

    Returns:
        bool: True if migration was performed, False if no migration needed.
    """
    if not LEGACY_PACT_IGNORE_PATH.exists():
        return False

    logger.info(f"Found legacy ignore file: {LEGACY_PACT_IGNORE_PATH}")

    # Ensure the AutoQAC Data directory exists
    AUTOQAC_DATA_PATH.mkdir(parents=True, exist_ok=True)

    # Check if the new ignore file already has user content
    new_file_has_content = False
    if AUTOQAC_IGNORE_PATH.exists():
        try:
            with AUTOQAC_IGNORE_PATH.open(encoding="utf-8") as f:
                content = f.read()
                # Check if file has any actual plugin entries (not just comments/template)
                for line in content.splitlines():
                    line = line.strip()
                    # Found an actual entry (not Example Plugin template)
                    if line.startswith("- ") and "Example Plugin" not in line:
                        new_file_has_content = True
                        break
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading new ignore file: {e}")

    if new_file_has_content:
        logger.info(
            f"New ignore file {AUTOQAC_IGNORE_PATH} already has user content. "
            f"Legacy file {LEGACY_PACT_IGNORE_PATH} will not be automatically migrated. "
            f"Please manually merge your ignore lists if needed."
        )
        return False

    # Perform migration - copy legacy file to new location
    try:
        logger.info(f"Migrating {LEGACY_PACT_IGNORE_PATH} → {AUTOQAC_IGNORE_PATH}")
        shutil.copy2(LEGACY_PACT_IGNORE_PATH, AUTOQAC_IGNORE_PATH)
        logger.info(f"Migration complete. You may delete the legacy file: {LEGACY_PACT_IGNORE_PATH}")
    except (OSError, shutil.Error) as e:
        logger.error(f"Failed to migrate legacy ignore file: {e}")
        return False
    else:
        return True


def run_all_migrations() -> dict[str, bool]:
    """
    Run all migration checks and migrations.

    Returns:
        dict[str, bool]: Dictionary of migration names to success status.
    """
    results: dict[str, bool] = {}

    # Perform actual migrations
    results["ignore_file"] = migrate_legacy_ignore_file()

    return results
