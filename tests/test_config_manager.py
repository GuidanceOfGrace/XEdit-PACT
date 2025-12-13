"""Tests for the ConfigManager class."""

from pathlib import Path
from typing import Any
from unittest.mock import patch  # noqa: F401

import pytest  # noqa: F401

from AutoQACLib.config_manager import ConfigManager


class TestConfigManager:
    """Test the ConfigManager class."""

    def test_initialization_with_new_file(self, temp_test_config_file: Path) -> None:
        """Test ConfigManager initialization with a new config file."""
        config_path: Path = temp_test_config_file

        config: ConfigManager = ConfigManager(config_path)
        assert config._path == config_path  # noqa: SLF001
        assert config_path.exists()

        # Should create empty config
        all_config: dict[str, Any] = config.get_all()
        assert all_config == {}

    def test_initialization_with_existing_file(self, temp_test_config_file: Path) -> None:
        """Test ConfigManager initialization with existing config file."""
        config_path: Path = temp_test_config_file
        config_path.write_text("test_key: test_value\n")

        config: ConfigManager = ConfigManager(config_path)
        assert config._path == config_path  # noqa: SLF001

        # Should read existing config
        value: Any = config.get("test_key")
        assert value == "test_value"

    def test_get_method(self, config_manager: ConfigManager) -> None:
        """Test the get method."""
        # Test getting non-existent key with default
        value = config_manager.get("non_existent", "default_value")
        assert value == "default_value"

        # Test getting non-existent key without default
        value = config_manager.get("non_existent")
        assert value is None

    def test_set_method(self, config_manager: ConfigManager) -> None:
        """Test the set method."""
        # Set a value
        success = config_manager.set("test_key", "test_value")
        assert success is True

        # Verify the value was set
        value = config_manager.get("test_key")
        assert value == "test_value"

        # Test setting nested keys
        success = config_manager.set("nested.key", "nested_value")
        assert success is True

        value = config_manager.get("nested.key")
        assert value == "nested_value"

    def test_get_all_method(self, config_manager: ConfigManager) -> None:
        """Test the get_all method."""
        # Initially empty
        all_config = config_manager.get_all()
        assert all_config == {}

        # Add some values
        config_manager.set("key1", "value1")
        config_manager.set("key2", "value2")
        config_manager.set("nested.key3", "value3")

        # Get all config
        all_config = config_manager.get_all()
        assert "key1" in all_config
        assert "key2" in all_config
        assert "nested" in all_config
        assert all_config["key1"] == "value1"
        assert all_config["key2"] == "value2"
        assert all_config["nested"]["key3"] == "value3"

    def test_update_multiple_method(self, config_manager: ConfigManager) -> None:
        """Test the update_multiple method."""
        updates: dict[str, Any] = {"key1": "value1", "key2": "value2", "nested.key3": "value3"}

        success: bool = config_manager.update_multiple(updates)
        assert success is True

        # Verify all updates were applied
        assert config_manager.get("key1") == "value1"
        assert config_manager.get("key2") == "value2"
        assert config_manager.get("nested.key3") == "value3"

    def test_get_game_config(self, config_manager: ConfigManager) -> None:
        """Test the get_game_config method."""
        # Set up game-specific config
        config_manager.set("AutoQAC_Data.XEdit_Lists.Skyrim", ["Skyrim.esm", "Update.esm"])
        config_manager.set("AutoQAC_Data.Skip_Lists.Skyrim", ["Dawnguard.esm"])

        game_config: dict[str, Any] = config_manager.get_game_config("Skyrim")

        assert "xedit_list" in game_config
        assert "skip_list" in game_config
        assert game_config["xedit_list"] == ["Skyrim.esm", "Update.esm"]
        assert game_config["skip_list"] == ["Dawnguard.esm"]

    def test_get_paths_method(self, config_manager: ConfigManager) -> None:
        """Test the get_paths method."""
        # Set up path configurations
        config_manager.set("Load_Order.File", "/path/to/loadorder.txt")
        config_manager.set("Mod_Organizer.Binary", "/path/to/ModOrganizer.exe")
        config_manager.set("Mod_Organizer.Install_Path", "/path/to/ModOrganizer")
        config_manager.set("xEdit.Binary", "/path/to/xEdit.exe")
        config_manager.set("xEdit.Install_Path", "/path/to/xEdit")

        paths: dict[str, Any] = config_manager.get_paths()

        assert "load_order_path" in paths
        assert "mo2_exe_path" in paths
        assert "mo2_install_path" in paths
        assert "xedit_exe_path" in paths
        assert "xedit_install_path" in paths

        assert paths["load_order_path"] == Path("/path/to/loadorder.txt")
        assert paths["mo2_exe_path"] == Path("/path/to/ModOrganizer.exe")
        assert paths["mo2_install_path"] == Path("/path/to/ModOrganizer")
        assert paths["xedit_exe_path"] == Path("/path/to/xEdit.exe")
        assert paths["xedit_install_path"] == Path("/path/to/xEdit")

    def test_get_settings_method(self, config_manager: ConfigManager) -> None:
        """Test the get_settings method."""
        # Set up settings
        config_manager.set("Settings.Journal_Expiration", 7)
        config_manager.set("Settings.Cleaning_Timeout", 300)
        config_manager.set("Settings.CPU_Threshold", 5)
        config_manager.set("Settings.MO2_Mode", False)

        settings: dict[str, Any] = config_manager.get_settings()

        assert "journal_expiration" in settings
        assert "cleaning_timeout" in settings
        assert "cpu_threshold" in settings
        assert "mo2_mode" in settings

        assert settings["journal_expiration"] == 7
        assert settings["cleaning_timeout"] == 300
        assert settings["cpu_threshold"] == 5
        assert settings["mo2_mode"] is False

    def test_validate_paths_method(self, config_manager: ConfigManager) -> None:
        """Test the validate_paths method."""
        # Set up paths (some valid, some invalid)
        config_manager.set("Load_Order.File", str(Path(__file__)))  # Valid path
        config_manager.set("Mod_Organizer.Binary", "/non/existent/path.exe")  # Invalid path
        config_manager.set("xEdit.Binary", "/another/non/existent/path.exe")  # Invalid path

        validation: dict[str, Any] = config_manager.validate_paths()

        assert "load_order_path" in validation
        assert "mo2_exe_path" in validation
        assert "xedit_exe_path" in validation

        # Should validate based on file existence
        assert validation["load_order_path"] is True  # This file exists
        assert validation["mo2_exe_path"] is False  # This path doesn't exist
        assert validation["xedit_exe_path"] is False  # This path doesn't exist

    def test_error_handling(self, config_manager: ConfigManager) -> None:
        """Test error handling in config operations."""
        # Test setting with invalid data (should not crash)
        success: bool = config_manager.set("test_key", {"complex": "data"})
        assert success is True

        # Test getting from corrupted config (should return default)
        value: Any = config_manager.get("corrupted_key", "default")
        assert value == "default"

    def test_nested_key_operations(self, config_manager: ConfigManager) -> None:
        """Test operations with deeply nested keys."""
        # Set deeply nested value
        config_manager.set("level1.level2.level3.level4", "deep_value")

        # Get the value
        value = config_manager.get("level1.level2.level3.level4")
        assert value == "deep_value"

        # Get intermediate level
        level2 = config_manager.get("level1.level2")
        assert isinstance(level2, dict)
        assert "level3" in level2

        # Update nested value
        config_manager.set("level1.level2.level3.level4", "updated_value")
        value = config_manager.get("level1.level2.level3.level4")
        assert value == "updated_value"

    def test_config_file_persistence(self, config_manager: ConfigManager) -> None:
        """Test that config changes persist to file."""
        # Set some values
        config_manager.set("persistent_key", "persistent_value")
        config_manager.set("nested.persistent", "nested_persistent_value")

        # Create new config manager with same file
        new_config: ConfigManager = ConfigManager(config_manager._path)  # noqa: SLF001

        # Values should persist
        assert new_config.get("persistent_key") == "persistent_value"
        assert new_config.get("nested.persistent") == "nested_persistent_value"

    def test_empty_file_handling(self, temp_test_config_file: Path) -> None:
        """Test handling of empty config files."""
        config_path: Path = temp_test_config_file
        # Create empty file
        config_path.write_text("")

        config: ConfigManager = ConfigManager(config_path)

        # Should handle empty file gracefully
        all_config: dict[str, Any] = config.get_all()
        assert all_config == {}

        # Should be able to set values
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
