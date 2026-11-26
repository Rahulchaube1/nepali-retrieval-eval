"""Command-line entry points; no network access or external runtime packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import DataError, load_dataset
from .evaluation import report_header, run_baseline
from .retrieval import BASELINES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independent retrieval evaluation with explicit provenance gates")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        command = commands.add_parser(name)
        command.add_argument("--data-dir", type=Path, required=True)
        command.add_argument("--mode", choices=("smoke", "benchmark"), required=True)
        if name == "run":
            command.add_argument("--baseline", choices=BASELINES, required=True)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        dataset = load_dataset(args.data_dir, args.mode)
        if args.command == "validate":
            report = report_header(dataset)
            report["validation"] = "passed"
            print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        else:
            report = run_baseline(dataset, args.baseline)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({
                "output": str(args.output), "mode": report["mode"],
                "status": report["status"], "metrics": report["metrics"],
            }, ensure_ascii=False, indent=2, allow_nan=False))
    except (DataError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
