#!/usr/bin/env bash
set -e

TYPE=${1:-all}
RAW_DIR="$(dirname "$0")/../../data/raw"
API_URL="http://localhost:8001/ingest"

ingest_dir() {
  local dir=$1
  echo "Ingesting files in $dir..."
  find "$dir" -type f | while read -r file; do
    echo "  -> $(basename "$file")"
    curl -s -X POST "$API_URL" \
      -F "file=@$file" \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'     {d[\"chunks_indexed\"]} chunks')"
  done
}

case $TYPE in
  pdf)      ingest_dir "$RAW_DIR/pdf" ;;
  markdown) ingest_dir "$RAW_DIR/markdown" ;;
  all)
    ingest_dir "$RAW_DIR/pdf"
    ingest_dir "$RAW_DIR/markdown"
    ;;
  *)
    echo "Usage: $0 [pdf|markdown|all]"
    exit 1
    ;;
esac

echo "Done."
