# controller/saver.py
import os
import json
import tempfile
from typing import List, Any, Dict, Optional

PROCESSED_FILENAME = ".processed.json"

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _atomic_write(path: str, data: str):
    """
    Écrit de manière atomique : écrit dans un fichier temporaire puis remplace.
    Permet d'éviter les fichiers corrompus si le process crash pendant l'écriture.
    """
    dirn = os.path.dirname(path) or "."
    fd, tmppath = tempfile.mkstemp(dir=dirn, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmppath, path)
    finally:
        # si quelque chose a échoué et le tmp existe encore, tente de le supprimer
        if os.path.exists(tmppath):
            try:
                os.remove(tmppath)
            except Exception:
                pass

def save_products_json(products: List[Any], target_dir: str, filename: str = "products.json") -> str:
    """
    Sauvegarde une liste d'objets 'product' en JSON lisible.
    Chaque élément est transformé par, dans l'ordre :
      - p.to_dict() si disponible
      - p.__dict__ si p est un objet
      - sinon str(p)
    Retourne le chemin du fichier écrit.
    """
    _ensure_dir(target_dir)
    path = os.path.join(target_dir, filename)
    records = []
    for p in products:
        try:
            if hasattr(p, "to_dict") and callable(getattr(p, "to_dict")):
                records.append(p.to_dict())
            elif isinstance(p, dict):
                records.append(p)
            elif hasattr(p, "__dict__"):
                records.append({k: v for k, v in p.__dict__.items() if not k.startswith("_")})
            else:
                records.append({"repr": str(p)})
        except Exception:
            try:
                records.append({"repr": str(p)})
            except Exception:
                records.append({})
    # write atomically
    json_text = json.dumps(records, ensure_ascii=False, indent=2)
    _atomic_write(path, json_text)
    return path

class SimpleStorage:
    """
    Stocke les ASINs déjà traités pour éviter les doublons entre runs.
    Structure sur disque (JSON) : { "<tag>": {"asins": ["B0...","B1..."]}, ... }
    - base_dir/.processed.json est utilisé.
    - is_processed(asin) vérifie si l'asin existe pour n'importe quel tag.
    - mark_processed(asin, tag) ajoute l'asin au tag et sauvegarde sur disque.
    """
    def __init__(self, base_dir: str = "data"):
        _ensure_dir(base_dir)
        self._path = os.path.join(base_dir, PROCESSED_FILENAME)
        self._data: Dict[str, Dict[str, List[str]]] = {}
        # tentative de chargement (tolérante)
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    # normaliser la structure : chaque valeur doit être dict avec key "asins" -> list
                    for k, v in raw.items():
                        if isinstance(v, dict):
                            asins = v.get("asins", [])
                            if isinstance(asins, list):
                                self._data[k] = {"asins": [str(x) for x in asins]}
                            else:
                                self._data[k] = {"asins": []}
                        elif isinstance(v, list):
                            # cas ancien : tag -> [asins]
                            self._data[k] = {"asins": [str(x) for x in v]}
                        else:
                            self._data[k] = {"asins": []}
                else:
                    self._data = {}
        except FileNotFoundError:
            self._data = {}
        except Exception:
            # en cas d'erreur, initialise vide (ne crash pas)
            self._data = {}

    def is_processed(self, asin: Optional[str]) -> bool:
        """
        Retourne True si l'ASIN est trouvé dans n'importe quel tag.
        Si asin est falsy (None/""), retourne False.
        """
        if not asin:
            return False
        a = str(asin)
        for info in self._data.values():
            try:
                if a in info.get("asins", []):
                    return True
            except Exception:
                continue
        return False

    def mark_processed(self, asin: Optional[str], tag: str):
        """
        Ajoute l'ASIN sous le tag donné et sauvegarde sur disque.
        Tag vide est remplacé par "default".
        """
        if not asin:
            return
        if not tag:
            tag = "default"
        a = str(asin)
        if tag not in self._data:
            self._data[tag] = {"asins": []}
        if a not in self._data[tag]["asins"]:
            self._data[tag]["asins"].append(a)
            # sauvegarde immédiate (persist)
            self._save()

    def _save(self):
        try:
            json_text = json.dumps(self._data, ensure_ascii=False, indent=2)
            _atomic_write(self._path, json_text)
        except Exception:
            # ne doit pas lever pour ne pas casser le scraper
            try:
                # fallback simple write
                with open(self._path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def close(self):
        """Sauvegarde et ferme (interface simple)."""
        self._save()
