import fitz

def extract_pdf_text(input_pdf_path, output_txt_path):

    doc = fitz.open(input_pdf_path)

    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n\n===== Seite {page_num + 1} =====\n\n{text}"

    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"Extraktion abgeschlossen: {output_txt_path}")

extract_pdf_text('Mathe_Skript_trimmed.pdf', '00_plain_text/plain_text.txt')
