"""BIP85 CLI integration tests.

Tests the BIP85 command-line interface integration with SSeed.
Covers all applications (BIP39, hex, password) and CLI scenarios.
"""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from bip_utils import Bip39Languages

from sseed.bip39 import (
    generate_mnemonic,
    validate_mnemonic,
)
from sseed.cli.commands.bip85 import (
    Bip85Command,
    handle_bip85_command,
)


class TestBip85CliBasic:
    """Test basic BIP85 CLI functionality."""

    def test_command_initialization(self):
        """Test that the BIP85 command initializes correctly."""
        cmd = Bip85Command()
        assert cmd.name == "bip85"
        assert "BIP85" in cmd.help_text
        assert "deterministic child entropy" in cmd.description

    def test_add_arguments_structure(self):
        """Test that arguments are added correctly."""
        cmd = Bip85Command()
        parser = argparse.ArgumentParser()
        cmd.add_arguments(parser)

        # Test that subparsers were created by checking for SubParsersAction
        subparsers_actions = [
            action
            for action in parser._actions
            if action.__class__.__name__ == "_SubParsersAction"
        ]
        assert len(subparsers_actions) == 1
        subparsers_action = subparsers_actions[0]
        assert "bip39" in subparsers_action.choices
        assert "hex" in subparsers_action.choices
        assert "password" in subparsers_action.choices

    def test_backward_compatibility_wrapper(self):
        """Test that the backward compatibility wrapper works."""
        # This just tests that the function exists and is callable
        assert callable(handle_bip85_command)

    def test_application_info_method(self):
        """Test the get_application_info method."""
        cmd = Bip85Command()
        info = cmd.get_application_info()
        assert "Supported BIP85 Applications" in info
        assert "BIP39" in info
        assert "Hex" in info
        assert "Password" in info


class TestBip85CliBip39:
    """Test BIP85 CLI BIP39 application."""

    @pytest.fixture
    def master_mnemonic(self):
        """Generate a test master mnemonic."""
        return generate_mnemonic(Bip39Languages.ENGLISH)

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink(missing_ok=True)

    def test_bip39_generation_default_options(self, master_mnemonic):
        """Test BIP39 generation with default options."""
        cmd = Bip85Command()

        # Mock stdin to provide master mnemonic
        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="bip39",
                    input=None,
                    output=None,
                    words=12,
                    language="en",
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 0

                # Check that output was printed
                assert mock_print.call_count >= 2  # mnemonic + metadata

                # Verify the generated mnemonic is valid
                output_calls = [
                    call[0][0] for call in mock_print.call_args_list if call[0]
                ]
                mnemonic_output = output_calls[0]  # First output should be the mnemonic
                assert validate_mnemonic(mnemonic_output)

    def test_bip39_generation_multiple_languages(self, master_mnemonic):
        """Test BIP39 generation in different languages."""
        cmd = Bip85Command()
        languages = ["en", "es", "fr", "it"]

        for lang in languages:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="bip39",
                        input=None,
                        output=None,
                        words=12,
                        language=lang,
                        index=0,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Verify output exists
                    assert mock_print.call_count >= 2

    def test_bip39_generation_different_word_counts(self, master_mnemonic):
        """Test BIP39 generation with different word counts."""
        cmd = Bip85Command()
        word_counts = [12, 15, 18, 21, 24]

        for count in word_counts:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="bip39",
                        input=None,
                        output=None,
                        words=count,
                        language="en",
                        index=0,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Verify the generated mnemonic has correct word count
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    mnemonic_output = output_calls[0]
                    assert len(mnemonic_output.split()) == count

    def test_bip39_file_output(self, master_mnemonic, temp_file):
        """Test BIP39 generation with file output."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="bip39",
                    input=None,
                    output=str(temp_file),
                    words=12,
                    language="en",
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 0

                # Check that success message was printed
                assert any(
                    "written to" in str(call) for call in mock_print.call_args_list
                )

                # Verify file was created and contains valid content
                assert temp_file.exists()
                content = temp_file.read_text()
                assert "BIP85 BIP39 Generation" in content
                assert "Application: bip39" in content

    def test_bip39_with_passphrase(self, master_mnemonic):
        """Test BIP39 generation with passphrase."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="bip39",
                    input=None,
                    output=None,
                    words=12,
                    language="en",
                    index=0,
                    passphrase="test123",
                )

                result = cmd.handle(args)
                assert result == 0

                # Verify output exists
                assert mock_print.call_count >= 2

    def test_bip39_different_indices(self, master_mnemonic):
        """Test BIP39 generation with different indices produces different results."""
        cmd = Bip85Command()
        results = []

        for index in [0, 1, 42]:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="bip39",
                        input=None,
                        output=None,
                        words=12,
                        language="en",
                        index=index,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Extract the mnemonic from output
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    mnemonic_output = output_calls[0]
                    results.append(mnemonic_output)

        # Verify all results are different
        assert len(set(results)) == len(results)


class TestBip85CliHex:
    """Test BIP85 CLI hex application."""

    @pytest.fixture
    def master_mnemonic(self):
        """Generate a test master mnemonic."""
        return generate_mnemonic(Bip39Languages.ENGLISH)

    def test_hex_generation_default_options(self, master_mnemonic):
        """Test hex generation with default options."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="hex",
                    input=None,
                    output=None,
                    bytes=32,
                    uppercase=False,
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 0

                # Verify hex output
                output_calls = [
                    call[0][0] for call in mock_print.call_args_list if call[0]
                ]
                hex_output = output_calls[0]
                assert len(hex_output) == 64  # 32 bytes * 2 chars
                assert all(c in "0123456789abcdef" for c in hex_output)

    def test_hex_generation_uppercase(self, master_mnemonic):
        """Test hex generation with uppercase option."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="hex",
                    input=None,
                    output=None,
                    bytes=32,
                    uppercase=True,
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 0

                # Verify uppercase hex output
                output_calls = [
                    call[0][0] for call in mock_print.call_args_list if call[0]
                ]
                hex_output = output_calls[0]
                assert len(hex_output) == 64
                assert all(c in "0123456789ABCDEF" for c in hex_output)

    def test_hex_generation_different_byte_lengths(self, master_mnemonic):
        """Test hex generation with different byte lengths."""
        cmd = Bip85Command()
        byte_lengths = [16, 24, 32, 48, 64]

        for length in byte_lengths:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="hex",
                        input=None,
                        output=None,
                        bytes=length,
                        uppercase=False,
                        index=0,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Verify correct hex length
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    hex_output = output_calls[0]
                    assert len(hex_output) == length * 2

    def test_hex_validation_errors(self, master_mnemonic):
        """Test hex generation with invalid byte counts."""
        cmd = Bip85Command()

        # Test invalid byte count (too small)
        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print"):
                args = argparse.Namespace(
                    application="hex",
                    input=None,
                    output=None,
                    bytes=8,  # Too small
                    uppercase=False,
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 2  # EXIT_VALIDATION_ERROR


class TestBip85CliPassword:
    """Test BIP85 CLI password application."""

    @pytest.fixture
    def master_mnemonic(self):
        """Generate a test master mnemonic."""
        return generate_mnemonic(Bip39Languages.ENGLISH)

    def test_password_generation_default_options(self, master_mnemonic):
        """Test password generation with default options."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="password",
                    input=None,
                    output=None,
                    length=20,
                    charset="base64",
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 0

                # Verify password output
                output_calls = [
                    call[0][0] for call in mock_print.call_args_list if call[0]
                ]
                password_output = output_calls[0]
                assert len(password_output) == 20

    def test_password_generation_different_charsets(self, master_mnemonic):
        """Test password generation with different character sets."""
        cmd = Bip85Command()
        charsets = ["base64", "base85", "alphanumeric", "ascii"]

        for charset in charsets:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="password",
                        input=None,
                        output=None,
                        length=20,
                        charset=charset,
                        index=0,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Verify password exists
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    password_output = output_calls[0]
                    assert len(password_output) == 20

    def test_password_generation_different_lengths(self, master_mnemonic):
        """Test password generation with different lengths."""
        cmd = Bip85Command()
        lengths = [10, 15, 25, 50, 100]

        for length in lengths:
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="password",
                        input=None,
                        output=None,
                        length=length,
                        charset="base64",
                        index=0,
                        passphrase="",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Verify correct password length
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    password_output = output_calls[0]
                    assert len(password_output) == length

    def test_password_validation_errors(self, master_mnemonic):
        """Test password generation with invalid lengths."""
        cmd = Bip85Command()

        # Test invalid length (too small)
        with patch(
            "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
        ):
            with patch("builtins.print"):
                args = argparse.Namespace(
                    application="password",
                    input=None,
                    output=None,
                    length=5,  # Too small
                    charset="base64",
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 2  # EXIT_VALIDATION_ERROR


class TestBip85CliErrorHandling:
    """Test BIP85 CLI error handling."""

    def test_invalid_master_mnemonic(self):
        """Test handling of invalid master mnemonic."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin",
            return_value="invalid mnemonic words",
        ):
            with patch("builtins.print") as mock_print:
                args = argparse.Namespace(
                    application="bip39",
                    input=None,
                    output=None,
                    words=12,
                    language="en",
                    index=0,
                    passphrase="",
                )

                result = cmd.handle(args)
                assert result == 2  # EXIT_VALIDATION_ERROR

                # Check that error message was printed
                error_printed = any(
                    "Invalid master mnemonic" in str(call)
                    for call in mock_print.call_args_list
                )
                assert error_printed

    def test_unknown_application(self):
        """Test handling of unknown application."""
        cmd = Bip85Command()

        with patch(
            "sseed.file_operations.read_from_stdin",
            return_value=generate_mnemonic(Bip39Languages.ENGLISH),
        ):
            with patch("builtins.print"):
                args = argparse.Namespace(
                    application="unknown", input=None, output=None
                )

                result = cmd.handle(args)
                assert result == 2  # EXIT_VALIDATION_ERROR

    def test_metadata_generation(self):
        """Test metadata comment generation."""
        cmd = Bip85Command()

        # Test BIP39 metadata
        args = argparse.Namespace(
            application="bip39", words=24, language="es", index=5, passphrase="test"
        )
        metadata = cmd._generate_metadata_comment(args)
        assert "BIP85 BIP39 Generation" in metadata
        assert "Words: 24" in metadata
        assert "Language: es" in metadata
        assert "Index: 5" in metadata
        assert "Passphrase: yes" in metadata

        # Test hex metadata
        args = argparse.Namespace(
            application="hex", bytes=48, uppercase=True, index=10, passphrase=""
        )
        metadata = cmd._generate_metadata_comment(args)
        assert "BIP85 HEX Generation" in metadata
        assert "Bytes: 48" in metadata
        assert "Format: uppercase" in metadata
        assert "Index: 10" in metadata
        assert "Passphrase: no" in metadata

        # Test password metadata
        args = argparse.Namespace(
            application="password", length=30, charset="ascii", index=15, passphrase=""
        )
        metadata = cmd._generate_metadata_comment(args)
        assert "BIP85 PASSWORD Generation" in metadata
        assert "Length: 30" in metadata
        assert "Character Set: ascii" in metadata
        assert "Index: 15" in metadata


class TestBip85CliDeterministic:
    """Test BIP85 CLI deterministic behavior."""

    @pytest.fixture
    def master_mnemonic(self):
        """Generate a test master mnemonic."""
        return generate_mnemonic(Bip39Languages.ENGLISH)

    def test_deterministic_bip39_generation(self, master_mnemonic):
        """Test that same inputs produce same BIP39 output."""
        cmd = Bip85Command()
        results = []

        # Generate the same output twice
        for _ in range(2):
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="bip39",
                        input=None,
                        output=None,
                        words=15,
                        language="fr",
                        index=42,
                        passphrase="test123",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Extract output
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    results.append(output_calls[0])

        # Verify outputs are identical
        assert results[0] == results[1]

    def test_deterministic_hex_generation(self, master_mnemonic):
        """Test that same inputs produce same hex output."""
        cmd = Bip85Command()
        results = []

        # Generate the same output twice
        for _ in range(2):
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="hex",
                        input=None,
                        output=None,
                        bytes=24,
                        uppercase=True,
                        index=123,
                        passphrase="secret",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Extract output
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    results.append(output_calls[0])

        # Verify outputs are identical
        assert results[0] == results[1]

    def test_deterministic_password_generation(self, master_mnemonic):
        """Test that same inputs produce same password output."""
        cmd = Bip85Command()
        results = []

        # Generate the same output twice
        for _ in range(2):
            with patch(
                "sseed.file_operations.read_from_stdin", return_value=master_mnemonic
            ):
                with patch("builtins.print") as mock_print:
                    args = argparse.Namespace(
                        application="password",
                        input=None,
                        output=None,
                        length=35,
                        charset="base85",
                        index=999,
                        passphrase="complex_pass",
                    )

                    result = cmd.handle(args)
                    assert result == 0

                    # Extract output
                    output_calls = [
                        call[0][0] for call in mock_print.call_args_list if call[0]
                    ]
                    results.append(output_calls[0])

        # Verify outputs are identical
        assert results[0] == results[1]
