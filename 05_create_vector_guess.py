import chromadb
from sentence_transformers import SentenceTransformer
import sys
import os
import json
import numpy as np


def extract_all_titles(hierarchy):
    """Rekursiv alle Titel aus verschachtelter Hierarchie extrahieren"""
    titles = []

    def recurse(node):
        if isinstance(node, dict):
            if "title" in node:
                titles.append(node["title"])
            for val in node.values():
                recurse(val)
        elif isinstance(node, list):
            for item in node:
                recurse(item)

    recurse(hierarchy)
    return titles


def extract_topic_and_types(search_term, hierarchy_json_path="01_hierarchy/hierarchy.json"):
    lowered = search_term.lower()
    types = []

    # Flexible Typ-Erkennung
    if "satz" in lowered:
        types.append("satz")
    if "definition" in lowered:
        types.append("definition")
    if "beispiel" in lowered or "beispiele" in lowered:
        types.append("beispiele")
    if "bemerkung" in lowered or "bemerkungen" in lowered:
        types.append("bemerkungen")

    # Entferne typische Füllwörter
    for keyword in ["satz", "definition", "beispiel", "beispiele", "bemerkung", "bemerkungen", "und", "oder", "zu", "zur", "zur", "zur"]:
        lowered = lowered.replace(keyword, "")
    cleaned_input = lowered.strip()

    # Lade Titel aus Hierarchie
    with open(hierarchy_json_path, "r", encoding="utf-8") as f:
        hierarchy = json.load(f)

    all_titles = extract_all_titles(hierarchy)
    if not all_titles:
        print("[WARN] Keine Titel in der Hierarchie gefunden.")
        return cleaned_input, types if types else None

    # Semantisch ähnlichsten Titel finden
    model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")
    input_emb = model.encode([cleaned_input])[0]
    title_embs = model.encode(all_titles)

    similarities = np.dot(title_embs, input_emb)
    best_match_index = int(np.argmax(similarities))
    best_title = all_titles[best_match_index]

    return best_title, types if types else None


def search_chroma_by_types_and_topic(topic, types, collection_name='math_contextual', top_n=4, output_dir='05_chroma_output/'):
    chroma_client = chromadb.PersistentClient(path="04_chromaDB")
    collection = chroma_client.get_collection(name=collection_name)
    embed_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")

    os.makedirs(output_dir, exist_ok=True)
    latest_filename = os.path.join(output_dir, "chroma_results_latest.txt")

    with open(latest_filename, 'w', encoding='utf-8') as f:
        for typ in types:
            query = f"{typ} zu {topic}"
            embedding = embed_model.encode([query])
            results = collection.query(query_embeddings=embedding, n_results=top_n, where={"type": typ})

            if not results["documents"]:
                continue

            for i, (doc_id, doc, distance, metadata) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['distances'][0],
                results['metadatas'][0]
            )):
                f.write(f"=== TREFFER ({typ.upper()}) {i + 1} ===\n")
                f.write(f"ID: {doc_id}\n")
                f.write(f"Score (Abstand): {distance:.6f}\n")
                f.write(f"Titel: {metadata.get('title', '')}\n")
                f.write(f"Typ: {metadata.get('type', '')}\n")
                f.write(f"Kapitel: {metadata.get('chapter', '')}\n")
                f.write(f"Abschnitt: {metadata.get('section', '')}\n")
                f.write(f"Subabschnitt: {metadata.get('subsection', '')}\n")
                f.write(f"Seite: {metadata.get('page', '')}\n")
                f.write(f"Inhalt:\n{doc}\n")
                f.write("\n" + "=" * 50 + "\n\n")

    print(f"[INFO] Ergebnisse gespeichert in: {latest_filename}")
    return latest_filename


def search_chroma(search_term, collection_name='math_contextual', top_n=10, output_dir='05_chroma_output/'):
    chroma_client = chromadb.PersistentClient(path="04_chromaDB")
    collection = chroma_client.get_collection(name=collection_name)
    embed_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")
    query_embedding = embed_model.encode([search_term])

    results = collection.query(query_embeddings=query_embedding, n_results=top_n)
    os.makedirs(output_dir, exist_ok=True)
    latest_filename = os.path.join(output_dir, "chroma_results_latest.txt")

    with open(latest_filename, 'w', encoding='utf-8') as f:
        for i, (doc_id, doc, distance, metadata) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        )):
            f.write(f"=== TREFFER {i + 1} ===\n")
            f.write(f"ID: {doc_id}\n")
            f.write(f"Score (Abstand): {distance:.6f}\n")
            f.write(f"Titel: {metadata.get('title', '')}\n")
            f.write(f"Typ: {metadata.get('type', '')}\n")
            f.write(f"Kapitel: {metadata.get('chapter', '')}\n")
            f.write(f"Abschnitt: {metadata.get('section', '')}\n")
            f.write(f"Subabschnitt: {metadata.get('subsection', '')}\n")
            f.write(f"Seite: {metadata.get('page', '')}\n")
            f.write(f"Inhalt:\n{doc}\n")
            f.write("\n" + "=" * 50 + "\n\n")

    print(f"[INFO] Ergebnisse gespeichert in: {latest_filename}")
    return latest_filename


if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
    else:
        search_term = input("Suchbegriff(e) eingeben: ")

    topic, types = extract_topic_and_types(search_term)
    print(f"[INFO] Finaler Topic: '{topic}', Types: {types}")

    if topic:
        combined_search_term = topic + " " + " ".join(types) if types else topic
        search_chroma(combined_search_term)
    else:
        search_chroma(search_term)
