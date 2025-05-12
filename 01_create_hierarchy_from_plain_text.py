import re
import json

input_file = "00_plain_text/plain_text.txt"
output_file = "01_hierarchy/hierarchy.json"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

hierarchy = {}
current_chapter = None
current_section = None
current_subsection = None
current_page = None
next_page = None  # merkt sich kommende Seitenzahl

i = 0
while i < len(lines):
    line = lines[i]

    # Seitenwechsel vorbereiten (erst später umschalten!)
    page_match = re.match(r"^===== Seite (\d+) =====$", line)
    if page_match:
        next_page = int(page_match.group(1))
        i += 1
        continue

    # Seite umschalten, sobald wir zu einem inhaltlichen Block kommen
    if next_page is not None:
        current_page = next_page
        next_page = None

    chapter_match = re.match(r"Kapitel\s+(\d+)", line)
    if chapter_match:
        chapter = chapter_match.group(1)
        title = lines[i + 1] if i + 1 < len(lines) else ""
        hierarchy[chapter] = {"title": title, "page": current_page, "sections": {}}
        current_chapter = chapter
        current_section = None
        current_subsection = None
        i += 2
        continue

    # Abschnitt (1.1)
    section_match = re.match(r"^(\d+\.\d+)$", line)
    if section_match and current_chapter:
        sec_id = section_match.group(1)
        sec_title = lines[i + 1] if i + 1 < len(lines) else ""
        hierarchy[current_chapter]["sections"][sec_id] = {
            "title": sec_title,
            "page": current_page,
            "subsections": {}
        }
        current_section = sec_id
        current_subsection = None
        i += 2
        continue

    # Unterabschnitt (1.1.1)
    subsection_match = re.match(r"^(\d+\.\d+\.\d+)$", line)
    if subsection_match and current_chapter and current_section:
        subsec_id = subsection_match.group(1)
        subsec_title = lines[i + 1] if i + 1 < len(lines) else ""
        hierarchy[current_chapter]["sections"][current_section]["subsections"][subsec_id] = {
            "title": subsec_title,
            "page": current_page,
            "content": []
        }
        current_subsection = subsec_id
        i += 2
        continue

    # Keyword-Inhalte
    keyword_match = re.match(r"^(Satz|Definition|Beweis|Beispiele|Bemerkungen|Anwendungen)(.*)", line)
    if keyword_match:
        keyword_type = keyword_match.group(1)
        keyword_text = line
        text_block = []
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if re.match(r"^(===== Seite \d+ =====|Kapitel\s+\d+|\d+\.\d+|\d+\.\d+\.\d+|Satz|Definition|Beweis|Beispiele|Bemerkungen|Anwendungen)", next_line):
                break
            text_block.append(next_line)
            i += 1
        entry = {"type": keyword_type, "text": keyword_text, "details": " ".join(text_block), "page": current_page}
        if current_subsection:
            hierarchy[current_chapter]["sections"][current_section]["subsections"][current_subsection]["content"].append(entry)
        else:
            if "content" not in hierarchy[current_chapter]["sections"][current_section]:
                hierarchy[current_chapter]["sections"][current_section]["content"] = []
            hierarchy[current_chapter]["sections"][current_section]["content"].append(entry)
        continue

    i += 1


with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(hierarchy, f, indent=2, ensure_ascii=False)

