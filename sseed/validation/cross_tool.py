"""Cross-tool compatibility validation for mnemonic testing.

This module provides functionality to test mnemonic compatibility across
different tools and implementations, ensuring cross-platform compatibility.
"""

import logging
import os
import subprocess
import tempfile
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

from ..bip39 import get_mnemonic_entropy

logger = logging.getLogger(__name__)


class CrossToolCompatibilityResult:
    """Results of cross-tool compatibility testing."""

    def __init__(self) -> None:
        self.overall_status: str = "unknown"
        self.timestamp: str = ""
        self.tools_tested: List[str] = []
        self.compatibility_score: int = 0

        # Test results for each tool
        self.tool_results: Dict[str, Dict[str, Any]] = {}

        # Issues and recommendations
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "overall_status": self.overall_status,
            "timestamp": self.timestamp,
            "tools_tested": self.tools_tested,
            "compatibility_score": self.compatibility_score,
            "tool_results": self.tool_results,
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }

    def is_compatible(self) -> bool:
        """Check if mnemonic is compatible with tested tools."""
        return self.compatibility_score >= 80 and self.overall_status != "fail"


class CrossToolTester:
    """Framework for testing external tool compatibility."""

    def __init__(self) -> None:
        self.available_tools = self._detect_available_tools()
        logger.info(f"Detected available tools: {list(self.available_tools.keys())}")

    def test_compatibility(self, mnemonic: str) -> CrossToolCompatibilityResult:
        """Test mnemonic compatibility with available external tools.

        Args:
            mnemonic: The mnemonic phrase to test

        Returns:
            CrossToolCompatibilityResult with compatibility analysis
        """
        result = CrossToolCompatibilityResult()
        result.timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        logger.info("Starting cross-tool compatibility testing")

        # Test with each available tool
        for tool_name, tool_info in self.available_tools.items():
            try:
                logger.info(f"Testing compatibility with {tool_name}")
                tool_result = self._test_tool_compatibility(
                    mnemonic, tool_name, tool_info
                )
                result.tool_results[tool_name] = tool_result
                result.tools_tested.append(tool_name)

                if tool_result.get("status") != "pass":
                    result.issues.append(
                        f"{tool_name}: {tool_result.get('message', 'Unknown issue')}"
                    )

            except Exception as e:
                logger.error(f"Error testing {tool_name}: {e}")
                result.tool_results[tool_name] = {
                    "status": "error",
                    "error": str(e),
                    "message": f"Testing failed: {str(e)}",
                }
                result.warnings.append(f"Could not test {tool_name}: {str(e)}")

        # Calculate overall compatibility
        self._calculate_compatibility_score(result)
        self._generate_recommendations(result)

        logger.info(
            "Cross-tool compatibility testing completed: score=%s, status=%s",
            result.compatibility_score,
            result.overall_status,
        )

        return result

    def _detect_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Detect available external tools for testing."""
        tools = {}

        # Test for Trezor shamir CLI
        if self._is_shamir_cli_available():
            tools["trezor_shamir"] = {
                "command": "shamir",
                "type": "shamir_cli",
                "description": "Official Trezor SLIP-39 CLI tool",
                "test_methods": ["slip39_round_trip", "entropy_verification"],
            }

        # Test for other tools (can be extended)
        # Example: Electrum, Bitcoin Core, etc.

        return tools

    def _is_shamir_cli_available(self) -> bool:
        """Check if the official Trezor shamir CLI tool is available."""
        try:
            returncode, stdout, _stderr = self._run_command("shamir --help")
            return returncode == 0 and "create" in stdout and "recover" in stdout
        except Exception:
            return False

    def _test_tool_compatibility(
        self, mnemonic: str, _tool_name: str, tool_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test compatibility with a specific tool."""
        if tool_info["type"] == "shamir_cli":
            return self._test_shamir_cli_compatibility(mnemonic, tool_info)
        else:
            return {
                "status": "unsupported",
                "message": f"Unsupported tool type: {tool_info['type']}",
            }

    def _test_shamir_cli_compatibility(
        self, mnemonic: str, _tool_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test compatibility with Trezor shamir CLI tool."""
        try:
            # Test 1: SLIP-39 round-trip compatibility
            round_trip_result = self._test_slip39_round_trip(mnemonic)

            # Test 2: Entropy verification
            entropy_result = self._test_entropy_verification(mnemonic)

            # Combine results
            if (
                round_trip_result["status"] == "pass"
                and entropy_result["status"] == "pass"
            ):
                return {
                    "status": "pass",
                    "message": "Full compatibility with Trezor shamir CLI",
                    "tests": {
                        "slip39_round_trip": round_trip_result,
                        "entropy_verification": entropy_result,
                    },
                }
            else:
                issues = []
                if round_trip_result["status"] != "pass":
                    issues.append(f"SLIP-39 round-trip: {round_trip_result['message']}")
                if entropy_result["status"] != "pass":
                    issues.append(f"Entropy verification: {entropy_result['message']}")

                return {
                    "status": "partial",
                    "message": f"Partial compatibility: {'; '.join(issues)}",
                    "tests": {
                        "slip39_round_trip": round_trip_result,
                        "entropy_verification": entropy_result,
                    },
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Testing failed: {str(e)}",
            }

    def _test_slip39_round_trip(self, mnemonic: str) -> Dict[str, Any]:
        """Test SLIP-39 round-trip compatibility: sseed shard → shamir recover."""
        temp_files = []

        try:
            # Create temporary mnemonic file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(mnemonic)
                mnemonic_file = f.name
            temp_files.append(mnemonic_file)

            # Extract original entropy for comparison
            original_entropy_bytes = get_mnemonic_entropy(mnemonic)
            original_entropy_hex = original_entropy_bytes.hex()

            # Create shards with sseed (use a secure temp directory)
            temp_dir = tempfile.mkdtemp(prefix="compat_test_")
            shard_prefix = os.path.join(temp_dir, "shards")
            temp_files.append(temp_dir)  # Will cleanup directory
            returncode, stdout, stderr = self._run_command(
                f"sseed shard -i {mnemonic_file} -g 2-of-3 --separate -o {shard_prefix}"
            )

            if returncode != 0:
                return {
                    "status": "fail",
                    "message": f"Failed to create shards with sseed: {stderr}",
                    "error": stderr,
                }

            # Read generated shards
            shard_files = [f"{shard_prefix}_{i:02d}.txt" for i in range(1, 4)]
            temp_files.extend(shard_files)

            shards = []
            for shard_file in shard_files:
                if os.path.exists(shard_file):
                    with open(shard_file, "r") as f:
                        shard_content = f.read().strip()
                        # Extract clean shard text (remove comments)
                        shard_lines = [
                            line.strip()
                            for line in shard_content.split("\n")
                            if line.strip() and not line.startswith("#")
                        ]
                        if shard_lines:
                            shards.append(" ".join(shard_lines))

            if len(shards) < 2:
                return {
                    "status": "fail",
                    "message": "Insufficient shards generated",
                    "shard_count": len(shards),
                }

            # Recover with shamir CLI (use first 2 shards)
            recovery_input = f"{shards[0]}\n{shards[1]}\n\n"
            returncode, stdout, stderr = self._run_command(
                "shamir recover", recovery_input
            )

            if returncode != 0:
                return {
                    "status": "fail",
                    "message": f"Shamir recovery failed: {stderr}",
                    "error": stderr,
                }

            # Extract recovered entropy
            recovered_entropy_hex = self._extract_entropy_from_shamir_output(stdout)

            if not recovered_entropy_hex:
                return {
                    "status": "fail",
                    "message": "Could not extract entropy from shamir output",
                    "output": stdout,
                }

            # Verify entropy match
            if recovered_entropy_hex.lower() == original_entropy_hex.lower():
                return {
                    "status": "pass",
                    "message": "Perfect SLIP-39 round-trip compatibility",
                    "original_entropy": original_entropy_hex,
                    "recovered_entropy": recovered_entropy_hex,
                    "shards_used": 2,
                    "shards_total": len(shards),
                }
            else:
                return {
                    "status": "fail",
                    "message": "Entropy mismatch in round-trip test",
                    "original_entropy": original_entropy_hex,
                    "recovered_entropy": recovered_entropy_hex,
                    "mismatch": True,
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Round-trip test failed: {str(e)}",
            }
        finally:
            # Cleanup temporary files and directories
            for temp_path in temp_files:
                try:
                    if os.path.exists(temp_path):
                        if os.path.isdir(temp_path):
                            import shutil

                            shutil.rmtree(temp_path)
                        else:
                            os.unlink(temp_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp path %s: %s", temp_path, e)

    def _test_entropy_verification(self, _mnemonic: str) -> Dict[str, Any]:
        """Test entropy verification: shamir create → sseed restore."""
        temp_files = []

        try:
            # Create shards with shamir
            returncode, stdout, stderr = self._run_command("shamir create 2of3")

            if returncode != 0:
                return {
                    "status": "fail",
                    "message": f"Shamir create failed: {stderr}",
                    "error": stderr,
                }

            # Parse shamir output
            lines = stdout.strip().split("\n")

            # Extract original entropy
            master_secret_lines = [
                line for line in lines if "Using master secret:" in line
            ]
            if not master_secret_lines:
                return {
                    "status": "fail",
                    "message": "Could not find master secret in shamir output",
                    "output": stdout,
                }

            original_entropy_hex = (
                master_secret_lines[0].split("Using master secret: ")[1].strip()
            )

            # Extract shards
            shard_lines = [
                line.strip()
                for line in lines
                if line.strip()
                and not line.startswith("Using")
                and not line.startswith("Group")
                and len(line.strip().split()) > 10
            ]

            if len(shard_lines) < 2:
                return {
                    "status": "fail",
                    "message": "Insufficient shards in shamir output",
                    "shard_count": len(shard_lines),
                }

            # Save shards to files for sseed
            shard_files = []
            for _i, shard in enumerate(shard_lines[:2]):  # Use first 2 shards
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as f:
                    f.write(shard)
                    shard_file = f.name
                temp_files.append(shard_file)
                shard_files.append(shard_file)

            # Restore with sseed
            returncode, stdout, stderr = self._run_command(
                f"sseed restore {' '.join(shard_files)}"
            )

            if returncode != 0:
                return {
                    "status": "fail",
                    "message": f"SSeed restore failed: {stderr}",
                    "error": stderr,
                }

            # Extract reconstructed mnemonic
            lines = stdout.strip().split("\n")
            mnemonic_lines = [
                line
                for line in lines
                if not line.startswith("2025-") and len(line.split()) >= 12
            ]

            if not mnemonic_lines:
                return {
                    "status": "fail",
                    "message": "Could not extract mnemonic from sseed output",
                    "output": stdout,
                }

            reconstructed_mnemonic = mnemonic_lines[0]

            # Convert back to entropy for comparison
            reconstructed_entropy_bytes = get_mnemonic_entropy(reconstructed_mnemonic)
            reconstructed_entropy_hex = reconstructed_entropy_bytes.hex()

            # Verify entropy match
            if reconstructed_entropy_hex.lower() == original_entropy_hex.lower():
                return {
                    "status": "pass",
                    "message": "Perfect entropy verification",
                    "original_entropy": original_entropy_hex,
                    "reconstructed_entropy": reconstructed_entropy_hex,
                    "reconstructed_mnemonic": reconstructed_mnemonic,
                }
            else:
                return {
                    "status": "fail",
                    "message": "Entropy mismatch in verification test",
                    "original_entropy": original_entropy_hex,
                    "reconstructed_entropy": reconstructed_entropy_hex,
                    "mismatch": True,
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Entropy verification test failed: {str(e)}",
            }
        finally:
            # Cleanup temporary files and directories
            for temp_path in temp_files:
                try:
                    if os.path.exists(temp_path):
                        if os.path.isdir(temp_path):
                            import shutil

                            shutil.rmtree(temp_path)
                        else:
                            os.unlink(temp_path)
                except Exception as e:
                    logger.warning("Failed to cleanup temp path %s: %s", temp_path, e)

    def _calculate_compatibility_score(
        self, result: CrossToolCompatibilityResult
    ) -> None:
        """Calculate overall compatibility score."""
        if not result.tools_tested:
            result.compatibility_score = 0
            result.overall_status = "no_tools"
            return

        total_score = 0
        max_score = 0

        for tool_name in result.tools_tested:
            tool_result = result.tool_results[tool_name]
            max_score += 100

            if tool_result["status"] == "pass":
                total_score += 100
            elif tool_result["status"] == "partial":
                total_score += 50
            elif tool_result["status"] == "error":
                total_score += 0
            else:  # fail
                total_score += 0

        result.compatibility_score = (
            int((total_score / max_score) * 100) if max_score > 0 else 0
        )

        # Determine overall status
        if result.compatibility_score >= 90:
            result.overall_status = "excellent"
        elif result.compatibility_score >= 80:
            result.overall_status = "good"
        elif result.compatibility_score >= 60:
            result.overall_status = "acceptable"
        elif result.compatibility_score >= 30:
            result.overall_status = "poor"
        else:
            result.overall_status = "fail"

    def _generate_recommendations(self, result: CrossToolCompatibilityResult) -> None:
        """Generate recommendations based on compatibility results."""
        recommendations = []

        if result.compatibility_score < 80:
            recommendations.append(
                "Mnemonic may not be fully compatible with external tools"
            )

        if not result.tools_tested:
            recommendations.append(
                "Install external tools for comprehensive compatibility testing"
            )
            recommendations.append(
                "Consider installing: pip install shamir-mnemonic[cli]"
            )

        failed_tools = [
            tool
            for tool, result_data in result.tool_results.items()
            if result_data["status"] in ["fail", "error"]
        ]

        if failed_tools:
            recommendations.append(
                f"Review compatibility issues with: {', '.join(failed_tools)}"
            )

        result.recommendations = recommendations

    def _run_command(
        self, cmd: str, input_text: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """Run a command and return the result."""
        try:
            # Split command to avoid shell=True security issue
            import shlex

            cmd_args = shlex.split(cmd)
            result = subprocess.run(
                cmd_args, capture_output=True, text=True, input=input_text
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)

    def _extract_entropy_from_shamir_output(self, stdout: str) -> str:
        """Extract hex entropy from shamir recover output."""
        lines = stdout.strip().split("\n")
        for line in lines:
            if "master secret is:" in line:
                return line.split("master secret is: ")[1].strip()
        return ""


def test_cross_tool_compatibility(mnemonic: str) -> Dict[str, Any]:
    """Public interface for cross-tool compatibility testing.

    Args:
        mnemonic: The mnemonic phrase to test

    Returns:
        Dictionary containing compatibility test results
    """
    tester = CrossToolTester()
    result = tester.test_compatibility(mnemonic)
    return result.to_dict()


def get_available_tools() -> List[str]:
    """Get list of available external tools for testing.

    Returns:
        List of available tool names
    """
    tester = CrossToolTester()
    return list(tester.available_tools.keys())


def is_tool_available(tool_name: str) -> bool:
    """Check if a specific tool is available for testing.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool is available, False otherwise
    """
    available_tools = get_available_tools()
    return tool_name in available_tools
