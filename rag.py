import json, os, sys, glob, urllib.request
import numpy as np
from advice import ADVICE

EMBED_MODEL = "nomic-embed-text"
INDEX_FILE = "index/index.json"
_cache = None


def embed(texts):
    req = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps({"model": EMBED_MODEL, "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["embeddings"]


def split_text(text, size=900, overlap=150):
    text = " ".join(text.split())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def collect_chunks():
    chunks = []
    # 1. advice.py base
    for name, (about, steps) in ADVICE.items():
        label = name.replace("___", " - ").replace("_", " ")
        text = f"{label}. {about} Steps: " + "; ".join(steps)
        chunks.append({"text": text, "source": "KisanSaathi advice base"})
    # 2. documents in docs/
    for path in glob.glob("docs/*"):
        fname = os.path.basename(path)
        if path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            for p, page in enumerate(PdfReader(path).pages, 1):
                for c in split_text(page.extract_text() or ""):
                    if len(c) > 80:
                        chunks.append({"text": c, "source": f"{fname}, page {p}"})
        elif path.lower().endswith(".txt"):
            with open(path, encoding="utf-8", errors="ignore") as f:
                for c in split_text(f.read()):
                    chunks.append({"text": c, "source": fname})
    return chunks


def build_index():
    chunks = collect_chunks()
    print(f"Embedding {len(chunks)} chunks...")
    for i in range(0, len(chunks), 16):
        batch = chunks[i:i + 16]
        for c, e in zip(batch, embed([b["text"] for b in batch])):
            c["embedding"] = e
    os.makedirs("index", exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f)
    print("Index saved.")


def search(query, k=3):
    global _cache
    if _cache is None:
        with open(INDEX_FILE, encoding="utf-8") as f:
            _cache = json.load(f)
        _cache_matrix = np.array([c["embedding"] for c in _cache])
        _cache.append(_cache_matrix)  # last item holds the matrix
    matrix = _cache[-1]
    items = _cache[:-1]
    q = np.array(embed([query])[0])
    sims = matrix @ q / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q) + 1e-9)
    top = np.argsort(-sims)[:k]
    return [{"text": items[i]["text"], "source": items[i]["source"], "score": float(sims[i])} for i in top]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for r in search(" ".join(sys.argv[1:])):
            print(f"[{r['score']:.2f}] {r['source']}\n{r['text']}\n")
    else:
        build_index()