# Corpus de Teste

O diretório `corpus/` é lido diretamente por ambos os benchmarks — nenhuma cópia, nenhuma transformação.

---

## Composição

| Tipo     | Arquivos | Tamanho médio | Total aprox. |
|----------|---------|---------------|-------------|
| `.md`    | 500     | 1 MB          | 500 MB      |
| `.txt`   | 500     | 1.5 MB        | 750 MB      |
| `.csv`   | 200     | 2 MB          | 400 MB      |
| `.json`  | 200     | 1.75 MB       | 350 MB      |
| **Total**| **1 400** | —           | **~2 GB**   |

---

## Como gerar

Execute `gera_corpus.sh` na raiz do repositório:

```bash
chmod +x gera_corpus.sh
./gera_corpus.sh
```

O script abaixo é a cópia de referência do que está em `gera_corpus.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly CORPUS_DIR="$(pwd)/corpus"

mkdir -p "$CORPUS_DIR"

echo "[1/4] Gerando arquivos .txt…"
for i in $(seq 1 500); do
  python3 -c "
import random, string, sys
random.seed($i * 7)
size = random.randint(800_000, 2_000_000)
words = [
    ''.join(random.choices(string.ascii_lowercase, k=random.randint(3,12)))
    for _ in range(size // 7)
]
sys.stdout.write(' '.join(words))
" > "$CORPUS_DIR/doc_${i}.txt"
done

echo "[2/4] Gerando arquivos .md…"
for i in $(seq 1 500); do
  python3 -c "
import random, string, sys
random.seed($i * 13)
sections = random.randint(5, 20)
out = []
for s in range(sections):
    out.append(f'## Section {s}')
    for _ in range(random.randint(3, 10)):
        words = [
            ''.join(random.choices(string.ascii_lowercase, k=random.randint(3,12)))
            for _ in range(random.randint(50, 150))
        ]
        out.append(' '.join(words))
        out.append('')
sys.stdout.write('\n'.join(out))
" > "$CORPUS_DIR/doc_${i}.md"
done

echo "[3/4] Gerando arquivos .csv…"
for i in $(seq 1 200); do
  python3 -c "
import random, string, sys, csv, io
random.seed($i * 31)
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(['id','title','body','score','tags'])
for r in range(random.randint(5_000, 15_000)):
    body = ' '.join(
        ''.join(random.choices(string.ascii_lowercase, k=random.randint(3,10)))
        for _ in range(random.randint(20, 60))
    )
    tags = ','.join(
        ''.join(random.choices(string.ascii_lowercase, k=5))
        for _ in range(random.randint(1,5))
    )
    w.writerow([r, f'title_{r}', body, round(random.random()*100,2), tags])
sys.stdout.write(buf.getvalue())
" > "$CORPUS_DIR/data_${i}.csv"
done

echo "[4/4] Gerando arquivos .json…"
for i in $(seq 1 200); do
  python3 -c "
import random, string, json, sys
random.seed($i * 53)
def rword(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))
docs = [
    {
        'id': d,
        'title': ' '.join(rword() for _ in range(random.randint(3,8))),
        'body': ' '.join(rword(random.randint(3,12)) for _ in range(random.randint(100,400))),
        'metadata': {
            'author': rword(),
            'tags': [rword() for _ in range(random.randint(1,6))],
            'score': round(random.random()*100, 4),
        }
    }
    for d in range(random.randint(200, 600))
]
sys.stdout.write(json.dumps(docs, ensure_ascii=False))
" > "$CORPUS_DIR/docs_${i}.json"
done

echo ""
echo "Corpus gerado em: $CORPUS_DIR"
du -sh "$CORPUS_DIR" | awk '{print "Tamanho total:    " $1}'
echo "Arquivos:         $(find "$CORPUS_DIR" -type f | wc -l)"
```

---

## Verificação de integridade

```bash
du -sh corpus/
find corpus/ -type f | wc -l
find corpus/ -type f -name "*.txt" | wc -l
find corpus/ -type f -name "*.md"  | wc -l
find corpus/ -name "*.csv" | wc -l
find corpus/ -name "*.json" | wc -l
```

---

## Notas

- Os arquivos gerados não são versionados — `.gitignore` exclui `corpus/*` exceto este README.
- Sementes fixas por índice (`seed = i × primo`): o corpus é byte-a-byte idêntico em qualquer máquina com **Python 3.10+**. O algoritmo interno do `random` pode diferir em versões anteriores.
- Não mova, renomeie ou recompacte os arquivos entre as execuções dos dois benchmarks.
