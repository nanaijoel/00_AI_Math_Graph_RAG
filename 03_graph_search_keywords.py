import json
import networkx as nx
from difflib import get_close_matches
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
                    item_label = f'{item["type"]}: {item["text"]}'
                    G.add_node(item_label, type=item['type'], page=item.get('page'), details=item.get('details'))
                    G.add_edge(subsec_label, item_label)
                    node_data[item_label] = item
    return G, node_data


def multi_stage_search(G, node_data, search_terms, output_dir='03_graph_search/'):
    os.makedirs(output_dir, exist_ok=True)
    latest_filename = os.path.join(output_dir, 'search_results_latest.txt')
    search_results = []

    def log_match(match, f):
        node_attr = G.nodes[match]
        f.write(f"=== MATCH: {match} ===\n")
        if 'page' in node_attr:
            f.write(f"Seite: {node_attr.get('page')}\n")
        details = node_data.get(match, {}).get('details') or node_attr.get('details')
        if details:
            f.write(f"Details: {details}\n")
        f.write("\n→ Nachbarn (ausgehend):\n")
        for neighbor in G.successors(match):
            n_attr = G.nodes[neighbor]
            f.write(f"  → {neighbor} (Seite {n_attr.get('page')})\n")
        f.write("← Nachbarn (eingehend):\n")
        for neighbor in G.predecessors(match):
            n_attr = G.nodes[neighbor]
            f.write(f"  ← {neighbor} (Seite {n_attr.get('page')})\n")
        f.write("\n" + "="*50 + "\n\n")

    all_nodes = list(G.nodes())
    lowercase_nodes = [n.lower() for n in all_nodes]

    def find_matches(keyword, node_types):
        return [n for n in all_nodes if any(kw in n.lower() for kw in keyword) and G.nodes[n].get('type') in node_types]

    with open(latest_filename, 'w', encoding='utf-8') as f:
        stages = [
            ("Kapitel-/Abschnittstitel mit 'matrix'", find_matches(['matrix'], ['chapter', 'section'])),
            ("Kapitel-/Abschnittstitel mit 'matrix rechenregeln'", find_matches(['matrix', 'rechenregeln'], ['chapter', 'section'])),
            ("Unterkapitel mit 'matrix'", find_matches(['matrix'], ['subsection'])),
            ("Unterkapitel mit 'rechenregeln'", find_matches(['rechenregeln'], ['subsection'])),
        ]

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

    search_input = input("Suchbegriff(e), z. B. 'Matrix Rechenregeln': ")
    multi_stage_search(G, node_data, search_input.split())
