# Modules/fetch.py
# Fusion de fetch_effects.py et fetch_preset.py

import socket
import json
import os
import glob
import xml.etree.ElementTree as ET
from Core.configs.port_config import DEFAULT_PORTS


def fetch_effects():
    """Envoie la commande pour récupérer les effets depuis Premiere via TCP."""
    payload = {"action": "get_effects"}
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect(('127.0.0.1', DEFAULT_PORTS["tcp_port"]))
        s.sendall((json.dumps(payload) + "\n").encode())
        try:
            while True:
                data = s.recv(8192)
                if not data:
                    break
        except socket.timeout:
            pass
    except Exception as e:
        pass
    finally:
        if s:
            try:
                s.close()
            except Exception:
                pass


def fetch_presets(version_folder, progress_callback=None):
    """Extrait les presets depuis le fichier XML Premiere."""
    docs_path = os.path.expanduser(r"~\Documents\Adobe\Premiere Pro")
    target_dir = os.path.join(docs_path, version_folder)
    
    profile_dirs = glob.glob(os.path.join(target_dir, "Profile-*"))
    if not profile_dirs:
        raise Exception(f"No 'Profile-*' folder found in {target_dir}")
        
    xml_file = os.path.join(profile_dirs[0], "Effect Presets and Custom Items.prfpset")
    if not os.path.exists(xml_file):
        raise Exception("PRFPSET file not found.")

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
        items_map[obj_id] = {"Name": name, "Type": "PRST" if is_preset else "Unknown", "Children": []}

    root_node = root_xml.find(".//RootBin")
    if root_node is None:
        raise Exception("ERROR:Root folder not found in XML.")
        
    root_ref = root_node.get("ObjectRef")
    root_container = items_map.get(root_ref)

    if not root_container:
        raise Exception("ERROR:Root container not found.")

    custom_roots = []
    for cid in root_container["Children"]:
        node = items_map.get(cid)
        if node and node["Name"] not in ["Presets", "Root"]:
            custom_roots.append(node["Name"])

    if len(custom_roots) > 1:
        raise Exception(f"ERROR:Unstable structure! You have {len(custom_roots)} folders ({', '.join(custom_roots)}) at root outside 'Presets'. You must only have one maximum. Please clean up Premiere Pro.")

    extracted_presets = []

    def traverse(item_id, current_parent):
        elem = items_map.get(item_id)
        if not elem: return
        
        if elem["Type"] == "PRST":
            extracted_presets.append({
                "type": "PRST",
                "matchName": elem["Name"],
                "displayName": elem["Name"],
                "parentFolder": current_parent
            })
            if progress_callback:
                progress_callback(len(extracted_presets), elem["Name"])
            
        for child_id in elem["Children"]:
            child_elem = items_map.get(child_id)
            if child_elem:
                traverse(child_id, elem["Name"] if elem["Type"] == "Bin" else current_parent)

    for cid in root_container["Children"]:
        traverse(cid, items_map.get(cid, {}).get("Name", "Unknown"))

    from Core.paths import get_data_path
    data_dir = get_data_path()
    
    cache_file = os.path.join(data_dir, "presets_cache.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(extracted_presets, f, indent=4)
        

