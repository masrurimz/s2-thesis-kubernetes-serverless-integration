#!/bin/bash
# Download ClarkNet and Calgary HTTP trace datasets

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAW_DIR="$SCRIPT_DIR/../raw"

mkdir -p "$RAW_DIR/clarknet" "$RAW_DIR/calgary"

echo "Downloading ClarkNet dataset..."
# Note: Original FTP may be unavailable, using archive.org mirror or placeholder
curl -L -o "$RAW_DIR/clarknet/clarknet-http.gz" \
  "https://web.archive.org/web/20230101000000/ftp://ita.ee.lbl.gov/traces/clarknet-http.gz" 2>/dev/null || \
  echo "ClarkNet download failed - create synthetic data for testing"

echo "Downloading Calgary dataset..."
curl -L -o "$RAW_DIR/calgary/calgary-http.gz" \
  "https://web.archive.org/web/20230101000000/ftp://ita.ee.lbl.gov/traces/calgary-http.gz" 2>/dev/null || \
  echo "Calgary download failed - create synthetic data for testing"

echo "Done. Check $RAW_DIR for downloaded files."
