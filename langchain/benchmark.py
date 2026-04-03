#!/usr/bin/env python3
"""Benchmark de ingestão e chunking com LangChain/RecursiveCharacterTextSplitter.

Métricas capturadas:
    Wall time via time.perf_counter, throughput em MB/s, peak heap via
    tracemalloc (memória Python gerenciada, não RSS do processo).
"""

import argparse
import concurrent.futures
import datetime
import os
import sys
import time
import tracemalloc
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

# chunk_size e overlap idênticos ao GopherDoc para comparação justa.
CHUNK_SIZE = 4096
CHUNK_OVERLAP = 512
SUPPORTED_EXT = {".md", ".txt", ".csv", ".json"}


def collect_files(corpus_dir: Path) -> list[Path]:
    """Retorna arquivos suportados dentro de corpus_dir, em ordem estável.

    Args:
        corpus_dir: Diretório raiz do corpus.

    Returns:
        Lista de Path ordenada lexicograficamente.
    """
    return sorted(
        p for p in corpus_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
    )


def process_file(
    path: Path,
    splitter: RecursiveCharacterTextSplitter,
) -> tuple[int, int]:
    """Lê um arquivo e aplica o splitter.

    Args:
        path: Caminho do arquivo a processar.
        splitter: Instância configurada do RecursiveCharacterTextSplitter.

    Returns:
        Tupla (bytes_lidos, num_chunks). Retorna (0, 0) em erro de I/O para
        não interromper o benchmark — erros são reportados em stderr.
    """
    try:
        raw = path.read_bytes()
        chunks = splitter.split_text(raw.decode("utf-8", errors="replace"))
        return len(raw), len(chunks)
    except OSError as exc:
        print(f"WARN: não foi possível ler {path}: {exc}", file=sys.stderr)
        return 0, 0


def main() -> None:
    parser = argparse.ArgumentParser(description="LangChain ingestion benchmark")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path(__file__).parent.parent / "corpus",
        help="Diretório do corpus (default: ../corpus)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(16, (os.cpu_count() or 1)),
        help="Threads paralelas (default: min(16, cpu_count))",
    )
    args = parser.parse_args()

    corpus_dir = args.corpus_dir.resolve()
    workers = args.workers

    if not corpus_dir.is_dir():
        print(f"ERROR: Corpus não encontrado em: {corpus_dir}", file=sys.stderr)
        sys.exit(1)

    # Coleta e stat dos arquivos antes de iniciar qualquer timer ou tracemalloc.
    files = collect_files(corpus_dir)
    if not files:
        print(
            f"ERROR: Nenhum arquivo suportado em: {corpus_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    corpus_bytes = sum(f.stat().st_size for f in files)
    corpus_mb = corpus_bytes / 1_048_576

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )

    print("=" * 60)
    print("  LangChain Benchmark")
    print("=" * 60)
    print(f"  Corpus : {corpus_dir}")
    print(f"  Tamanho: {corpus_mb:.2f} MB ({len(files)} arquivos)")
    print(f"  Workers: {workers}")
    print(f"  Chunk  : {CHUNK_SIZE} bytes | Overlap: {CHUNK_OVERLAP} bytes")
    print("=" * 60)
    print()

    # tracemalloc iniciado antes de qualquer alocação de dados do corpus.
    tracemalloc.start()

    total_bytes = 0
    total_chunks = 0
    wall_start = time.perf_counter()

    # ThreadPoolExecutor é eficaz aqui porque leitura de disco domina o tempo;
    # o GIL não é o gargalo neste workload I/O-bound.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_file, f, splitter): f for f in files
        }
        for future in concurrent.futures.as_completed(futures):
            b, c = future.result()
            total_bytes += b
            total_chunks += c

    wall_s = time.perf_counter() - wall_start

    # Snapshot capturado imediatamente após o processamento.
    snapshot = tracemalloc.take_snapshot()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    throughput_mbs = (total_bytes / 1_048_576) / wall_s if wall_s > 0 else 0.0
    peak_heap_mb = peak_bytes / 1_048_576

    print()
    print("=" * 60)
    print("  RESULTADO — LangChain")
    print("=" * 60)
    print(f"  Wall time          : {wall_s:.3f} s")
    print(f"  Throughput         : {throughput_mbs:.2f} MB/s")
    print(f"  Peak heap (real)   : {peak_heap_mb:.2f} MB")
    print(f"  Total de chunks    : {total_chunks:,}")
    print(f"  Arquivos           : {len(files):,}")
    print(f"  Corpus             : {corpus_mb:.2f} MB")
    print("=" * 60)
    print()
    print("  Top 5 alocadores (tracemalloc):")
    for stat in snapshot.statistics("lineno")[:5]:
        print(f"    {stat}")
    print()

    results_file = Path(__file__).parent.parent / "results" / "results.md"
    if results_file.exists():
        py_version = (
            f"python{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        )
        date_now = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        row = (
            f"| LangChain | {py_version} "
            f"| {wall_s:.3f} s "
            f"| {throughput_mbs:.2f} MB/s "
            f"| {peak_heap_mb:.2f} MB "
            f"| {len(files):,} "
            f"| {date_now} |\n"
        )
        with results_file.open("a") as fh:
            fh.write(row)
        print(f"  -> Resultado appended em {results_file}")


if __name__ == "__main__":
    main()
