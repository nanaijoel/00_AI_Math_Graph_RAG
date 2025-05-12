import json
import networkx as nx


# Build graph
with open('01_hierarchy/hierarchy.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

G = nx.DiGraph()
for chap_id, chap in data.items():
    chap_label = f'Kapitel {chap_id}: {chap["title"]}'
    G.add_node(chap_label, type='chapter')

    for sec_id, sec in chap['sections'].items():
        sec_label = f'{sec_id} {sec["title"]}'
        G.add_node(sec_label, type='section')
        G.add_edge(chap_label, sec_label)

        for subsec_id, subsec in sec['subsections'].items():
            subsec_label = f'{subsec_id} {subsec["title"]}'
            G.add_node(subsec_label, type='subsection')
            G.add_edge(sec_label, subsec_label)

            for item in subsec.get('content', []):
                item_label = f'{item["type"]}: {item["text"][:50]}...'  # nur ersten 50 Zeichen
                G.add_node(item_label, type=item['type'])
                G.add_edge(subsec_label, item_label)


with open('02_knowledge_graph/graph_structure.txt', 'w', encoding='utf-8') as f:
    f.write("Nodes:\n")
    for node, attr in G.nodes(data=True):
        f.write(f"- {node} (type={attr['type']})\n")

    f.write("\nEdges:\n")
    for source, target in G.edges():
        f.write(f"- {source} → {target}\n")

nx.write_graphml(G, '02_knowledge_graph/graph.graphml')
print("GraphML-Datei wurde gespeichert unter: 02_knowledge_graph/graph.graphml")
