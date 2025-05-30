import chromadb
from openai import OpenAI
import sys
import os
import json
import numpy as np


def search_chroma(search_term, collection_name='math_contextual', top_n=3, output_dir='05_chroma_output/'):
    chroma_client = chromadb.PersistentClient(path="04_chromaDB")
    collection = chroma_client.get_collection(name=collection_name)
    embed_client = OpenAI()
    embedding = embed_client.embeddings.create(input=[search_term], model="text-embedding-ada-002").data[0].embedding

    results = collection.query(query_embeddings=[embedding], n_results=top_n)
    os.makedirs(output_dir, exist_ok=True)
    latest_filename = os.path.join(output_dir, "chroma_results_latest.txt")
    found_pages = set()

    with open(latest_filename, 'w', encoding='utf-8') as f:
        for i, (doc_id, doc, distance, metadata) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        )):
            pages = metadata.get('page', [])
            if isinstance(pages, list):
                found_pages.update(pages)
            elif isinstance(pages, int):
                found_pages.add(pages)

            f.write(f"=== TREFFER {i + 1} ===\n")
            f.write(f"ID: {doc_id}\n")
            f.write(f"Score (Abstand): {distance:.6f}\n")
            f.write(f"Kapitel: {metadata.get('chapter', '')}\n")
            f.write(f"Abschnitt: {metadata.get('section', '')}\n")
            f.write(f"Subabschnitt: {metadata.get('subsection', '')}\n")
            f.write(f"Seite: {pages}\n")
            f.write(f"Inhalt:\n{doc}\n")
            f.write("\n" + "=" * 50 + "\n\n")

    sorted_pages = sorted(found_pages)
    pages_filename = os.path.join(output_dir, "chroma_pages_latest.txt")
    with open(pages_filename, "w", encoding="utf-8") as pf:
        pf.write(",".join(str(p) for p in sorted_pages))

    print(f"[INFO] Ergebnisse gespeichert in: {latest_filename}")
    print(f"[INFO] Relevante Seiten gespeichert in: {pages_filename}")
    return latest_filename


if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
    else:
        search_term = input("Suchbegriff(e) eingeben: ")

    search_chroma(search_term)
