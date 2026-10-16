import json, urllib.request

MODEL = "llama3.2:3b"

def ask_llm(question, disease=None, facts=None):
    system = (
        "You are KisanSaathi, a careful farm advisor for small farmers in Maharashtra. "
        "Answer in simple words, in at most 5 short lines. "
        "When known facts are given, base your answer on them and do not add new medical or chemical claims. "
        "Never give pesticide doses or mixing amounts. "
        "If you are not sure, say so and tell the farmer to ask the local agriculture officer."
    )
    context = ""
    if disease:
        context += f"Detected problem: {disease}\n"
    if facts:
        context += "Known facts:\n- " + "\n- ".join(facts) + "\n"
    body = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": context + "\nQuestion: " + question},
        ],
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)["message"]["content"].strip()
    except Exception:
        return "The advisor is not available. Make sure Ollama is running, then try again."

def ask_rag(question, disease=None):
    try:
        import rag
        query = f"{disease.replace('___', ' ').replace('_', ' ')} {question}" if disease else question
        hits = [h for h in rag.search(query, k=3) if h["score"] >= 0.5]
    except Exception:
        hits = []
    facts = [h["text"] for h in hits]
    answer = ask_llm(question, disease=disease, facts=facts or None)
    sources = []
    for h in hits:
        if h["source"] not in sources:
            sources.append(h["source"])
    return {"answer": answer, "sources": sources}