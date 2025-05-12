import os
import re
import json

GRAPH_PATH = "03_graph_search/search_results_latest.txt"
CHROMA_PATH = "05_chroma_output/chroma_results_latest.txt"
LATEX_DIR = "00_Latex_single_pages"
OUTPUT_DIR = "06_LLM_data_input"
USER_INPUT_PATH = "user_input.txt"
HIERARCHY_JSON = "01_hierarchy/hierarchy.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PROMPT = r"""
Du bist ein mathematisches Expertensystem und antwortest ausschließlich auf Deutsch. Beantworte die Frage basierend auf dem übergebenen Dokumentauszug - Notationen EXAKT wie in den Input Dateien gezeigt.
Gib ausschließlich eine vollständige und gültige LaTeX-Datei zurück, die direkt mit pdflatex kompiliert werden kann.
Verwende dazu folgende Struktur:

\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[ngerman]{babel}
\usepackage{amsmath, amssymb, mathtools}
\usepackage{geometry}
\geometry{margin=2.5cm}

Beginne den Text nach \begin{document} und beende ihn mit \end{document}.
""".strip()


def extract_pages(file_path):
    pages = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"Seite:?[\s]*(\d+)", line)
            if match:
                pages.add(int(match.group(1)))
    return pages


def extract_subsection_ids(file_path):
    ids = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"^\s*=== MATCH: (\d+\.\d+\.\d+)", line)
            if match:
                ids.append(match.group(1))
    return ids


def load_hierarchy(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_subsection_page_range(hierarchy, subsec_id):
    parts = subsec_id.split(".")
    if len(parts) != 3:
        return None

    chap, sec, sub = parts
    try:
        subsection = hierarchy[chap]["sections"][f"{chap}.{sec}"]["subsections"][f"{chap}.{sec}.{sub}"]
        base_page = subsection["page"]
        extra_pages = [c.get("page") for c in subsection.get("content", []) if "page" in c]
        max_page = max([base_page] + extra_pages)
        return range(base_page, max_page + 1)
    except KeyError:
        return None


def read_latex_pages(pages, latex_dir):
    latex_content = ""
    for page in sorted(pages):
        page_file = os.path.join(latex_dir, f"page_{page}.tex")
        if os.path.exists(page_file):
            with open(page_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Header entfernen
                content = re.sub(r"\\documentclass\[.*?\\begin\{document\}", "", content, flags=re.DOTALL)
                content = re.sub(r"\\end\{document\}", "", content)
                latex_content += f"\n### LaTeX-Seite {page} ###\n\n" + content.strip() + "\n"
    return latex_content


def build_llm_input(user_input):
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        graph = f.read().strip()
    with open(CHROMA_PATH, "r", encoding="utf-8") as f:
        chroma = f.read().strip()

    pages = extract_pages(GRAPH_PATH).union(extract_pages(CHROMA_PATH))

    # Seitenbereich erweitern basierend auf Subsection-IDs
    hierarchy = load_hierarchy(HIERARCHY_JSON)
    for subsec_id in extract_subsection_ids(GRAPH_PATH):
        page_range = get_subsection_page_range(hierarchy, subsec_id)
        if page_range:
            pages.update(page_range)

    latex_content = read_latex_pages(pages, LATEX_DIR)

    result = SYSTEM_PROMPT + "\n\n"
    result += "### USER-FRAGE ###\n" + user_input.strip() + "\n"
    result += "\n### GRAPH-SUCHE ###\n" + graph + "\n"
    result += "\n### CHROMA-SUCHE ###\n" + chroma + "\n"
    result += "\n### WICHTIGE LATEX-SEITEN ###\n" + latex_content.strip() + "\n"

    out_path = os.path.join(OUTPUT_DIR, "llm_input_latest.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"LLM-Eingabe gespeichert unter: {out_path}")
    return out_path


if __name__ == "__main__":
    if not os.path.exists(USER_INPUT_PATH):
        print("Fehler: 'user_input.txt' nicht gefunden.")
    else:
        with open(USER_INPUT_PATH, "r", encoding="utf-8") as f:
            user_input = f.read().strip()
        build_llm_input(user_input)
