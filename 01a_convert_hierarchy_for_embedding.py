import json

def prepare_hierarchy(input_file='01_hierarchy/hierarchy.json', output_file='01_hierarchy/hierarchy_prepared.json'):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def process_node(node):
        # Wenn Details vorhanden - setze als neuen Text
        if 'details' in node and node['details']:
            node['text'] = node['details']
        node.pop('details', None)

    for chap in data.values():
        process_node(chap)
        for sec in chap.get('sections', {}).values():
            process_node(sec)
            for subsec in sec.get('subsections', {}).values():
                process_node(subsec)
                for item in subsec.get('content', []):
                    process_node(item)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Neues JSON gespeichert unter: {output_file}")

if __name__ == "__main__":
    prepare_hierarchy()
