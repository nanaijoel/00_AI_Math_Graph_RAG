import chromadb
from sentence_transformers import SentenceTransformer
# from datetime import datetime
import sys
import os
import shutil

def search_chroma(search_term, collection_name='math_knowledge', top_n=6, output_dir='05_chroma_output/'):
    chroma_client = chromadb.PersistentClient(path="04_chromaDB")
    collection = chroma_client.get_collection(name=collection_name)

    embed_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")
    query_embedding = embed_model.encode([search_term])

    results = collection.query(query_embeddings=query_embedding, n_results=top_n)

    os.makedirs(output_dir, exist_ok=True)
    latest_filename = f"{output_dir}chroma_results_latest.txt"

    with open(latest_filename, 'w', encoding='utf-8') as f:
        for i in range(len(results['ids'][0])):
            doc_id = results['ids'][0][i]
            doc = results['documents'][0][i]
            distance = results['distances'][0][i]
            metadata = results['metadatas'][0][i]

            f.write(f"=== TREFFER {i + 1} ===\n")
            f.write(f"ID: {doc_id}\n")
            f.write(f"Score (Abstand): {distance}\n")
            f.write(f"Text: {doc}\n")
            f.write(f"Typ: {metadata.get('type', '')}\n")
            f.write(f"Seite: {metadata.get('page', '')}\n")
            f.write("\n" + "=" * 50 + "\n\n")

    print(f"Ergebnisse gespeichert in: {latest_filename}")
    return latest_filename


if __name__ == "__main__":

    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
        search_chroma(search_term)

