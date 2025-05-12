import os
import requests
from openai import OpenAI

INPUT_FILE = "06_LLM_data_input/llm_input_latest.txt"
OUTPUT_DIR = "07_LLM_output"
USE_OPENAI = True  # True = OpenAI, False = Ollama
MODEL_NAME = "gpt-4-turbo" if USE_OPENAI else "qwen3:14b"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_ollama(prompt, system_prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print("Fehler beim Ollama-Aufruf:", response.status_code, response.text)
            return ""
    except Exception as e:
        print(f"Ausnahme bei Ollama: {e}")
        return ""


def run_openai(prompt, system_prompt):
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Fehler bei OpenAI-Aufruf: {e}")
        return ""


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        prompt = f.read()

    system_prompt = (
        "Du bist ein mathematisches Expertensystem und antwortest ausschließlich auf Deutsch. "
        "Beantworte die Frage basierend auf dem übergebenen Dokumentauszug. "
        "Gib ausschließlich eine vollständige und gültige LaTeX-Datei zurück, die direkt mit pdflatex kompiliert werden kann. "
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

    print("Sende Anfrage an", "OpenAI..." if USE_OPENAI else "Ollama...")
    response = run_openai(prompt, system_prompt) if USE_OPENAI else run_ollama(prompt, system_prompt)

    if not response.strip():
        print("Leere Antwort erhalten.")
        return

    tex_latest = os.path.join(OUTPUT_DIR, "llm_output_latest.tex")
    txt_latest = os.path.join(OUTPUT_DIR, "llm_output_latest.txt")

    with open(tex_latest, "w", encoding="utf-8") as f:
        f.write(response)
    with open(txt_latest, "w", encoding="utf-8") as f:
        f.write(response)

    print(f"LaTeX-Datei gespeichert: {tex_latest}")
    print(f"Rohtext-Datei gespeichert: {txt_latest}")


if __name__ == "__main__":
    main()
