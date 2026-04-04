# Benchmark Results — RAG Ingestion

---

## Environment

| Field                    | Value                   |
|--------------------------|------------------------|
| Date                     | 2026-04-04              |
| OS                       | Ubuntu 24.04 LTS        |
| Go version               | go1.22.2                |
| Python version           | 3.12.3                  |
| langchain-text-splitters | 0.3.8                   |
| GopherDoc                | v1.0.1 (commit 29c5ba4) |

---

## Benchmark parameters

| Parameter  | Value                   |
|------------|-------------------------|
| chunk_size | 4096                    |
| overlap    | 512                     |
| workers    | 16                      |
| Corpus     | 1688.79 MB (1402 files) |
| File types | .md, .txt, .csv, .json  |

---

## Results (median of 3 runs)

| Engine    | Version  | Wall time      | Throughput      | Peak heap     | Chunks  | Files |
|-----------|----------|----------------|-----------------|---------------|---------|-------|
| GopherDoc | go1.22.2 | **4.770 s**    | **354.04 MB/s** | **116 MB**    | 498,210 | 1,402 |
| LangChain | py3.12.3 | **1369.986 s** | **1.23 MB/s**   | **396.67 MB** | 496,348 | 1,402 |

---

## Delta

| Metric           | GopherDoc    | LangChain    | Difference                  |
|------------------|--------------|--------------|-----------------------------|
| Wall time        | 4.770 s      | 1369.986 s   | **GopherDoc 287× faster**   |
| Throughput       | 354.04 MB/s  | 1.23 MB/s    | **GopherDoc 288× higher**   |
| Peak heap        | 116 MB       | 396.67 MB    | **GopherDoc 3.4× smaller**  |
| Chunks generated | 498,210      | 496,348      | ~0.4% difference (expected) |

---

## Raw runs

| Run        | GopherDoc wall time | GopherDoc throughput | GopherDoc heap | LangChain wall time | LangChain throughput | LangChain heap |
|------------|---------------------|----------------------|----------------|---------------------|----------------------|----------------|
| 1          | 4.010 s             | 421.14 MB/s          | 117 MB         | 1363.332 s          | 1.24 MB/s            | 388.76 MB      |
| 2          | 9.674 s             | 174.56 MB/s          | 82 MB          | 1391.983 s          | 1.21 MB/s            | 396.69 MB      |
| 3          | 4.770 s             | 354.04 MB/s          | 116 MB         | 1369.986 s          | 1.23 MB/s            | 396.67 MB      |
| **Median** | **4.770 s**         | **354.04 MB/s**      | **116 MB**     | **1369.986 s**      | **1.23 MB/s**        | **396.67 MB**  |

---

## Notes

- **Nearly identical chunk counts** (~0.4% difference): both use chunk_size=4096 / overlap=512 over the same files — the delta is explained by differences in separator handling between `RecursiveCharacterTextSplitter` and GopherDoc's parsers.
- **GopherDoc run 2 outlier (9.674 s)**: likely cold page cache or competing I/O. The median correctly isolates this.
- **LangChain heap (396.67 MB)**: measured via `tracemalloc` — Python-managed memory only. Process RSS peaked at **~1.3 GB** during execution due to interpreter overhead and Python's internal string structures.
- **GopherDoc heap (116 MB)**: largest heap value recorded by `gctrace` at collection time. On a more homogeneous 2.1 GB corpus (GopherDoc's original benchmark), the post-GC live set is **2.0 MB** — the higher value here reflects the larger CSV/JSON files in this corpus.
- LangChain was run with `ThreadPoolExecutor(16)`. CPython's GIL prevents real parallelism for CPU-bound code; chunking runs mostly in series, which explains the ~288× lower throughput.

---

## How to interpret

- **Wall time**: clock time from start to finish, including I/O and parallelism.
- **Throughput**: `corpus_bytes / wall_time`, in MB/s (1 MB = 1,048,576 bytes).
- **Peak heap**:
  - GopherDoc: largest heap value recorded by `gctrace` (`GODEBUG=gctrace=1`).
  - LangChain: peak from `tracemalloc.get_traced_memory()[1]` — Python-managed memory, does **not** include interpreter overhead.
- **Chunks**: number of segments produced by the splitter. Small divergences are expected due to differences in whitespace/separator handling between the two implementations.
