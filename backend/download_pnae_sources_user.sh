#!/usr/bin/env bash
set -e

OUT_DIR=${1:-"./data/rag_documents"}
mkdir -p "$OUT_DIR"

CSV="pnae_rag_docs_cleaned.csv"

echo "Saving into $OUT_DIR"

tail -n +2 "$CSV" | while IFS=',' read -r title url type org status; do
  filename=$(echo "$title" | tr ' ' '_' | tr -cd '[:alnum:]_')
  outfile="$OUT_DIR/$filename"

  echo "Downloading: $title"

  curl -L \
    --retry 3 \
    --retry-delay 2 \
    --connect-timeout 15 \
    --max-time 60 \
    -A "Mozilla/5.0 (X11; Linux x86_64)" \
    "$url" \
    -o "$outfile"

done