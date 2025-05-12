import chromadb
from sentence_transformers import SentenceTransformer
import sys
import os


def extract_topic_and_types(search_term):
    lowered = search_term.lower()
    types = []

    if "satz" in lowered:
        types.append("satz")
    if "definition" in lowered:
        types.append("definition")
    if "beispiel" in lowered or "beispiele" in lowered:
        types.append("beispiele")
    if "bemerkung" in lowered or "bemerkungen" in lowered:
        types.append("bemerkungen")

    # Entferne diese Wörter aus dem Thema
    for keyword in ["satz", "definition", "beispiel", "beispiele", "bemerkung", "bemerkungen", "und", "oder", "zu"]:
        lowered = lowered.replace(keyword, "")
    topic = lowered.strip()

    return topic, types if types else None


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


def search_chroma(search_term, collection_name='math_contextual', top_n=6, output_dir='05_chroma_output/'):
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

    print(f"Ergebnisse gespeichert in: {latest_filename}")
    return latest_filename


if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
    else:
        search_term = input("Suchbegriff(e) eingeben: ")

    topic, types = extract_topic_and_types(search_term)
    print(f"[INFO] Extrahiert: Topic = '{topic}', Types = {types}")

    if topic and types:
        search_chroma_by_types_and_topic(topic, types)
    else:
        search_chroma(search_term)
