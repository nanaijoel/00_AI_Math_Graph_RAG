import os
import subprocess
import shutil
from datetime import datetime
import re

LATEX_INPUT = "07_LLM_output/llm_output_latest.tex"
PDF_OUTPUT_DIR = "08_Final_PDF_output"

os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

def clean_latex_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Entferne Markdown-Reste
    if content.strip().startswith("```latex"):
        content = content.replace("```latex", "", 1)
    if content.strip().endswith("```"):
        content = content.rstrip("`").rstrip()

    # Entferne alle \includegraphics-Zeilen (auch mit optionalen Parametern)
    content = re.sub(r"\\includegraphics\[.*?\]\{.*?\}", "", content)
    content = re.sub(r"\\includegraphics\{.*?\}", "", content)

    # Repariere \begin{aligned} außerhalb von Mathe-Modus
    def wrap_aligned(match):
        return r"\\[\n" + match.group(0) + r"\n\\]"

    aligned_pattern = r"(?<!\\\[)\s*\\begin{aligned}.*?\\end{aligned}(?!\s*\\\])"
    content = re.sub(aligned_pattern, wrap_aligned, content, flags=re.DOTALL)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def compile_latex_to_pdf(latex_file, output_dir):
    clean_latex_file(latex_file)

    base_name = os.path.splitext(os.path.basename(latex_file))[0]
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ziel-Dateinamen vorbereiten
    pdf_final = os.path.join(output_dir, f"{base_name}_{date_str}.pdf")
    pdf_latest = os.path.join(output_dir, f"{base_name}_latest.pdf")

    # pdflatex zweimal ausführen
    for i in range(2):
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", latex_file],
                cwd=os.path.dirname(latex_file),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Kompilieren von LaTeX (Durchgang {i+1}):")
            print(e.stdout)
            return None

    generated_pdf = os.path.join(os.path.dirname(latex_file), base_name + ".pdf")
    if os.path.exists(generated_pdf):
        try:
            shutil.copyfile(generated_pdf, pdf_final)
            shutil.copyfile(generated_pdf, pdf_latest)
            print(f"PDF erfolgreich erstellt: {pdf_final}")
            print(f"Zusätzlich gespeichert als: {pdf_latest}")
            return pdf_final
        except Exception as e:
            print(f"Fehler beim Speichern der PDF-Dateien: {e}")
            return None
    else:
        print("PDF konnte nicht gefunden werden.")
        return None

if __name__ == "__main__":
    if not os.path.exists(LATEX_INPUT):
        print("Keine LaTeX-Eingabedatei gefunden.")
    else:
        compile_latex_to_pdf(os.path.abspath(LATEX_INPUT), PDF_OUTPUT_DIR)
