import faiss
import joblib
import numpy as np

# ==========================
# Load Existing Embeddings
# ==========================

df = joblib.load("embeddings.joblib")

print(f"Loaded {len(df)} chunks")

# ==========================
# Convert Embeddings
# ==========================

embedding_matrix = np.vstack(df["embedding"].values)

# Convert to float32 (VERY IMPORTANT)
embedding_matrix = embedding_matrix.astype("float32")

print("Embedding Matrix Shape:")
print(embedding_matrix.shape)

# ==========================
# Create FAISS Index
# ==========================

dimension = embedding_matrix.shape[1]

index = faiss.IndexFlatL2(dimension)

print("FAISS Index Created")

# ==========================
# Add Embeddings to Index
# ==========================

index.add(embedding_matrix)

print(f"Total vectors in index: {index.ntotal}")

# ==========================
# Save Index
# ==========================

faiss.write_index(index, "faiss_index.bin")

print("FAISS index saved successfully")