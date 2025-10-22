# view/report_format.py
from typing import Dict, Any, List

def format_subcat_text(rel: str, info: Dict[str,Any]) -> str:
    saved = info.get("saved", 0)
    found = info.get("found", "N/A")
    lines = [f"Sous-catégorie: {rel}",
             f"  Found: {found}   Saved: {saved}"]
    prods = info.get("products", [])
    if not prods:
        lines.append("  (aucun produit)\n")
        return "\n".join(lines)
    lines.append(f"  Produits ({len(prods)}):")
    for p in prods:
        name = p.get("name") or "<no name>"
        asin = p.get("asin") or ""
        url = p.get("url") or ""
        img = p.get("image") or ""
        part = f"    - {name}"
        if asin: part += f" ({asin})"
        if url: part += f" -> {url}"
        if img: part += f" [img: {img}]"
        lines.append(part)
    lines.append("")  # blank line
    return "\n".join(lines)

def build_text_report(report: Dict[str,Any]) -> str:
    ts = report.get("generated_at", "unknown")
    header = f"Rapport généré : {ts}\nDossier data root : {report.get('data_root')}\n\n"
    totals = report.get("totals", {})
    header += f"Total sous-catégories: {totals.get('subcategories',0)}  Found: {totals.get('found','N/A')}  Saved: {totals.get('saved',0)}\n\n"
    body_parts: List[str] = []
    for rel, info in sorted(report.get("subcats", {}).items()):
        body_parts.append(format_subcat_text(rel, info))
    return header + "\n".join(body_parts)
