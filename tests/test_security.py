"""Tests for command security validation."""

import pytest

from droidmind.security import assess_command_risk, validate_shell_command


def test_validate_shell_command_allows_simple_command():
    assert validate_shell_command("echo hello") is True


def test_validate_shell_command_blocks_disallowed_in_chained_segment():
    with pytest.raises(ValueError, match="explicitly disallowed"):
        validate_shell_command("echo ok && rm -rf /")


def test_validate_shell_command_allows_uiautomator_dump_then_cat():
    assert validate_shell_command("uiautomator dump /sdcard/ui.xml && cat /sdcard/ui.xml") is True


def test_validate_shell_command_rejects_other_uiautomator_subcommands():
    with pytest.raises(ValueError, match="Only 'uiautomator dump' is allowed"):
        validate_shell_command("uiautomator list")


def test_assess_command_risk_sees_disallowed_in_chained_segment():
    assert assess_command_risk("echo ok && rm -rf /").name in {"HIGH", "CRITICAL"}
