# view/report_collect.py
import os, json
from typing import List, Dict, Any

DATA_ROOT = "data"

def find_product_files(data_root: str = DATA_ROOT) -> List[str]:
    out = []
    for root, _, files in os.walk(data_root):
        for fn in files:
            low = fn.lower()
            if low in ("products.json", "grosses.json", "gross.json"):
                out.append(os.path.join(root, fn))
            elif low.endswith(".json") and ("products" in low or "gross" in low):
                out.append(os.path.join(root, fn))
    return out

def read_products(path: str) -> List[Dict[str,Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("products","items","results"):
            if isinstance(data.get(k), list):
                return data[k]
        vals = [v for v in data.values() if isinstance(v, dict)]
        if vals:
            return vals
    return []

def collect_by_subdir(data_root: str = DATA_ROOT) -> Dict[str, Dict[str,Any]]:
    files = find_product_files(data_root)
    mapping: Dict[str, Dict[str,Any]] = {}
    for p in files:
        rel = os.path.relpath(os.path.dirname(p), data_root).replace("\\","/")
        lst = read_products(p)
        if rel not in mapping:
            mapping[rel] = {"products": [], "example_path": p}
        mapping[rel]["products"].extend(lst)
    for k in mapping:
        mapping[k]["count"] = len(mapping[k]["products"])
    return mapping
