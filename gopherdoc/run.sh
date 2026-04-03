#!/usr/bin/env bash
# gopherdoc/run.sh — Benchmark do GopherDoc
# Uso: ./gopherdoc/run.sh [CORPUS_DIR] [WORKERS] [LIMIT_BYTES]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORPUS_DIR="${1:-$REPO_ROOT/corpus}"
WORKERS="${2:-16}"
readonly CHUNK_SIZE=4096
readonly OVERLAP=512
LIMIT="${3:-10485760}"
GOPHERDOC_REPO="${GOPHERDOC_REPO:-$REPO_ROOT/gopherdoc/engine}"

RESULTS_FILE="$REPO_ROOT/results/results.md"

if ! command -v go &>/dev/null; then
  echo "ERROR: 'go' não encontrado no PATH." >&2
  exit 1
fi

if [[ ! -f "$GOPHERDOC_REPO/go.mod" ]]; then
  echo "ERROR: Submodule GopherDoc não inicializado em: $GOPHERDOC_REPO" >&2
  echo "       Execute: git submodule update --init --recursive" >&2
  exit 1
fi

if [[ ! -d "$CORPUS_DIR" ]] || [[ -z "$(ls -A "$CORPUS_DIR" 2>/dev/null)" ]]; then
  echo "ERROR: Corpus não encontrado ou vazio em: $CORPUS_DIR" >&2
  echo "       Execute ./gera_corpus.sh primeiro." >&2
  exit 1
fi

CORPUS_BYTES=$(du -sb "$CORPUS_DIR" | awk '{print $1}')
CORPUS_MB=$(echo "scale=2; $CORPUS_BYTES / 1048576" | bc)
FILE_COUNT=$(find "$CORPUS_DIR" -type f | wc -l | tr -d ' ')

echo "============================================================"
echo "  GopherDoc Benchmark"
echo "============================================================"
echo "  Corpus : $CORPUS_DIR"
printf "  Tamanho: %s MB (%s arquivos)\n" "$CORPUS_MB" "$FILE_COUNT"
echo "  Workers: $WORKERS"
echo "  Chunk  : ${CHUNK_SIZE} bytes | Overlap: ${OVERLAP} bytes"
echo "  Limit  : $LIMIT bytes por arquivo"
echo "============================================================"
echo ""

# Build fora do timer para não contaminar o wall time.
cd "$GOPHERDOC_REPO"
echo "  Compilando GopherDoc..."
go build -o /tmp/gopherdoc_bin ./cmd/gopherdoc
echo ""

# stderr captura gctrace + linha "done: N chunks, M errors".
STDERR_LOG=$(mktemp /tmp/gopherdoc_stderr.XXXXXX)
trap 'rm -f "$STDERR_LOG"' EXIT

# stdout (JSON chunks) descartado — apenas métricas importam.
START_NS=$(date +%s%N)

GODEBUG=gctrace=1 /tmp/gopherdoc_bin \
  -dir "$CORPUS_DIR" \
  -workers "$WORKERS" \
  -chunk-size "$CHUNK_SIZE" \
  -overlap "$OVERLAP" \
  -limit "$LIMIT" \
  > /dev/null \
  2>"$STDERR_LOG"

END_NS=$(date +%s%N)

WALL_NS=$(( END_NS - START_NS ))
WALL_S=$(echo "scale=3; $WALL_NS / 1000000000" | bc)
THROUGHPUT=$(echo "scale=2; $CORPUS_MB / $WALL_S" | bc)

CHUNK_COUNT=$(grep -oP 'done: \K\d+(?= chunks)' "$STDERR_LOG" || echo "N/A")

# Formato gctrace: "gc N @Xs Y%: ... W->X->Z MB, ..."
# Z = heap live pós-GC. Peak = maior Z entre todos os ciclos.
PEAK_HEAP_MB=$(grep -oP '\d+->\d+->\K\d+(?= MB)' "$STDERR_LOG" \
  | sort -n | tail -1 || echo "N/A")

GC_COUNT=$(grep -c '^gc ' "$STDERR_LOG" 2>/dev/null || echo "0")

echo ""
echo "============================================================"
echo "  RESULTADO — GopherDoc"
echo "============================================================"
printf "  Wall time          : %s s\n"    "$WALL_S"
printf "  Throughput         : %s MB/s\n" "$THROUGHPUT"
printf "  Peak heap (pós-GC) : %s MB\n"  "$PEAK_HEAP_MB"
printf "  GC cycles          : %s\n"      "$GC_COUNT"
printf "  Total de chunks    : %s\n"      "$CHUNK_COUNT"
printf "  Arquivos           : %s\n"      "$FILE_COUNT"
printf "  Corpus             : %s MB\n"   "$CORPUS_MB"
echo "============================================================"
echo ""

if [[ -f "$RESULTS_FILE" ]]; then
  GO_VERSION=$(go version | awk '{print $3}')
  DATE_NOW=$(date -u +"%Y-%m-%d %H:%M UTC")
  echo "| GopherDoc | $GO_VERSION | $WALL_S s | $THROUGHPUT MB/s | $PEAK_HEAP_MB MB | $CHUNK_COUNT | $FILE_COUNT | $DATE_NOW |" \
    >> "$RESULTS_FILE"
  echo "  -> Resultado appended em $RESULTS_FILE"
fi
