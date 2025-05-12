import json
import networkx as nx
import os

def build_graph(hierarchy_path):
    with open(hierarchy_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    G = nx.DiGraph()
    node_data = {}

    for chap_id, chap in data.items():
        chap_label = f'Kapitel {chap_id}: {chap["title"]}'
        G.add_node(chap_label, type='chapter', page=chap.get('page'))
        node_data[chap_label] = chap

        for sec_id, sec in chap['sections'].items():
            sec_label = f'{sec_id} {sec["title"]}'
            G.add_node(sec_label, type='section', page=sec.get('page'))
            G.add_edge(chap_label, sec_label)
            node_data[sec_label] = sec

            for subsec_id, subsec in sec['subsections'].items():
                subsec_label = f'{subsec_id} {subsec["title"]}'
                G.add_node(subsec_label, type='subsection', page=subsec.get('page'))
                G.add_edge(sec_label, subsec_label)
                node_data[subsec_label] = subsec

                for item in subsec.get('content', []):
                    short = item.get("text", "").strip()[:30].replace(" ", "_").replace(":", "")
                    item_label = f'{subsec_id}_{item["type"]}_{short}'
                    G.add_node(item_label, type=item['type'], page=item.get('page'), details=item.get('details'))
                    G.add_edge(subsec_label, item_label)
                    node_data[item_label] = item
    return G, node_data


def multi_stage_search(G, node_data, search_terms, output_dir='03_graph_search/'):
    os.makedirs(output_dir, exist_ok=True)
    latest_filename = os.path.join(output_dir, 'search_results_latest.txt')
    search_results = []

    def log_match(match, f, max_page_dist=4):
        node_attr = G.nodes[match]
        base_page = node_attr.get('page')
        pages = {base_page} if base_page else set()

        entry = node_data.get(match)
        if entry:
            for child in entry.get('content', []):
                p = child.get('page')
                if p:
                    pages.add(p)

        if pages:
            page_range = f"{min(pages)}–{max(pages)}" if len(pages) > 1 else f"{min(pages)}"
            f.write(f"Seitenbereich: {page_range}\n")
        else:
            f.write("Seite: (unbekannt)\n")

        details = entry.get('details') or node_attr.get('details')
        if details:
            f.write(f"Details: {details}\n")

        f.write("\n→ Nachbarn (ausgehend):\n")
        for neighbor in G.successors(match):
            n_attr = G.nodes[neighbor]
            n_page = n_attr.get("page")
            if base_page and n_page and abs(n_page - base_page) <= max_page_dist:
                f.write(f"  → {neighbor} (Seite {n_page})\n")

        f.write("← Nachbarn (eingehend):\n")
        for neighbor in G.predecessors(match):
            n_attr = G.nodes[neighbor]
            f.write(f"  ← {neighbor} (Seite {n_attr.get('page')})\n")

        f.write("\n" + "=" * 50 + "\n\n")

    all_nodes = list(G.nodes())

    def find_matches_all(terms, node_types):
        return [n for n in all_nodes if G.nodes[n].get('type') in node_types and all(t in n.lower() for t in terms)]

    def find_matches_any(terms, node_types):
        return [n for n in all_nodes if G.nodes[n].get('type') in node_types and any(t in n.lower() for t in terms)]

    terms_lower = [t.lower() for t in search_terms]

    stages = [
        ("Alle Begriffe im Kapitel-/Abschnittstitel", find_matches_all(terms_lower, ['chapter', 'section'])),
        ("Alle Begriffe in Unterkapiteln", find_matches_all(terms_lower, ['subsection'])),
        ("Alle Begriffe in Inhalten (Definition, Satz, etc.)", find_matches_all(terms_lower, ['Definition', 'Satz', 'Beispiel', 'Bemerkungen', 'Anwendungen'])),
        ("Einzelbegriffe in Kapitel-/Abschnittstitel", find_matches_any(terms_lower, ['chapter', 'section'])),
        ("Einzelbegriffe in Unterkapiteln", find_matches_any(terms_lower, ['subsection'])),
        ("Einzelbegriffe in Inhalten (Definition, Satz, etc.)", find_matches_any(terms_lower, ['Definition', 'Satz', 'Beispiel', 'Bemerkungen', 'Anwendungen'])),
    ]

    with open(latest_filename, 'w', encoding='utf-8') as f:
        for stage_name, matches in stages:
            if not matches:
                continue
            f.write(f"##### STAGE: {stage_name} #####\n\n")
            for match in matches:
                log_match(match, f)
                search_results.append(match)

    print(f"Ergebnisse gespeichert in: {latest_filename}")
    return latest_filename


if __name__ == "__main__":
    hierarchy_file = '01_hierarchy/hierarchy.json'
    G, node_data = build_graph(hierarchy_file)

    search_input = input("Suchbegriff(e), z.B. 'Matrix Rechenregeln': ")
    multi_stage_search(G, node_data, search_input.split())
