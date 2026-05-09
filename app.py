import pandas as pd
import numpy as np
import joblib
import requests
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
import logging
import faiss

# ================= CONFIG =================

LLM_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"

OLLAMA_URL = "http://localhost:11434"

CACHE_FILE = "lecture_cache.json"

TOP_RESULTS = 5
SIMILARITY_THRESHOLD = 0.35

# ==========================================

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

# ================= CACHE ==================

def load_cache():

    if os.path.exists(CACHE_FILE):

        try:

            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:

            logging.error(f"Cache Load Error: {e}")

            return {}

    return {}

def save_to_cache(query, result):

    cache = load_cache()

    cache[query.lower().strip()] = result

    with open(CACHE_FILE, "w", encoding="utf-8") as f:

        json.dump(
            cache,
            f,
            indent=4,
            ensure_ascii=False
        )

# ==========================================

# ============= LOAD DATA ==================

try:

    df = joblib.load("embeddings.joblib")

    logging.info("Embeddings loaded successfully.")
    logging.info(f"Total chunks: {len(df)}")

    # Old cosine similarity matrix
    # DF_EMBEDDING_MATRIX = np.vstack(df["embedding"].values)

    # Load FAISS index
    FAISS_INDEX = faiss.read_index("faiss_index.bin")

    logging.info("FAISS index loaded successfully.")

except Exception as e:

    logging.error(f"Initialization Error: {e}")

    df = pd.DataFrame()

    FAISS_INDEX = None

# ==========================================

# ============ AI FUNCTIONS ================

def create_embedding(text):

    try:

        r = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=30
        )

        r.raise_for_status()

        data = r.json()

        if "embeddings" in data:
            return data["embeddings"][0]

        elif "embedding" in data:
            return data["embedding"]

        else:

            logging.error(
                f"Unexpected embedding response: {data}"
            )

            return None

    except Exception as e:

        logging.error(f"Embedding Error: {e}")

        return None

def generate_llm_response(prompt):

    try:

        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=120
        )

        r.raise_for_status()

        data = r.json()

        return data.get(
            "response",
            "No response generated."
        )

    except Exception as e:

        logging.error(f"LLM Error: {e}")

        return "Error generating response."

# ==========================================

# =============== API ROUTE ================

@app.route("/api/query", methods=["POST"])
def rag_query():

    data = request.get_json()

    incoming_query = data.get(
        "query",
        ""
    ).strip()

    if not incoming_query:

        return jsonify({
            "error": "Query is empty."
        }), 400

    # ========= CACHE CHECK =========

    cache = load_cache()

    cache_key = incoming_query.lower()

    if cache_key in cache:

        logging.info(f"Cache Hit: {incoming_query}")

        return jsonify(cache[cache_key])

    # =================================

    if df.empty or FAISS_INDEX is None:

        return jsonify({
            "error": "Embeddings or FAISS index not loaded."
        }), 500

    # ========= QUERY EMBEDDING ========

    question_embedding = create_embedding(
        incoming_query
    )

    if question_embedding is None:

        return jsonify({
            "error": "Failed to create embedding."
        }), 500

    # ===================================
    # OLD COSINE SIMILARITY RETRIEVAL
    # ===================================

    # query_vector = np.array(question_embedding).reshape(1, -1)

    # similarities = cosine_similarity(
    #     DF_EMBEDDING_MATRIX,
    #     query_vector
    # ).flatten()

    # sorted_indices = similarities.argsort()[::-1]

    # filtered_indices = [
    #     idx for idx in sorted_indices
    #     if similarities[idx] >= SIMILARITY_THRESHOLD
    # ][:TOP_RESULTS]

    # retrieved_df = df.iloc[filtered_indices]

    # ===================================
    # NEW FAISS RETRIEVAL
    # ===================================

    query_vector = np.array(
        question_embedding,
        dtype="float32"
    ).reshape(1, -1)

    distances, indices = FAISS_INDEX.search(
        query_vector,
        TOP_RESULTS
    )

    retrieved_indices = indices[0]

    retrieved_df = df.iloc[retrieved_indices]

    # ===================================

    context_data = retrieved_df[
        ["title", "number", "start", "end", "text"]
    ].to_dict(orient="records")

    # ========= PROMPT =========

    prompt = f"""
You are LectureLens AI.

Use ONLY the lecture context below to answer the student's question.

LECTURE CONTEXT:
{json.dumps(context_data, indent=2)}

QUESTION:
{incoming_query}

RULES:
- Mention lecture number
- Mention timestamps
- Explain clearly
- Do not invent information
- If answer is unavailable, say so
"""

    # ========= GENERATE =========

    llm_response = generate_llm_response(
        prompt
    )

    final_payload = {
        "answer": llm_response,
        "context_sources": context_data
    }

    # ========= SAVE CACHE =========

    save_to_cache(
        incoming_query,
        final_payload
    )

    return jsonify(final_payload)

# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )