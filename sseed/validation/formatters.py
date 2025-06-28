"""Output formatters for validation results.

This module provides multiple output format support for validation results
including human-readable text, structured JSON, and batch summaries.
"""

import json
import logging
from typing import (
    Any,
    Dict,
)

logger = logging.getLogger(__name__)


class ValidationFormatter:
    """Multiple output format support for validation results."""

    # ANSI color codes for terminal output
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }

    # Status symbols
    SYMBOLS = {
        "pass": "✅",
        "fail": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "excellent": "🌟",
        "good": "✅",
        "acceptable": "⚡",
        "poor": "⚠️",
        "error": "❌",
    }

    @classmethod
    def format_text(
        cls,
        results: Dict[str, Any],
        verbose: bool = False,
        use_colors: bool = True,
        use_symbols: bool = True,
    ) -> str:
        """Format validation results as human-readable text.

        Args:
            results: Validation results dictionary
            verbose: Include detailed information
            use_colors: Use ANSI color codes
            use_symbols: Use Unicode symbols

        Returns:
            Formatted text string
        """
        lines = []

        # Helper functions
        def colorize(text: str, color: str) -> str:
            if not use_colors:
                return text
            return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

        def symbolize(status: str) -> str:
            if not use_symbols:
                return status.upper()
            return cls.SYMBOLS.get(status, status)

        # Check if this is a batch result
        if "summary" in results:
            return cls._format_batch_text(results, verbose, use_colors, use_symbols)

        # Single validation result
        overall_score = results.get("overall_score", 0)
        overall_status = results.get("overall_status", "unknown")

        # Header
        status_symbol = symbolize(cls._get_quality_level(overall_score))
        status_color = cls._get_status_color(overall_status)

        lines.append(colorize("🔍 Mnemonic Validation Report", "bold"))
        lines.append("=" * 40)
        lines.append(
            f"{status_symbol} Overall Score: {colorize(str(overall_score), status_color)}/100"
        )
        lines.append(f"Status: {colorize(overall_status.title(), status_color)}")

        if results.get("timestamp"):
            lines.append(f"Analyzed: {results['timestamp']}")

        if results.get("analysis_duration_ms"):
            lines.append(f"Duration: {results['analysis_duration_ms']:.1f}ms")

        lines.append("")

        # Validation checks
        checks = results.get("checks", {})
        if checks:
            lines.append(colorize("📋 Validation Checks:", "bold"))
            lines.append("-" * 20)

            for check_name, check_data in checks.items():
                if not isinstance(check_data, dict):
                    continue

                status = check_data.get("status", "unknown")
                symbol = symbolize(status)
                color = "green" if status == "pass" else "red"

                check_title = check_name.replace("_", " ").title()
                lines.append(f"{symbol} {colorize(check_title, color)}")

                if verbose and check_data.get("message"):
                    lines.append(f"   {check_data['message']}")

                if verbose and check_data.get("details"):
                    for key, value in check_data["details"].items():
                        if isinstance(value, (str, int, float, bool)):
                            lines.append(f"   {key}: {value}")

            lines.append("")

        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            lines.append(colorize("⚠️  Warnings:", "yellow"))
            for warning in warnings:
                lines.append(f"   • {warning}")
            lines.append("")

        # Recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            lines.append(colorize("💡 Recommendations:", "cyan"))
            for rec in recommendations:
                lines.append(f"   • {rec}")
            lines.append("")

        # Security notes
        security_notes = results.get("security_notes", [])
        if security_notes:
            lines.append(colorize("🔒 Security Notes:", "magenta"))
            for note in security_notes:
                lines.append(f"   • {note}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def format_json(
        cls,
        results: Dict[str, Any],
        pretty: bool = True,
        compact: bool = False,
    ) -> str:
        """Format validation results as JSON.

        Args:
            results: Validation results dictionary
            pretty: Use pretty printing with indentation
            compact: Use compact format (overrides pretty)

        Returns:
            JSON string
        """
        if compact:
            return json.dumps(results, separators=(",", ":"))
        elif pretty:
            return json.dumps(results, indent=2, sort_keys=True)
        else:
            return json.dumps(results)

    @classmethod
    def format_summary(
        cls,
        results: Dict[str, Any],
        use_colors: bool = True,
        use_symbols: bool = True,
    ) -> str:
        """Format validation results as a summary.

        Args:
            results: Validation results dictionary
            use_colors: Use ANSI color codes
            use_symbols: Use Unicode symbols

        Returns:
            Summary string
        """

        def colorize(text: str, color: str) -> str:
            if not use_colors:
                return text
            return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

        def symbolize(status: str) -> str:
            if not use_symbols:
                return status.upper()
            return cls.SYMBOLS.get(status, status)

        # Check if this is a batch result
        if "summary" in results:
            summary = results["summary"]
            success_rate = summary.get("success_rate", 0)

            status_color = (
                "green"
                if success_rate >= 90
                else "yellow" if success_rate >= 70 else "red"
            )
            symbol = symbolize(
                "pass"
                if success_rate >= 90
                else "warning" if success_rate >= 70 else "fail"
            )

            # Format file counts to avoid f-string quote conflicts
            passed_files = summary.get("passed_files", 0)
            total_files = summary.get("total_files", 0)
            file_ratio = f"{passed_files}/{total_files}"
            success_percent = f"{success_rate:.1f}%"

            return (
                f"{symbol} Batch Validation: "
                f"{colorize(file_ratio, status_color)} "
                f"passed ({colorize(success_percent, status_color)} success rate)"
            )
        else:
            # Single validation result
            overall_score = results.get("overall_score", 0)
            overall_status = results.get("overall_status", "unknown")

            status_symbol = symbolize(cls._get_quality_level(overall_score))
            status_color = cls._get_status_color(overall_status)

            return (
                f"{status_symbol} Score: {colorize(str(overall_score), status_color)}/100 "
                f"({colorize(overall_status.title(), status_color)})"
            )

    @classmethod
    def _format_batch_text(
        cls,
        results: Dict[str, Any],
        verbose: bool = False,
        use_colors: bool = True,
        use_symbols: bool = True,
    ) -> str:
        """Format batch validation results as text."""
        lines = []

        def colorize(text: str, color: str) -> str:
            if not use_colors:
                return text
            return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

        def symbolize(status: str) -> str:
            if not use_symbols:
                return status.upper()
            return cls.SYMBOLS.get(status, status)

        summary = results.get("summary", {})
        statistics = results.get("statistics", {})
        file_results = results.get("file_results", [])
        errors = results.get("errors", [])

        # Header
        lines.append(colorize("📊 Batch Validation Report", "bold"))
        lines.append("=" * 50)

        # Summary statistics
        total_files = summary.get("total_files", 0)
        _processed_files = summary.get("processed_files", 0)
        passed_files = summary.get("passed_files", 0)
        failed_files = summary.get("failed_files", 0)
        error_files = summary.get("error_files", 0)
        success_rate = summary.get("success_rate", 0)

        status_color = (
            "green" if success_rate >= 90 else "yellow" if success_rate >= 70 else "red"
        )
        status_symbol = symbolize(
            "pass"
            if success_rate >= 90
            else "warning" if success_rate >= 70 else "fail"
        )

        lines.append(
            f"{status_symbol} Overall Success Rate: {colorize(f'{success_rate:.1f}%', status_color)}"
        )
        lines.append(f"📁 Total Files: {total_files}")
        lines.append(f"✅ Passed: {colorize(str(passed_files), 'green')}")
        lines.append(f"❌ Failed: {colorize(str(failed_files), 'red')}")

        if error_files > 0:
            lines.append(f"🚫 Errors: {colorize(str(error_files), 'red')}")

        if summary.get("average_score"):
            lines.append(f"📈 Average Score: {summary['average_score']:.1f}/100")

        if summary.get("total_duration_ms"):
            lines.append(f"⏱️  Total Duration: {summary['total_duration_ms']:.1f}ms")

        lines.append("")

        # Quality distribution
        if statistics.get("quality_distribution"):
            lines.append(colorize("📊 Quality Distribution:", "bold"))
            quality_dist = statistics["quality_distribution"]

            for quality, count in quality_dist.items():
                if count > 0:
                    symbol = symbolize(quality)
                    color = cls._get_quality_color(quality)
                    lines.append(
                        f"   {symbol} {quality.title()}: {colorize(str(count), color)}"
                    )

            lines.append("")

        # Language distribution
        if statistics.get("language_distribution"):
            lines.append(colorize("🌐 Language Distribution:", "bold"))
            for lang, count in statistics["language_distribution"].items():
                lines.append(f"   {lang}: {count}")
            lines.append("")

        # Word count distribution
        if statistics.get("word_count_distribution"):
            lines.append(colorize("📝 Word Count Distribution:", "bold"))
            for count, files in statistics["word_count_distribution"].items():
                lines.append(f"   {count} words: {files} files")
            lines.append("")

        # Errors summary
        if errors and verbose:
            lines.append(colorize("🚫 Errors:", "red"))
            for error in errors[:10]:  # Show first 10 errors
                lines.append(f"   {error['file_name']}: {error['error']}")
            if len(errors) > 10:
                lines.append(f"   ... and {len(errors) - 10} more errors")
            lines.append("")

        # Individual file results (if verbose and not too many)
        if verbose and file_results and len(file_results) <= 20:
            lines.append(colorize("📋 Individual Results:", "bold"))
            for result in file_results:
                file_name = result["file_name"]
                analysis = result["analysis"]
                score = analysis.get("overall_score", 0)
                status = analysis.get("overall_status", "unknown")

                symbol = symbolize(cls._get_quality_level(score))
                color = cls._get_status_color(status)

                lines.append(
                    f"   {symbol} {file_name}: {colorize(str(score), color)}/100"
                )

        return "\n".join(lines)

    @classmethod
    def _get_quality_level(cls, score: int) -> str:
        """Get quality level from score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "acceptable"
        elif score >= 50:
            return "poor"
        else:
            return "fail"

    @classmethod
    def _get_status_color(cls, status: str) -> str:
        """Get color for status."""
        if status in ["pass", "excellent", "good"]:
            return "green"
        elif status in ["acceptable", "warning"]:
            return "yellow"
        elif status in ["poor", "fail", "error"]:
            return "red"
        else:
            return "white"

    @classmethod
    def _get_quality_color(cls, quality: str) -> str:
        """Get color for quality level."""
        if quality in ["excellent"]:
            return "green"
        elif quality in ["good"]:
            return "cyan"
        elif quality in ["acceptable"]:
            return "yellow"
        elif quality in ["poor"]:
            return "magenta"
        else:
            return "red"


def format_validation_output(
    results: Dict[str, Any],
    output_format: str = "text",
    verbose: bool = False,
    use_colors: bool = True,
    use_symbols: bool = True,
    pretty_json: bool = True,
) -> str:
    """Format validation output in the specified format.

    Args:
        results: Validation results dictionary
        output_format: Output format ("text", "json", "summary")
        verbose: Include detailed information
        use_colors: Use ANSI color codes
        use_symbols: Use Unicode symbols
        pretty_json: Use pretty JSON formatting

    Returns:
        Formatted output string
    """
    formatter = ValidationFormatter()

    if output_format == "json":
        return formatter.format_json(results, pretty=pretty_json)
    elif output_format == "summary":
        return formatter.format_summary(
            results, use_colors=use_colors, use_symbols=use_symbols
        )
    else:  # text
        return formatter.format_text(
            results, verbose=verbose, use_colors=use_colors, use_symbols=use_symbols
        )
