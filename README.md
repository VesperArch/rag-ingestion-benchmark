# RAG Ingestion Benchmark — GopherDoc vs LangChain

Comparação de throughput, heap e wall time entre GopherDoc (Go) e LangChain (Python) sobre o mesmo corpus de ~1.7 GB.

| Métrica            | GopherDoc | LangChain |
|--------------------|-----------|-----------|
| Wall time          | 4.010 s   | 1363.332 s |
| Throughput         | 421 MB/s  | 1.24 MB/s  |
| Peak heap (pós-GC) | 117 MB    | 389 MB     |
| Chunks gerados     | 498,211   | 496,349    |

Resultados completos e ambiente: [results/results.md](results/results.md).

---

## Estrutura

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

## Como reproduzir

### 1. Clonar com submodule

```bash
git clone --recurse-submodules https://github.com/VesperArch/rag-ingestion-benchmark
```

### 2. Pré-requisitos

- Go 1.22+
- Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r langchain/requirements.txt
```

### 3. Gerar o corpus

```bash
chmod +x gera_corpus.sh
./gera_corpus.sh
```

### 4. Rodar o GopherDoc

```bash
chmod +x gopherdoc/run.sh
./gopherdoc/run.sh
```

Compila o binário antes de iniciar o timer (`go build` não entra no wall time). Usa `GODEBUG=gctrace=1` para capturar heap pós-GC real.

### 5. Rodar o LangChain

```bash
source .venv/bin/activate
python langchain/benchmark.py --corpus-dir corpus/ --workers 16
```

`tracemalloc` é iniciado antes de qualquer alocação de dados do corpus.

### 6. Ver resultados

```bash
cat results/results.md
```

---

## Metodologia

### O que é medido

| Métrica   | GopherDoc                                          | LangChain                                    |
|-----------|----------------------------------------------------|----------------------------------------------|
| Wall time | `date +%s%N` antes/depois da execução do binário   | `time.perf_counter()` antes/depois do pool   |
| Throughput| `corpus_bytes / wall_time`                         | `corpus_bytes / wall_time`                   |
| Peak heap | maior `Z` em `W->X->Z MB` do gctrace              | `tracemalloc.get_traced_memory()[1]`          |

### O que não é medido

- Tempo de embedding — nenhum modelo é chamado.
- Escrita em banco vetorial.
- Compilação do GopherDoc.
- Inicialização do interpretador Python.

### Comparabilidade

- Mesmo corpus, mesmo diretório, sem transformações intermediárias.
- `chunk_size=4096`, `overlap=512` nos dois lados.
- 16 workers nos dois lados.

### Limitações

1. `tracemalloc` rastreia memória Python gerenciada. O RSS do processo inclui overhead do interpretador (~20–30 MB adicionais).
2. `GODEBUG=gctrace=1` reporta heap pós-GC (live set), não o pico bruto. Para `HeapInuse` máximo, instrumentar com `runtime.MemStats`.
3. `ThreadPoolExecutor` no Python não paralela código CPU-bound por causa do GIL. O chunking ocorre majoritariamente em série, o que explica o throughput ~340× menor.
4. Rodar 3 vezes e usar a mediana — resultados variam com estado do page cache e carga do sistema.

---

## Versões

| Componente               | Versão          |
|--------------------------|-----------------|
| Go                       | 1.22.2          |
| GopherDoc                | v1.0.1 (29c5ba4)|
| Python                   | 3.12.3          |
| langchain-text-splitters | 0.3.8           |
| langchain-core           | 0.3.52          |
| OS                       | Ubuntu 24.04 LTS|

---

## Referências

- [VesperArch/GopherDoc](https://github.com/VesperArch/GopherDoc)
- [LangChain RecursiveCharacterTextSplitter](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [GODEBUG gctrace](https://pkg.go.dev/runtime#hdr-Environment_Variables)
- [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)

---

## Licença

MIT
