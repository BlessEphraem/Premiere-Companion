import sys
import os
import glob
import json
import xml.etree.ElementTree as ET

# Force l'encodage de la console en UTF-8 pour éviter les crashs avec les caractères spéciaux
sys.stdout.reconfigure(encoding='utf-8')

def fetch_presets(version_folder):
    # 1. Construire le chemin vers le dossier Premiere Pro
    docs_path = os.path.expanduser(r"~\Documents\Adobe\Premiere Pro")
    target_dir = os.path.join(docs_path, version_folder)
    
    # 2. Trouver le dossier Profile-*
    profile_dirs = glob.glob(os.path.join(target_dir, "Profile-*"))
    if not profile_dirs:
        raise Exception(f"No 'Profile-*' folder found in {target_dir}")
        
    xml_file = os.path.join(profile_dirs[0], "Effect Presets and Custom Items.prfpset")
    if not os.path.exists(xml_file):
        raise Exception("PRFPSET file not found.")

    # 3. Parsing XML
    try:
        tree = ET.parse(xml_file)
        root_xml = tree.getroot()
    except Exception as e:
        raise Exception(f"Cannot load XML file: {e}")

    items_map = {}
    preset_ids = {p.get("ObjectID") for p in root_xml.findall(".//FilterPresetItem")}

    for bin_item in root_xml.findall(".//BinTreeItem"):
        obj_id = bin_item.get("ObjectID")
        name = bin_item.findtext("./TreeItemBase/Name") or "Unnamed"
        children = [i.get("ObjectRef") for i in bin_item.findall("./Items/Item")]
        items_map[obj_id] = {"Name": name, "Type": "Bin", "Children": children}

    for tree_item in root_xml.findall(".//TreeItem"):
        obj_id = tree_item.get("ObjectID")
        name = tree_item.findtext("./TreeItemBase/Name") or "Unnamed"
        data_node = tree_item.find("./TreeItemBase/Data")
        
        is_preset = (data_node is not None and data_node.get("ObjectRef") in preset_ids)
        items_map[obj_id] = {"Name": name, "Type": "Preset" if is_preset else "Unknown", "Children": []}

    root_node = root_xml.find(".//RootBin")
    if root_node is None:
        raise Exception(f"ERROR:Root folder not found in XML.")
        
    root_ref = root_node.get("ObjectRef")
    root_container = items_map.get(root_ref)

    if not root_container:
        raise Exception("ERROR:Root container not found.")

    # 4. Règle de sécurité : Maximum 1 dossier custom en dehors de "Presets"
    custom_roots = []
    for cid in root_container["Children"]:
        node = items_map.get(cid)
        if node and node["Name"] not in ["Presets", "Root"]:
            custom_roots.append(node["Name"])

    if len(custom_roots) > 1:
        raise Exception(f"ERROR:Unstable structure! You have {len(custom_roots)} folders ({', '.join(custom_roots)}) at root outside 'Presets'. You must only have one maximum. Please clean up Premiere Pro.")

    # 5. Extraction des presets
    extracted_presets = []

    def traverse(item_id, current_parent):
        elem = items_map.get(item_id)
        if not elem: return
        
        if elem["Type"] == "Preset":
            extracted_presets.append({
                "type": "Preset",
                "matchName": elem["Name"],
                "displayName": elem["Name"],
                "parentFolder": current_parent
            })
            
        for child_id in elem["Children"]:
            child_elem = items_map.get(child_id)
            if child_elem:
                # Transmet le nom du dossier actuel comme parent aux enfants
                traverse(child_id, elem["Name"] if elem["Type"] == "Bin" else current_parent)

    for cid in root_container["Children"]:
        traverse(cid, items_map.get(cid, {}).get("Name", "Unknown"))

    # 6. Sauvegarde en ABSOLU (pour éviter de sauvegarder le fichier n'importe où)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "Data")
    os.makedirs(data_dir, exist_ok=True)
    
    cache_file = os.path.join(data_dir, "presets_cache.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(extracted_presets, f, indent=4)
        
    print(f"SUCCESS:{len(extracted_presets)} presets imported successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_presets(sys.argv[1])
    else:
        print("ERROR:No version specified.")