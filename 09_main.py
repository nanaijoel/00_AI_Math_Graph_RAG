import os
import sys
import subprocess
from datetime import datetime

def call_script(script_name, *args):
    print(f"\nStarte: {script_name} {' '.join(args)}")
    result = subprocess.run([sys.executable, script_name, *args])
    if result.returncode != 0:
        print(f"Fehler beim Ausführen von {script_name}")
        exit(result.returncode)

def main():
    print("Mathe-RAG-System wird gestartet...")

    user_input = input("Was möchtest du wissen? ").strip()
    if not user_input:
        print("Kein Input eingegeben. Vorgang abgebrochen.")
        return

    with open("user_input.txt", "w", encoding="utf-8") as f:
        f.write(user_input)

    call_script("03_graph_search_keywords.py", user_input)

    call_script("05_create_vector_guess.py", user_input)

    call_script("06_prepare_LLM_input.py", user_input)

    call_script("07_run_LLM.py")

    output_dir = "07_LLM_output"
    latest_tex = None

    if os.path.exists(output_dir):
        output_files = sorted(os.listdir(output_dir), reverse=True)
        for f in output_files:
            if f.endswith(".tex"):
                latest_tex = f
                print(f"\nLetztes Ergebnis gespeichert in:\n   {output_dir}/{f}")
                break
        else:
            print("Keine .tex-Datei im Output-Verzeichnis gefunden.")
    else:
        print("Output-Verzeichnis '07_LLM_output' fehlt.")

    if latest_tex:
        call_script("08_convert_latex_to_pdf.py")


if __name__ == "__main__":
    main()
