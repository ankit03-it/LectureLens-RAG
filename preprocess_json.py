import requests  # type: ignore
import os
import json
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import joblib  # type: ignore

def create_embedding(text_list):
    # Send the POST request to the Ollama embedding endpoint
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "nomic-embed-text",
        "input": text_list
    })

    # Check if the response was successful
    if r.status_code != 200:
        print(f"Error: Received status code {r.status_code}")
        print("Response text:", r.text)
        raise Exception("Failed to create embedding from Ollama")

    response_data = r.json()

    # Look for "embeddings" (plural) or fall back to "embedding" (singular)
    if "embeddings" in response_data:
        return response_data["embeddings"]
    else:
        # If neither key is found, print what we got back to debug
        print("Unexpected response structure:", response_data)
        raise KeyError("Could not find 'embeddings' key in the response JSON.")


folder_name = "newjsons"
jsons = os.listdir(folder_name) 
my_dicts = []
chunk_id = 0

for json_file in jsons:
    with open(f"{folder_name}/{json_file}", encoding="utf-8") as f:
        content = json.load(f)
        
    print(f"Creating Embeddings for {json_file}")
    
    # Extract the texts from the chunks
    texts = [c['text'] for c in content['chunks']]
    
    # Generate embeddings
    embeddings = create_embedding(texts)
    
    for i, chunk in enumerate(content['chunks']):
        chunk['chunk_id'] = chunk_id
        # Safely assign the embedding
        chunk['embedding'] = embeddings[i]
        chunk_id += 1
        my_dicts.append(chunk) 

df = pd.DataFrame.from_records(my_dicts)
# Save this dataframe
joblib.dump(df, 'embeddings.joblib')
print("Successfully created and saved embeddings.joblib!")