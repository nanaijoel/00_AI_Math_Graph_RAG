import json
from pathlib import Path
from tqdm import tqdm
import chromadb
from sentence_transformers import SentenceTransformer

def create_contextual_chroma(hierarchy_path="01_hierarchy/hierarchy.json", db_dir="04_chromaDB"):
    db_path = Path(db_dir)
    db_path.mkdir(exist_ok=True)

    model_id = "sentence-transformers/distiluse-base-multilingual-cased-v2"
    model = SentenceTransformer(model_id)

    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection("math_contextual")

    documents, metadatas, ids, embeddings = [], [], [], []

    with open(hierarchy_path, "r", encoding="utf-8") as f:
        hierarchy = json.load(f)

    for chap_id, chap in tqdm(hierarchy.items(), desc="Kapitel"):
        chap_title = chap["title"]
        for sec_id, sec in chap.get("sections", {}).items():
            sec_title = sec["title"]
            for subsec_id, subsec in sec.get("subsections", {}).items():
                subsec_title = subsec["title"]
                topic = subsec_title

                for i, entry in enumerate(subsec.get("content", [])):
                    entry_type = entry.get("type", "Sonstiges")
                    entry_text = entry.get("text", "").strip()
                    entry_details = entry.get("details", "").strip()
                    entry_page = entry.get("page", subsec.get("page", -1))

                    full_text = f"""Kapitel: {chap_title}
Abschnitt: {sec_title}
Unterabschnitt: {subsec_title}
Typ: {entry_type}
Seite: {entry_page}

{entry_text}
{entry_details}
""".strip()

                    entry_id = f"{subsec_id}_{entry_type}_{i}"

                    documents.append(full_text)
                    ids.append(entry_id)
                    metadatas.append({
                        "chapter": chap_id,
                        "chapter_title": chap_title,
                        "section": sec_id,
                        "section_title": sec_title,
                        "subsection": subsec_id,
                        "subsection_title": subsec_title,
                        "type": entry_type,
                        "page": entry_page,
                        "topic": topic,
                        "embedding_model": model_id
                    })
                    embeddings.append(model.encode(full_text))

    collection.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)
    print(f"Fertig: {len(documents)} Einträge mit Embeddings in {db_dir}/ gespeichert.")

if __name__ == "__main__":
    create_contextual_chroma()
