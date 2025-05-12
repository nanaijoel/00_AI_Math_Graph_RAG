import os
import re

GRAPH_PATH = "03_graph_search/search_results_latest.txt"
CHROMA_PATH = "05_chroma_output/chroma_results_latest.txt"
LATEX_DIR = "00_Latex_single_pages"
OUTPUT_DIR = "06_LLM_data_input"
USER_INPUT_PATH = "user_input.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Systemprompt als fester Bestandteil des Prompts
SYSTEM_PROMPT = (
    "Du bist ein mathematisches Expertensystem und antwortest ausschließlich auf Deutsch. "
    "Beantworte die Frage basierend auf dem übergebenen Dokumentauszug - Notationen so wie in den Input Dateien gezeigt."
    "Gib ausschließlich eine vollständige und gültige LaTeX-Datei zurück, die direkt mit pdflatex kompiliert werden kann."
    "Verwende dazu folgende Struktur:\n\n"
    "\\documentclass[a4paper,12pt]{article}\n"
    "\\usepackage[utf8]{inputenc}\n"
    "\\usepackage[T1]{fontenc}\n"
    "\\usepackage[ngerman]{babel}\n"
    "\\usepackage{amsmath, amssymb, mathtools}\n"
    "\\usepackage{geometry}\n"
    "\\geometry{margin=2.5cm}\n\n"
    "Beginne den Text nach \\begin{document} und beende ihn mit \\end{document}."
)


def extract_pages(file_path):
    pages = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"Seite:?[\s]*(\d+)", line)
            if match:
                pages.add(int(match.group(1)))
    return pages

def read_latex_pages(pages, latex_dir):
    latex_content = ""
    for page in sorted(pages):
        page_file = os.path.join(latex_dir, f"page_{page}.tex")
        if os.path.exists(page_file):
            with open(page_file, "r", encoding="utf-8") as f:
                content = f.read()
                # LaTeX-Header entfernen
                content = re.sub(r"\\documentclass\[.*?\\begin\{document\}", "", content, flags=re.DOTALL)
                content = re.sub(r"\\end\{document\}", "", content)
                latex_content += f"\n### LaTeX-Seite {page} ###\n\n" + content.strip() + "\n"
    return latex_content

def build_llm_input(user_input):
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        graph = f.read().strip()
    with open(CHROMA_PATH, "r", encoding="utf-8") as f:
        chroma = f.read().strip()

    all_pages = extract_pages(GRAPH_PATH).union(extract_pages(CHROMA_PATH))
    latex_content = read_latex_pages(all_pages, LATEX_DIR)

    result = SYSTEM_PROMPT.strip() + "\n\n"
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

