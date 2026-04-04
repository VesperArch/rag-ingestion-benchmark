# RAG Ingestion Benchmark — GopherDoc vs LangChain

Comparison of throughput, heap usage, and wall time between GopherDoc (Go) and LangChain (Python) over the same ~1.7 GB corpus.

| Metric              | GopherDoc    | LangChain    |
|---------------------|--------------|--------------|
| Wall time           | 4.770 s      | 1369.986 s   |
| Throughput          | 354.04 MB/s  | 1.23 MB/s    |
| Peak heap (post-GC) | 116 MB       | 396.67 MB    |
| Chunks generated    | 498,210      | 496,348      |

*Median of 3 runs. Raw data: [results/results.md](results/results.md).*

Full results and environment details: [results/results.md](results/results.md).

---

## Structure

```
rag-ingestion-benchmark/
├── gera_corpus.sh
├── corpus/
│   └── README.md
├── gopherdoc/
│   ├── engine/          ← submodule VesperArch/GopherDoc
│   └── run.sh
├── langchain/
│   ├── benchmark.py
│   └── requirements.txt
└── results/
    └── results.md
```

---

## How to reproduce

### 1. Clone with submodule

```bash
git clone --recurse-submodules https://github.com/VesperArch/rag-ingestion-benchmark
```

### 2. Prerequisites

- Go 1.22+
- Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r langchain/requirements.txt
```

### 3. Generate the corpus

```bash
chmod +x gera_corpus.sh
./gera_corpus.sh
```

### 4. Run GopherDoc

```bash
chmod +x gopherdoc/run.sh
./gopherdoc/run.sh
```

Compiles the binary before starting the timer (`go build` does not count toward wall time). Uses `GODEBUG=gctrace=1` to capture real heap at collection time.

### 5. Run LangChain

```bash
source .venv/bin/activate
python langchain/benchmark.py --corpus-dir corpus/ --workers 16
```

`tracemalloc` is started before any corpus data is allocated.

### 6. View results

```bash
cat results/results.md
```

---

## Methodology

### What is measured

| Metric    | GopherDoc                                        | LangChain                                  |
|-----------|--------------------------------------------------|--------------------------------------------|
| Wall time | `date +%s%N` before/after binary execution       | `time.perf_counter()` before/after pool    |
| Throughput| `corpus_bytes / wall_time`                       | `corpus_bytes / wall_time`                 |
| Peak heap | largest `Z` in `W->X->Z MB` from gctrace        | `tracemalloc.get_traced_memory()[1]`        |

### What is not measured

- Embedding time — no model is called.
- Writing to a vector store.
- GopherDoc compilation.
- Python interpreter startup.

### Comparability

- Same corpus, same directory, no intermediate transformations.
- `chunk_size=4096`, `overlap=512` on both sides.
- 16 workers on both sides.

### Limitations

1. `tracemalloc` tracks Python-managed memory only. Process RSS includes interpreter overhead (~20–30 MB additional).
2. `GODEBUG=gctrace=1` reports the heap size at collection time — the largest value captured represents the peak before release, not the post-GC live set. To measure the live set after a full collection, instrument with `runtime.MemStats.HeapInuse` after an explicit `runtime.GC()`.
3. `ThreadPoolExecutor` in Python does not parallelize CPU-bound code due to the GIL. Chunking runs mostly in series, which explains the ~340× lower throughput.
4. Run 3 times and use the median — results vary with page cache state and system load.

---

## Versions

| Component                | Version         |
|--------------------------|-----------------|
| Go                       | 1.22.2          |
| GopherDoc                | v1.0.1 (29c5ba4)|
| Python                   | 3.12.3          |
| langchain-text-splitters | 0.3.8           |
| langchain-core           | 0.3.52          |
| OS                       | Ubuntu 24.04 LTS|

---

## References

- [VesperArch/GopherDoc](https://github.com/VesperArch/GopherDoc)
- [LangChain RecursiveCharacterTextSplitter](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [GODEBUG gctrace](https://pkg.go.dev/runtime#hdr-Environment_Variables)
- [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)

---

## License

MIT
