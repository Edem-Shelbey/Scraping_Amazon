# view/report.py
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

REPORTS_DIR = os.path.join("view", "reports")
DATA_ROOT = "data"

def ensure_reports_dir(path: str = REPORTS_DIR):
    os.makedirs(path, exist_ok=True)

def find_products_files(data_root: str = DATA_ROOT) -> List[str]:
    """Trouve tous les fichiers 'products.json' sous data_root."""
    files = []
    for root, _, filenames in os.walk(data_root):
        for fn in filenames:
            if fn.lower() == "products.json":
                files.append(os.path.join(root, fn))
    return files

def read_products(path: str) -> List[Dict[str, Any]]:
    """Lit un products.json et retourne la liste d'objets (tolérant)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # si format { "products": [...] } ou similaire
        for key in ("products", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        # sinon si dictionnaire de produits, tenter d'extraire
        vals = []
        for v in data.values():
            if isinstance(v, dict) or isinstance(v, list):
                vals.append(v)
        # on ne tente pas des conversions complexes — renvoyer vide si doute
    return []

def _product_name_from_record(rec: Any) -> str:
    """Récupère un nom lisible depuis un enregistrement produit."""
    if isinstance(rec, dict):
        name = rec.get("name") or rec.get("title") or rec.get("product_name")
        if name and isinstance(name, str) and name.strip():
            return name.strip()
        # fallback: ASIN or sku to help identification
        asin = rec.get("asin") or rec.get("ASIN") or rec.get("sku")
        if asin:
            return f"{asin}"
    return "Produit sans nom"

def build_report(data_root: str = DATA_ROOT) -> Dict[str, Any]:
    """
    Construit un rapport minimaliste :
    - totals: nombre de sous-catégories et nombre total de produits sauvegardés
    - subcats: mapping subcat_name -> {'saved': int, 'products': [names...]}
    """
    files = find_products_files(data_root)
    subcats: Dict[str, Dict[str, Any]] = {}
    total_products = 0

    for p in files:
        # dériver le nom de sous-catégorie depuis le répertoire parent du products.json
        rel_dir = os.path.relpath(os.path.dirname(p), data_root).replace("\\", "/")
        sub_name = rel_dir.split("/")[-1] if rel_dir else os.path.basename(os.path.dirname(p))
        prods = read_products(p)
        names = []
        for rec in prods:
            n = _product_name_from_record(rec)
            names.append(n)
        saved = len(names)
        if sub_name in subcats:
            # si plusieurs products.json pour la même sous-catég (peu probable), on concatène
            subcats[sub_name]["products"].extend(names)
            subcats[sub_name]["saved"] += saved
        else:
            subcats[sub_name] = {"saved": saved, "products": names, "example_path": p}
        total_products += saved

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "totals": {"sous_categories": len(subcats), "sauvegardes": total_products},
        "subcats": subcats
    }
    return report

def build_text_report_simple(report: Dict[str, Any]) -> str:
    """Formate le rapport en texte simple, en français, sans chemins ni liens."""
    lines: List[str] = []
    generated = report.get("generated_at", "")
    totals = report.get("totals", {})
    scount = totals.get("sous_categories", 0)
    saved = totals.get("sauvegardes", 0)

    lines.append(f"Rapport généré : {generated}")
    lines.append(f"Total sous-catégories : {scount}    Produits extraits : {saved}\n")

    subcats = report.get("subcats", {})
    if not subcats:
        lines.append("Aucune sous-catégorie trouvée.\n")
        return "\n".join(lines)

    for sub_name, info in sorted(subcats.items()):
        lines.append(f"Sous-catégorie : {sub_name}")
        lines.append(f"  Produits extraits : {info.get('saved',0)}")
        prods: List[str] = info.get("products", [])
        if not prods:
            lines.append("    (aucun produit)")
        else:
            for n in prods:
                # n est déjà une string (nom du produit)
                lines.append(f"    - {n}")
        lines.append("")  # ligne vide entre sous-catégories

    return "\n".join(lines)

def generate_text_reports(report: Dict[str, Any], out_dir: str = REPORTS_DIR) -> Dict[str, str]:
    """
    Écrit trois fichiers texte simples:
      - report_default.txt
      - report_categories.txt
      - report_all_categories.txt
    Tous utilisent le même contenu minimaliste en français.
    """
    ensure_reports_dir(out_dir)
    text = build_text_report_simple(report)
    paths = {}
    mapping = {
        "default": "report_default.txt",
        "categories": "report_categories.txt",
        "all_categories": "report_all_categories.txt"
    }
    for k, fn in mapping.items():
        path = os.path.join(out_dir, fn)
        try:
            with open(path, "w", encoding="utf-8") as f:
                header = "=== Rapport ===\n\n" if k == "default" else f"=== Rapport ({k}) ===\n\n"
                f.write(header + text)
            paths[k] = path
        except Exception as e:
            paths[k] = f"(erreur écriture: {e})"
    return paths

def save_report_json(report: Dict[str, Any], out_dir: str = REPORTS_DIR) -> str:
    """Archive un JSON complet (avec timestamp) et met à jour report_latest.json"""
    ensure_reports_dir(out_dir)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"report_{ts}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        latest = os.path.join(out_dir, "report_latest.json")
        try:
            with open(latest, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return path
    except Exception as e:
        return f"(erreur écriture JSON: {e})"

def save_last_scrape(kind: str, results: List[Tuple[str, str, int]], out_dir: str = REPORTS_DIR) -> Dict[str, str]:
    """
    Sauvegarde un résumé du dernier run (json + texte luible).
    Résumé minimaliste : name / url / saved.
    """
    ensure_reports_dir(out_dir)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(out_dir, f"last_run_{kind}_{ts}.json")
    txt_path = os.path.join(out_dir, f"last_run_{kind}.txt")
    try:
        payload = {"generated_at": datetime.utcnow().isoformat()+"Z", "kind": kind,
                   "summary":[{"name": r[0], "url": r[1], "saved": int(r[2])} for r in results]}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Résumé dernier run ({kind}) - {payload['generated_at']}\n\n")
            if not results:
                f.write("Aucun élément collecté.\n")
            else:
                for name, url, saved in results:
                    f.write(f" - {name} : {saved} produits\n")
        # regénérer rapports globaux
        rpt = build_report()
        generate_text_reports(rpt)
        save_report_json(rpt)
        return {"json": json_path, "txt": txt_path}
    except Exception as e:
        return {"error": str(e)}

def read_text_report(kind: str, out_dir: str = REPORTS_DIR) -> str:
    mapping = {
        "default": os.path.join(out_dir, "report_default.txt"),
        "categories": os.path.join(out_dir, "report_categories.txt"),
        "all_categories": os.path.join(out_dir, "report_all_categories.txt")
    }
    path = mapping.get(kind)
    if not path or not os.path.exists(path):
        return f"(Fichier {os.path.basename(path) if path else kind} introuvable. Générez le rapport d'abord.)"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"(Erreur lecture {path}: {e})"

def interactive_report_menu():
    ensure_reports_dir()
    while True:
        print("\n=== MENU RAPPORTS ===")
        print("1) Afficher le rapport du scrape par défaut")
        print("2) Afficher le rapport du scrape de la catégorie (dernier run)")
        print("3) Afficher le rapport du scrape de toutes les catégories (dernier run)")
        print("4) Regénérer et sauvegarder les rapports")
        print("0) Retour")
        c = input("Choix : ").strip()
        if c == "1":
            content = read_text_report("default")
            if "introuvable" in content:
                rpt = build_report(); generate_text_reports(rpt); save_report_json(rpt); content = read_text_report("default")
            print("\n" + content)
        elif c == "2":
            content = read_text_report("categories")
            if "introuvable" in content:
                rpt = build_report(); generate_text_reports(rpt); save_report_json(rpt); content = read_text_report("categories")
            print("\n" + content)
        elif c == "3":
            content = read_text_report("all_categories")
            if "introuvable" in content:
                rpt = build_report(); generate_text_reports(rpt); save_report_json(rpt); content = read_text_report("all_categories")
            print("\n" + content)
        elif c == "4":
            rpt = build_report(); generate_text_reports(rpt); p = save_report_json(rpt); print(f"Rapports régénérés. JSON archivé: {p}")
        elif c == "0":
            break
        else:
            print("Choix invalide.")
