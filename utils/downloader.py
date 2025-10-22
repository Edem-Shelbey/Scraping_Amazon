# utils/downloader.py
import os
import requests
from urllib.parse import urlparse
from requests.exceptions import RequestException

def _guess_ext_from_url(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext and len(ext) <= 5:
        return ext
    return ".jpg"

def download_image(url: str, out_path: str, timeout: int = 10, retries: int = 2) -> bool:
    """
    Télécharge l'image depuis `url` et écrit dans `out_path`.
    Retourne True si ok, False sinon.
    Gestion simple de retry + écriture atomique.
    """
    if not url:
        return False
    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)
    tmp = out_path + ".tmp"
    for attempt in range(retries + 1):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
                r.raise_for_status()
                # try to guess extension from content-type if missing
                content_type = r.headers.get("content-type", "")
                ext = os.path.splitext(out_path)[1]
                if not ext:
                    if "image/" in content_type:
                        guessed = "." + content_type.split("/")[-1].split(";")[0]
                        if len(guessed) <= 5:
                            out_path = os.path.splitext(out_path)[0] + guessed
                            tmp = out_path + ".tmp"
                    else:
                        guessed = _guess_ext_from_url(url)
                        out_path = os.path.splitext(out_path)[0] + guessed
                        tmp = out_path + ".tmp"
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            # move tmp to final atomically
            os.replace(tmp, out_path)
            return True
        except RequestException:
            # remove tmp if exists
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            if attempt < retries:
                continue
            return False

# -----------------------------------------
# Helper convenience: construit le chemin du fichier, appelle download_image
# et renvoie le chemin relatif (ou None).
def download_image_to_dir(url: str, images_dir: str, product_name: str, asin: str, safe_fn):
    """
    url: image url
    images_dir: dossier où enregistrer
    product_name: nom produit (pour générer filename)
    asin: ASIN (pour filename)
    safe_fn: fonction safe_filename(name)->str déjà fournie par utils
    Retourne: path relatif (str) si ok, None sinon.
    """
    if not url:
        return None
    os.makedirs(images_dir, exist_ok=True)
    # extension detection: try parse from url path
    ext = os.path.splitext(urlparse(url).path)[1] or ""
    safe_name = safe_fn(product_name)[:80]
    if not ext:
        # build tmp name without ext, download_image will guess from headers/url
        out_path = os.path.join(images_dir, f"{safe_name}_{asin}")
    else:
        out_path = os.path.join(images_dir, f"{safe_name}_{asin}{ext}")
    ok = download_image(url, out_path)
    if not ok:
        return None
    # ensure returned path has final extension (download_image may have added it)
    # we find the file that starts with safe_name_asin in images_dir
    base = f"{safe_name}_{asin}"
    for fname in os.listdir(images_dir):
        if fname.startswith(base):
            return os.path.join(images_dir, fname)
    return None
