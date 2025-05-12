import json
import os
import tqdm
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import PersistentClient

DB_DIR = "04_chromaDB"
COLLECTION_NAME = "math_knowledge"

def extract_blocks(data):
    blocks = []
    counter = 0

    for chap_id, chap in data.items():
        chap_label = f'Kapitel {chap_id}: {chap["title"]}'
        blocks.append({
            "id": f'{chap_label}_{counter}',
            "text": chap.get("title", ""),
            "page": chap.get("page"),
            "type": "chapter"
        })
        counter += 1

        for sec_id, sec in chap['sections'].items():
            sec_label = f'{sec_id} {sec["title"]}'
            blocks.append({
                "id": f'{sec_label}_{counter}',
                "text": sec.get("title", ""),
                "page": sec.get("page"),
                "type": "section"
            })
            counter += 1

            for subsec_id, subsec in sec['subsections'].items():
                subsec_label = f'{subsec_id} {subsec["title"]}'
                blocks.append({
                    "id": f'{subsec_label}_{counter}',
                    "text": subsec.get("title", ""),
                    "page": subsec.get("page"),
                    "type": "subsection"
                })
                counter += 1

                for item in subsec.get('content', []):
                    blocks.append({
                        "id": f'{item["type"]}_{counter}',
                        "text": item.get("text", ""),
                        "page": item.get("page"),
                        "type": item.get("type", "")
                    })
                    counter += 1

    return blocks

def main():
    with open('01_hierarchy/hierarchy_prepared.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    blocks = extract_blocks(data)
    print(f"Erstelle Embeddings für {len(blocks)} Blöcke...")

    model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v2")

    texts = [b['text'] for b in blocks]
    ids = [b['id'] for b in blocks]
    metadatas = [{"page": b['page'], "type": b['type']} for b in blocks]

    embeddings = []
    batch_size = 16
    for i in tqdm.tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        emb = model.encode(batch)
        embeddings.extend(emb)

    os.makedirs(DB_DIR, exist_ok=True)
    chroma_client = PersistentClient(path=DB_DIR)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"ChromaDB-Collection '{COLLECTION_NAME}' mit {len(texts)} Dokumenten erstellt und gespeichert.")

if __name__ == "__main__":
    main()

