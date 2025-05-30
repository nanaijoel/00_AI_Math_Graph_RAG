import json
from pathlib import Path
from tqdm import tqdm
import chromadb
from openai import OpenAI


def create_contextual_chroma(hierarchy_path="01_hierarchy/hierarchy.json", db_dir="04_chromaDB"):
    db_path = Path(db_dir)
    db_path.mkdir(exist_ok=True)

    client = OpenAI()
    embed_model = "text-embedding-ada-002"

    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_or_create_collection("math_contextual")

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

                combined_texts = []
                types = set()
                pages = set()

                for entry in subsec.get("content", []):
                    entry_type = entry.get("type", "Sonstiges")
                    entry_text = entry.get("text", "").strip()
                    entry_details = entry.get("details", "").strip()
                    entry_page = entry.get("page", subsec.get("page", -1))

                    if not entry_text and not entry_details:
                        continue

                    types.add(entry_type)
                    pages.add(entry_page)

                    text = f"{entry_type}:\n{entry_text}\n{entry_details}".strip()
                    combined_texts.append(text)

                if not combined_texts:
                    continue

                joined_text = "\n\n".join(combined_texts)

                full_text = (
                    f"Kapitel: {chap_title}\n"
                    f"Abschnitt: {sec_title}\n"
                    f"Unterabschnitt: {subsec_title}\n"
                    f"Typen: {sorted(types)}\n"
                    f"Seiten: {sorted(pages)}\n\n"
                    f"{joined_text}"
                )

                entry_id = f"{subsec_id}_full"

                documents.append(full_text)
                ids.append(entry_id)
                metadatas.append({
                    "chapter": chap_id,
                    "chapter_title": chap_title,
                    "section": sec_id,
                    "section_title": sec_title,
                    "subsection": subsec_id,
                    "subsection_title": subsec_title,
                    "page": ", ".join(str(p) for p in sorted(pages)),
                    "topic": topic,
                    "embedding_model": embed_model
                })

                try:
                    embedding = client.embeddings.create(
                        input=full_text,
                        model=embed_model
                    ).data[0].embedding
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Fehler beim Einbetten von {entry_id}: {e}")
                    embeddings.append([0.0] * 1536)  # Dummy-Vektor

    collection.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)
    print(f"\nFertig: {len(documents)} Einträge gespeichert in → {db_dir}/")

if __name__ == "__main__":
    create_contextual_chroma()
