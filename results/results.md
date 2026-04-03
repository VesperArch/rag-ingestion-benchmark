# Resultados do Benchmark — RAG Ingestion

---

## Ambiente

| Campo                    | Valor                   |
|--------------------------|------------------------|
| Data                     | 2026-04-03              |
| OS                       | Ubuntu 24.04 LTS        |
| Go version               | go1.22.2                |
| Python version           | 3.12.3                  |
| langchain-text-splitters | 0.3.8                   |
| GopherDoc                | v1.0.1 (commit 29c5ba4) |

---

## Parâmetros do benchmark

| Parâmetro        | Valor                      |
|------------------|---------------------------|
| chunk_size       | 4096                       |
| overlap          | 512                        |
| workers          | 16                         |
| Corpus           | 1688.79 MB (1402 arquivos) |
| Tipos de arquivo | .md, .txt, .csv, .json     |

---

## Tabela de resultados

| Engine    | Versão   | Wall time   | Throughput   | Peak heap | Chunks  | Arquivos |
|-----------|----------|-------------|--------------|-----------|---------|----------|
| GopherDoc | go1.22.2 | 4.010 s     | 421.14 MB/s  | 117 MB    | 498,211 | 1,402    |
| LangChain | py3.12.3 | 1363.332 s  | 1.24 MB/s    | 388.76 MB | 496,349 | 1,402    |

---

## Delta

| Métrica        | GopherDoc     | LangChain    | Diferença                        |
|----------------|--------------|--------------|----------------------------------|
| Wall time      | 4.010 s      | 1363.332 s   | **GopherDoc 340× mais rápido**   |
| Throughput     | 421.14 MB/s  | 1.24 MB/s    | **GopherDoc 340× maior**         |
| Peak heap      | 117 MB       | 388.76 MB    | **GopherDoc 3.3× menor**         |
| Chunks gerados | 498,211      | 496,349      | ~0.4% de diferença (esperado)    |

---

## Observações

- **Chunks quase idênticos** (~0.4% de diferença): ambos usam chunk_size=4096 / overlap=512 sobre os mesmos arquivos — o delta é explicado por diferenças no tratamento de separadores entre `RecursiveCharacterTextSplitter` e os parsers do GopherDoc.
- **Heap do LangChain (389 MB)**: medição via `tracemalloc` — memória Python gerenciada. O RSS do processo chegou a **~1.3 GB** durante a execução, devido ao overhead do interpretador e das estruturas internas de strings Python.
- **Heap do GopherDoc (117 MB)**: valor pós-GC do `gctrace`. Em corpus de 2.1 GB mais homogêneo (benchmark original do GopherDoc), o heap pós-GC é de **2.0 MB** — o valor mais alto aqui reflete os arquivos CSV/JSON maiores deste corpus.
- O LangChain foi executado com `ThreadPoolExecutor(16)`. O GIL do CPython impede paralelismo real em código CPU-bound; o chunking ocorre de forma majoritariamente serial, explicando o throughput ~340× menor.

---

## Como interpretar

- **Wall time**: tempo de relógio do início ao fim, incluindo I/O e paralelismo.
- **Throughput**: `corpus_bytes / wall_time`, em MB/s (1 MB = 1 048 576 bytes).
- **Peak heap**:
  - GopherDoc: maior valor `HEAP` pós-GC registrado pelo `gctrace` (`GODEBUG=gctrace=1`).
  - LangChain: pico de `tracemalloc.get_traced_memory()[1]` — memória Python gerenciada, **não** inclui overhead do interpretador.
- **Chunks**: número de segmentos produzidos pelo splitter. Pequenas divergências são esperadas por diferenças no tratamento de whitespace/separadores entre as duas implementações.
