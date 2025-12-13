"""Tests for cleaning service."""

from pathlib import Path
from unittest.mock import Mock, patch  # noqa: F401

import pytest

from AutoQACLib.cleaning_service import CleaningService, CleanResult  # noqa: F401
from AutoQACLib.state_manager import AppState


class TestCleaningService:
    """Test cases for CleaningService."""

    @pytest.fixture
    def mock_main_config(self) -> Mock:
        """Create a mock main config manager."""
        config: Mock = Mock()
        config.get_game_config.return_value = {"xedit_list": [], "skip_list": []}
        config.get.return_value = []
        return config

    @pytest.fixture
    def mock_user_config(self) -> Mock:
        """Create a mock user config manager."""
        config: Mock = Mock()
        config.get.return_value = False
        return config

    @pytest.fixture
    def mock_state(self) -> Mock:
        """Create a mock state manager."""
        state: Mock = Mock()
        state.state = AppState()
        return state

    @pytest.fixture
    def service(self, mock_main_config: Mock, mock_user_config: Mock, mock_state: Mock) -> CleaningService:
        """Create a CleaningService instance for testing."""
        return CleaningService(mock_main_config, mock_user_config, mock_state)

    def test_build_cleaning_command_with_partial_forms_enabled(self, service: CleaningService) -> None:
        """Test that Partial Forms command line options are added when enabled."""
        # Create state with Partial Forms enabled
        state_snapshot: AppState = AppState(
            xedit_exe_path=Path("C:/xEdit/SSEEdit.exe"), game_type="SSE", partial_forms_enabled=True
        )

        # Build command
        command: str = service._build_cleaning_command("test.esp", state_snapshot)  # noqa: SLF001

        # Verify command includes Partial Forms options
        assert "-iknowwhatimdoing" in command
        assert "-allowmakepartial" in command
        assert "-QAC" in command
        assert "-autoexit" in command
        assert "-autoload" in command
        assert '"test.esp"' in command

    def test_build_cleaning_command_with_partial_forms_disabled(self, service: CleaningService) -> None:
        """Test that Partial Forms command line options are not added when disabled."""
        # Create state with Partial Forms disabled
        state_snapshot: AppState = AppState(
            xedit_exe_path=Path("C:/xEdit/SSEEdit.exe"), game_type="SSE", partial_forms_enabled=False
        )

        # Build command
        command: str = service._build_cleaning_command("test.esp", state_snapshot)  # noqa: SLF001

        # Verify command does not include Partial Forms options
        assert "-iknowwhatimdoing" not in command
        assert "-allowmakepartial" not in command
        assert "-QAC" in command
        assert "-autoexit" in command
        assert "-autoload" in command
        assert '"test.esp"' in command

    def test_build_cleaning_command_mo2_mode_with_partial_forms(self, service: CleaningService) -> None:
        """Test Partial Forms options with MO2 mode enabled."""
        # Create state with MO2 mode and Partial Forms enabled
        state_snapshot: AppState = AppState(
            xedit_exe_path=Path("C:/xEdit/SSEEdit.exe"),
            mo2_exe_path=Path("C:/MO2/ModOrganizer.exe"),
            game_type="SSE",
            mo2_mode=True,
            partial_forms_enabled=True,
        )

        # Build command
        command: str = service._build_cleaning_command("test.esp", state_snapshot)  # noqa: SLF001

        # Verify MO2 command structure with Partial Forms options
        assert str(state_snapshot.mo2_exe_path) in command
        assert "run" in command
        assert str(state_snapshot.xedit_exe_path) in command
        assert "-a" in command

        # Verify Partial Forms options are included in the command
        assert "-iknowwhatimdoing" in command
        assert "-allowmakepartial" in command
        assert "-QAC" in command
        assert "-autoexit" in command
        assert "-autoload" in command
        assert '"test.esp"' in command

    def test_build_cleaning_command_universal_xedit_with_partial_forms(self, service: CleaningService) -> None:
        """Test Partial Forms options with universal xEdit executable."""
        # Create state with universal xEdit and Partial Forms enabled
        state_snapshot: AppState = AppState(
            xedit_exe_path=Path("C:/xEdit/xEdit.exe"), game_type="SSE", partial_forms_enabled=True
        )

        # Build command
        command: str = service._build_cleaning_command("test.esp", state_snapshot)  # noqa: SLF001

        # Verify command includes Partial Forms options
        assert "-iknowwhatimdoing" in command
        assert "-allowmakepartial" in command
        assert "-SSE" in command
        assert "-QAC" in command
        assert "-autoexit" in command
        assert "-autoload" in command
        assert '"test.esp"' in command
