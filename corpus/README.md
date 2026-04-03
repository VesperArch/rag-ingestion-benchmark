# Test Corpus

The `corpus/` directory is read directly by both benchmarks — no copies, no transformations.

---

## Composition

| Type     | Files   | Avg size | Total approx. |
|----------|---------|----------|---------------|
| `.md`    | 500     | 1 MB     | 500 MB        |
| `.txt`   | 500     | 1.5 MB   | 750 MB        |
| `.csv`   | 200     | 2 MB     | 400 MB        |
| `.json`  | 200     | 1.75 MB  | 350 MB        |
| **Total**| **1 400** | —      | **~2 GB**     |

---

## How to generate

Run `gera_corpus.sh` from the repository root:

```bash
chmod +x gera_corpus.sh
./gera_corpus.sh
```

The script below is the reference copy of what is in `gera_corpus.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly CORPUS_DIR="$(pwd)/corpus"

mkdir -p "$CORPUS_DIR"

echo "[1/4] Generating .txt files…"
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

echo "[2/4] Generating .md files…"
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

echo "[3/4] Generating .csv files…"
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

echo "[4/4] Generating .json files…"
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
echo "Corpus generated at: $CORPUS_DIR"
du -sh "$CORPUS_DIR" | awk '{print "Total size:       " $1}'
echo "Files:            $(find "$CORPUS_DIR" -type f | wc -l)"
```

---

## Integrity check

```bash
du -sh corpus/
find corpus/ -type f | wc -l
find corpus/ -type f -name "*.txt" | wc -l
find corpus/ -type f -name "*.md"  | wc -l
find corpus/ -name "*.csv" | wc -l
find corpus/ -name "*.json" | wc -l
```

---

## Notes

- Generated files are not versioned — `.gitignore` excludes `corpus/*` except this README.
- Fixed seeds per index (`seed = i × prime`): the corpus is byte-for-byte identical on any machine running **Python 3.10+**. The internal `random` algorithm may differ in earlier versions.
- Do not move, rename, or repack files between the two benchmark runs.
