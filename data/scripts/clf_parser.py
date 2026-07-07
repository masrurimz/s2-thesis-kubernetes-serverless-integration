#!/usr/bin/env python3
"""
CLF (Combined Log Format) to RPS Time Series Converter.

Parses Apache/Nginx access logs and converts to requests-per-second time series
for training workload prediction models.

Dataset sources:
- ClarkNet: ftp://ita.ee.lbl.gov/traces/clarknet-http.gz
- Calgary: ftp://ita.ee.lbl.gov/traces/calgary-http.gz
"""

import gzip
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator, Tuple, Optional
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)

# CLF regex pattern
CLF_PATTERN = re.compile(
    r"^(\S+)\s+"  # host
    r"(\S+)\s+"  # ident
    r"(\S+)\s+"  # authuser
    r"\[([^\]]+)\]\s+"  # date
    r'"([^"]*)"?\s*'  # request
    r"(\d+|-)\s*"  # status
    r"(\d+|-)"  # bytes
)

# Date format in CLF
CLF_DATE_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_clf_line(line: str) -> Optional[Tuple[datetime, str, int, int]]:
    """Parse a single CLF line, return (timestamp, request, status, bytes)."""
    match = CLF_PATTERN.match(line)
    if not match:
        return None

    try:
        date_str = match.group(4)
        # Handle timezone offset format
        timestamp = datetime.strptime(date_str, CLF_DATE_FORMAT)
        request = match.group(5)
        status = int(match.group(6)) if match.group(6) != "-" else 0
        bytes_sent = int(match.group(7)) if match.group(7) != "-" else 0
        return (timestamp, request, status, bytes_sent)
    except (ValueError, IndexError):
        return None


def parse_clf_file(filepath: Path) -> Iterator[Tuple[datetime, str, int, int]]:
    """Parse CLF file (supports .gz compression)."""
    open_func = gzip.open if str(filepath).endswith(".gz") else open
    mode = "rt" if str(filepath).endswith(".gz") else "r"

    with open_func(filepath, mode, encoding="latin-1", errors="replace") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.decode("latin-1", errors="replace") if isinstance(line, bytes) else line
            result = parse_clf_line(line_str.strip())
            if result:
                yield result
            elif line_num <= 10:  # Log first few failures for debugging
                logger.debug("Failed to parse line", line_num=line_num)


def clf_to_rps(filepath: Path, resolution_seconds: int = 1, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Convert CLF log file to RPS time series.

    Args:
        filepath: Path to CLF log file
        resolution_seconds: Time bucket size (default 1 second)
        output_path: Optional path to save CSV output

    Returns:
        DataFrame with columns: timestamp, rps, total_bytes, avg_status
    """
    logger.info("Parsing CLF file", filepath=str(filepath))

    # Collect all entries
    entries = list(parse_clf_file(filepath))
    if not entries:
        logger.error("No valid entries found")
        return pd.DataFrame()

    logger.info("Parsed entries", count=len(entries))

    # Create DataFrame
    df = pd.DataFrame(entries, columns=["timestamp", "request", "status", "bytes"])

    # Floor timestamps to resolution
    df["bucket"] = df["timestamp"].dt.floor(f"{resolution_seconds}s")

    # Aggregate by time bucket
    rps_df = (
        df.groupby("bucket")
        .agg(
            rps=("request", "count"),
            total_bytes=("bytes", "sum"),
            avg_status=("status", "mean"),
            error_count=("status", lambda x: (x >= 400).sum()),
        )
        .reset_index()
    )

    rps_df.rename(columns={"bucket": "timestamp"}, inplace=True)

    # Fill missing time buckets with zeros
    full_range = pd.date_range(
        start=rps_df["timestamp"].min(), end=rps_df["timestamp"].max(), freq=f"{resolution_seconds}s"
    )
    rps_df = rps_df.set_index("timestamp").reindex(full_range, fill_value=0).reset_index()
    rps_df.rename(columns={"index": "timestamp"}, inplace=True)

    logger.info(
        "Generated RPS series",
        duration_hours=(rps_df["timestamp"].max() - rps_df["timestamp"].min()).total_seconds() / 3600,
        max_rps=rps_df["rps"].max(),
        avg_rps=rps_df["rps"].mean(),
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rps_df.to_csv(output_path, index=False)
        logger.info("Saved to CSV", path=str(output_path))

    return rps_df


def create_train_val_test_split(
    df: pd.DataFrame, train_ratio: float = 0.7, val_ratio: float = 0.15, output_dir: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split time series into train/val/test sets (temporal split, no shuffling).

    Args:
        df: RPS DataFrame
        train_ratio: Training set ratio
        val_ratio: Validation set ratio (test = 1 - train - val)
        output_dir: Directory to save split files

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()

    logger.info("Created splits", train_size=len(train_df), val_size=len(val_df), test_size=len(test_df))

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        train_df.to_csv(output_dir / "train.csv", index=False)
        val_df.to_csv(output_dir / "val.csv", index=False)
        test_df.to_csv(output_dir / "test.csv", index=False)
        logger.info("Saved splits", output_dir=str(output_dir))

    return train_df, val_df, test_df


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert CLF logs to RPS time series")
    parser.add_argument("input", type=Path, help="Input CLF file (.log or .gz)")
    parser.add_argument("-o", "--output", type=Path, help="Output CSV path")
    parser.add_argument("-r", "--resolution", type=int, default=1, help="Time resolution in seconds")
    parser.add_argument("--split", action="store_true", help="Create train/val/test splits")
    parser.add_argument("--split-dir", type=Path, help="Directory for split files")

    args = parser.parse_args()

    rps_df = clf_to_rps(args.input, args.resolution, args.output)

    if args.split and len(rps_df) > 0:
        split_dir = args.split_dir or args.input.parent / "splits"
        create_train_val_test_split(rps_df, output_dir=split_dir)

    print(f"Processed {len(rps_df)} time points")
    print(f"Max RPS: {rps_df['rps'].max():.0f}")
    print(f"Avg RPS: {rps_df['rps'].mean():.1f}")


if __name__ == "__main__":
    main()
