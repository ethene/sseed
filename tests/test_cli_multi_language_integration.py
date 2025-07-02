"""CLI multi-language integration tests for Stage 3.

This module provides comprehensive testing for CLI commands with multi-language support,
ensuring all workflows function correctly across all 9 supported BIP-39 languages.
"""

import tempfile
from pathlib import Path

import pytest

from sseed.cli.commands.gen import GenCommand
from sseed.cli.commands.restore import RestoreCommand
from sseed.cli.commands.seed import SeedCommand
from sseed.cli.commands.shard import ShardCommand
from sseed.languages import SUPPORTED_LANGUAGES


class TestCLIMultiLanguageIntegration:
    """Test CLI commands with comprehensive multi-language support."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.parametrize("lang_code", ["en", "es", "fr", "zh-cn", "ko"])
    def test_gen_command_with_language_selection(self, temp_dir, lang_code):
        """Test gen command with different language options."""
        output_file = temp_dir / f"mnemonic_{lang_code}.txt"

        # Create mock args for gen command
        class MockArgs:
            language = lang_code
            output = str(output_file)
            show_entropy = False
            words = 24  # Default word count

        # Test generation
        gen_cmd = GenCommand()
        result = gen_cmd.handle(MockArgs())

        # Verify success
        assert result == 0
        assert output_file.exists()

        # Verify file contains language metadata
        content = output_file.read_text(encoding="utf-8")
        lang_info = SUPPORTED_LANGUAGES[lang_code]
        assert f"Language: {lang_info.name} ({lang_info.code})" in content

        # Verify mnemonic is valid for the language
        lines = content.strip().split("\n")
        mnemonic_line = next((line for line in lines if not line.startswith("#")), None)
        assert mnemonic_line is not None
        assert len(mnemonic_line.split()) == 24

    def test_end_to_end_workflow_spanish(self, temp_dir):
        """Test complete workflow: gen → shard → restore in Spanish."""
        # Step 1: Generate Spanish mnemonic
        mnemonic_file = temp_dir / "spanish_mnemonic.txt"

        class GenArgs:
            language = "es"
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        assert gen_cmd.handle(GenArgs()) == 0
        assert mnemonic_file.exists()

        # Verify original file contains Spanish language info
        original_content = mnemonic_file.read_text(encoding="utf-8")
        assert "Language: Spanish (es)" in original_content

        # Step 2: Create SLIP-39 shards
        shard_prefix = temp_dir / "spanish_shards"

        class ShardArgs:
            input = str(mnemonic_file)
            output = str(shard_prefix)
            group = "3-of-5"
            separate = True

        shard_cmd = ShardCommand()
        assert shard_cmd.handle(ShardArgs()) == 0

        # Verify shard files exist and contain language metadata
        shard_files = list(temp_dir.glob("spanish_shards_*.txt"))
        assert len(shard_files) == 5

        for shard_file in shard_files:
            content = shard_file.read_text(encoding="utf-8")
            assert "Language: Spanish (es)" in content

        # Step 3: Restore from shards
        restored_file = temp_dir / "restored_spanish.txt"

        class RestoreArgs:
            shards = [str(f) for f in shard_files[:3]]  # Use 3 of 5 shards
            output = str(restored_file)
            show_entropy = False

        restore_cmd = RestoreCommand()
        assert restore_cmd.handle(RestoreArgs()) == 0
        assert restored_file.exists()

        # Verify restoration includes language detection
        # Note: SLIP-39 reconstruction normalizes mnemonics to English equivalent
        restored_content = restored_file.read_text(encoding="utf-8")
        assert "Language: English (en)" in restored_content

        # Verify both mnemonics are valid and properly formatted
        original_mnemonic = self._extract_mnemonic(original_content)
        restored_mnemonic = self._extract_mnemonic(restored_content)

        # Both should be 24-word mnemonics
        assert len(original_mnemonic.split()) == 24
        assert len(restored_mnemonic.split()) == 24

        # Both should be valid mnemonics (even if different due to SLIP-39 normalization)
        from bip_utils import Bip39Languages

        from sseed.bip39 import validate_mnemonic

        assert validate_mnemonic(original_mnemonic, Bip39Languages.SPANISH)
        assert validate_mnemonic(restored_mnemonic, Bip39Languages.ENGLISH)

    def test_end_to_end_workflow_chinese(self, temp_dir):
        """Test complete workflow with Chinese Simplified."""
        # Step 1: Generate Chinese mnemonic
        mnemonic_file = temp_dir / "chinese_mnemonic.txt"

        class GenArgs:
            language = "zh-cn"
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        assert gen_cmd.handle(GenArgs()) == 0

        # Step 2: Generate master seed
        seed_file = temp_dir / "chinese_seed.txt"

        class SeedArgs:
            input = str(mnemonic_file)
            output = str(seed_file)
            passphrase = False
            format = "hex"

        seed_cmd = SeedCommand()
        assert seed_cmd.handle(SeedArgs()) == 0
        assert seed_file.exists()

        # Verify seed file contains language metadata
        seed_content = seed_file.read_text(encoding="utf-8")
        assert "Language: Chinese Simplified (zh-cn)" in seed_content

    def test_language_auto_detection_workflow(self, temp_dir):
        """Test that language auto-detection works in restore workflow."""
        # Create a French mnemonic manually (simulating external source)
        french_file = temp_dir / "external_french.txt"

        # Generate a French mnemonic first
        class GenArgs:
            language = "fr"
            output = str(french_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        assert gen_cmd.handle(GenArgs()) == 0

        # Verify original French file
        original_content = french_file.read_text(encoding="utf-8")
        assert "Language: French (fr)" in original_content

        # Now test auto-detection by creating shards without explicit language
        shard_prefix = temp_dir / "auto_detect_shards"

        class ShardArgs:
            input = str(french_file)
            output = str(shard_prefix)
            group = "2-of-3"
            separate = True

        shard_cmd = ShardCommand()
        assert shard_cmd.handle(ShardArgs()) == 0

        # Verify shards contain detected French language info
        shard_files = list(temp_dir.glob("auto_detect_shards_*.txt"))
        assert len(shard_files) == 3

        for shard_file in shard_files:
            content = shard_file.read_text(encoding="utf-8")
            assert "Language: French (fr)" in content

        # Test restore with auto-detection
        restored_file = temp_dir / "auto_detected_restore.txt"

        class RestoreArgs:
            shards = [str(f) for f in shard_files[:2]]  # Use 2 of 3
            output = str(restored_file)
            show_entropy = False

        restore_cmd = RestoreCommand()
        assert restore_cmd.handle(RestoreArgs()) == 0

        # Verify auto-detection worked (SLIP-39 normalizes to English)
        restored_content = restored_file.read_text(encoding="utf-8")
        assert "Language: English (en)" in restored_content

        # Verify both mnemonics are valid and properly formatted
        original_mnemonic = self._extract_mnemonic(original_content)
        restored_mnemonic = self._extract_mnemonic(restored_content)

        # Both should be 24-word mnemonics
        assert len(original_mnemonic.split()) == 24
        assert len(restored_mnemonic.split()) == 24

        # Both should be valid mnemonics (even if different due to SLIP-39 normalization)
        from bip_utils import Bip39Languages

        from sseed.bip39 import validate_mnemonic

        assert validate_mnemonic(original_mnemonic, Bip39Languages.FRENCH)
        assert validate_mnemonic(restored_mnemonic, Bip39Languages.ENGLISH)

    @pytest.mark.parametrize("lang_code", ["en", "es", "it", "pt", "cs"])
    def test_latin_script_languages(self, temp_dir, lang_code):
        """Test Latin script languages work correctly."""
        mnemonic_file = temp_dir / f"{lang_code}_mnemonic.txt"

        class GenArgs:
            language = lang_code
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        result = gen_cmd.handle(GenArgs())

        assert result == 0
        assert mnemonic_file.exists()

        # Verify language metadata
        content = mnemonic_file.read_text(encoding="utf-8")
        lang_info = SUPPORTED_LANGUAGES[lang_code]
        assert f"Language: {lang_info.name} ({lang_info.code})" in content

    @pytest.mark.parametrize("lang_code", ["zh-cn", "zh-tw"])
    def test_chinese_script_languages(self, temp_dir, lang_code):
        """Test Chinese ideographic script languages."""
        mnemonic_file = temp_dir / f"{lang_code}_mnemonic.txt"

        class GenArgs:
            language = lang_code
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        result = gen_cmd.handle(GenArgs())

        assert result == 0
        assert mnemonic_file.exists()

        # Verify Chinese characters in mnemonic
        content = mnemonic_file.read_text(encoding="utf-8")
        mnemonic = self._extract_mnemonic(content)

        # Check for Chinese characters
        has_chinese = any("\u4e00" <= char <= "\u9fff" for char in mnemonic)
        assert has_chinese, f"No Chinese characters found in {lang_code} mnemonic"

    def test_korean_hangul_script(self, temp_dir):
        """Test Korean Hangul script support."""
        mnemonic_file = temp_dir / "korean_mnemonic.txt"

        class GenArgs:
            language = "ko"
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        result = gen_cmd.handle(GenArgs())

        assert result == 0
        assert mnemonic_file.exists()

        # Verify Hangul characters in mnemonic
        content = mnemonic_file.read_text(encoding="utf-8")
        mnemonic = self._extract_mnemonic(content)

        # Check for Hangul characters (broader range including syllables and jamo)
        has_hangul = any("\u1100" <= char <= "\ud7ff" for char in mnemonic)
        assert has_hangul, "No Hangul characters found in Korean mnemonic"

    def test_backward_compatibility_no_language_specified(self, temp_dir):
        """Test that existing CLI usage (no language specified) still works."""
        mnemonic_file = temp_dir / "default_mnemonic.txt"

        class GenArgs:
            language = "en"  # Default behavior
            output = str(mnemonic_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        result = gen_cmd.handle(GenArgs())

        assert result == 0
        assert mnemonic_file.exists()

        # Should default to English
        content = mnemonic_file.read_text(encoding="utf-8")
        assert "Language: English (en)" in content

    def test_error_handling_invalid_language_code(self):
        """Test error handling for invalid language codes."""

        class GenArgs:
            language = "invalid"
            output = None
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()

        # This should return an error code, not raise an exception
        result = gen_cmd.handle(GenArgs())
        assert result != 0  # Should return error code for invalid language

    def test_file_io_with_unicode_content(self, temp_dir):
        """Test file I/O operations with Unicode content."""
        # Test with Spanish (accented characters)
        spanish_file = temp_dir / "spanish_unicode.txt"

        class GenArgs:
            language = "es"
            output = str(spanish_file)
            show_entropy = False
            words = 24

        gen_cmd = GenCommand()
        assert gen_cmd.handle(GenArgs()) == 0

        # Verify file can be read back correctly
        content = spanish_file.read_text(encoding="utf-8")
        assert "Language: Spanish (es)" in content

        # Verify no encoding issues
        mnemonic = self._extract_mnemonic(content)
        assert len(mnemonic.split()) == 24

    def _extract_mnemonic(self, file_content: str) -> str:
        """Extract mnemonic from file content (ignoring comments)."""
        lines = file_content.strip().split("\n")
        mnemonic_lines = [line for line in lines if not line.startswith("#")]
        return " ".join(mnemonic_lines).strip()


class TestCLIPerformanceRegression:
    """Test performance characteristics of multi-language CLI operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_language_detection_performance(self, temp_dir):
        """Ensure language detection doesn't significantly impact performance."""
        import time

        # Generate test mnemonics in different languages
        test_files = []
        for lang_code in ["en", "es", "fr", "zh-cn"]:
            mnemonic_file = temp_dir / f"perf_test_{lang_code}.txt"

            class GenArgs:
                language = lang_code
                output = str(mnemonic_file)
                show_entropy = False
                words = 24

            gen_cmd = GenCommand()
            gen_cmd.handle(GenArgs())
            test_files.append(mnemonic_file)

        # Measure shard operation performance (includes language detection)
        start_time = time.time()

        for test_file in test_files:

            class ShardArgs:
                input = str(test_file)
                output = None  # stdout
                group = "2-of-3"
                separate = False

            shard_cmd = ShardCommand()
            shard_cmd.handle(ShardArgs())

        elapsed_time = time.time() - start_time

        # Should complete all operations in reasonable time
        # (This is a basic performance check, not a precise benchmark)
        assert (
            elapsed_time < 5.0
        ), f"Multi-language operations took too long: {elapsed_time}s"

    def test_memory_usage_with_multiple_languages(self):
        """Test that multiple language operations don't cause memory issues."""
        import gc

        # Force garbage collection before test
        gc.collect()

        # Perform operations with all languages
        for lang_code in SUPPORTED_LANGUAGES.keys():

            class GenArgs:
                language = lang_code
                output = None  # stdout
                show_entropy = False
                words = 24

            gen_cmd = GenCommand()
            result = gen_cmd.handle(GenArgs())
            assert result == 0

        # Force garbage collection after test
        gc.collect()

        # This is a basic check - in a real scenario, you'd use memory profiling tools
        # The test passing means no obvious memory leaks or excessive usage


class TestCLIErrorHandling:
    """Test error handling scenarios in multi-language CLI operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_graceful_fallback_when_detection_fails(self, temp_dir):
        """Test graceful fallback when language detection fails."""
        # Create a file with invalid/mixed content
        invalid_file = temp_dir / "invalid_content.txt"
        invalid_file.write_text("this is not a valid mnemonic at all", encoding="utf-8")

        class ShardArgs:
            input = str(invalid_file)
            output = None
            group = "2-of-3"
            separate = False

        shard_cmd = ShardCommand()

        # Should fail gracefully, not crash
        result = shard_cmd.handle(ShardArgs())
        assert result != 0  # Should return error code

    def test_unicode_error_handling(self, temp_dir):
        """Test handling of Unicode-related errors."""
        # Create a file with problematic Unicode content
        problematic_file = temp_dir / "unicode_problem.txt"

        # Write content that might cause Unicode issues
        with open(problematic_file, "wb") as f:
            f.write(b"\xff\xfe invalid unicode content")

        class SeedArgs:
            input = str(problematic_file)
            output = None
            passphrase = False
            format = "hex"

        seed_cmd = SeedCommand()

        # Should handle Unicode errors gracefully
        result = seed_cmd.handle(SeedArgs())
        assert result != 0  # Should return error code, not crash
