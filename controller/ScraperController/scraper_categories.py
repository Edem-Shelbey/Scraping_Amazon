# controller/ScraperController/scraper_categories.py
from typing import List, Tuple, Optional
from ..fetcher import init_driver, fetch_page
from ..parser import extract_product_links, parse_product_page, get_subcategory_links_from_html
from ..utils import ensure_dir, safe_filename, jitter_sleep
from utils.downloader import download_image_to_dir
from urllib.parse import urlparse, parse_qs
import os, time, random

# optional driver-aware helper (from parser module)
try:
    from ..parser import get_subcategory_links
except Exception:
    get_subcategory_links = None

ROOT = os.path.join("data", "ScraperCategories")
ensure_dir(ROOT)


def _get_subcats(driver, category_url, max_subcats=5):
    """Use driver-aware parser if present, else HTML-only fallback (this function is internal).
    It always returns a dict of {name: url} (possibly empty).
    """
    if get_subcategory_links is not None:
        return get_subcategory_links(driver, category_url, max_subcats=max_subcats) or {}
    # fallback to fetch_page + html parser helper
    html = fetch_page(driver, category_url)
    return get_subcategory_links_from_html(html, max_subcats=max_subcats) or {}


def _scrape_subcategory(driver, name: str, url: str, out_dir: str,
                        max_products: int, max_pages: int):
    # delegate to the implementation in scraper_default to keep behavior identical
    mod = __import__("controller.ScraperController.scraper_default", fromlist=["*"])
    return mod._scrape_subcategory(driver, name, url, out_dir, max_products, max_pages)  # type: ignore


def _infer_category_name(parsed) -> str:
    """Return a readable category name: prefer k/q, else a meaningful path segment, else host prefix."""
    qs = parse_qs(parsed.query)
    name = qs.get("k", qs.get("q", [None]))[0]
    if name:
        return name
    path = (parsed.path or "").strip("/").split("/")
    if path:
        last = path[-1]
        if last and len(last) >= 4 and not last.isnumeric() and last.lower() not in {"b", "s", "gp", "ref", "dp"}:
            return last
    host = (parsed.netloc or "").replace("www.", "")
    if host:
        return host.split(".")[0]
    return "categorie"


def scrape_category(
    category_url: str,
    max_products: int,
    max_subcats: int,
    max_pages: int,
    headless: bool = True,
    driver: Optional[object] = None,
    base_dir: Optional[str] = None,
):
    """Scrape a single provided category URL.

    base_dir: optional directory where to write outputs for this category.
              If provided, outputs/subcategory folders are created under base_dir.
              If not, defaults to module ROOT (data/ScraperCategories).
    NOTE: This implementation does NOT include fallback behaviour: base_dir is respected if given.
    """
    parsed = urlparse(category_url)
    netloc = (parsed.netloc or "").lower()
    if not netloc or "amazon." not in netloc:
        print("URL invalide : veuillez fournir une URL Amazon (ex: https://www.amazon.fr/s?k=...).")
        return []

    category_name = _infer_category_name(parsed)
    safe_category = safe_filename(category_name)

    print(f"=== Scrape catégorie : {category_name} ===")

    created_driver = False
    if driver is None:
        driver = init_driver(headless=headless)
        created_driver = True

    # Determine out_root (no fallback logic here)
    out_root = base_dir if base_dir else ROOT
    ensure_dir(out_root)

    # storage tied to out_root (isolated state per base_dir)
    from ..saver import SimpleStorage
    storage = SimpleStorage(base_dir=out_root)

    results = []

    try:
        subcats = _get_subcats(driver, category_url, max_subcats=max_subcats)

        # If no subcategories found -> scrape the provided page and place results under out_root/<safe_category>/
        if not subcats:
            print("Aucune sous-catégorie trouvée -> scrape de la page fournie.")
            out_dir = os.path.join(out_root, safe_category)
            ensure_dir(out_dir)
            prods = _scrape_subcategory(driver, category_name, category_url, out_dir, max_products, max_pages)

            saved = []
            for p in prods:
                if storage.is_processed(p.asin):
                    continue
                storage.mark_processed(p.asin, safe_category)
                saved.append(p)
            results.append((category_name, category_url, len(saved)))
            return results

        # When subcategories are present, create each subfolder under out_root
        items = list(subcats.items())[:max_subcats]
        for i, (sub_name, sub_url) in enumerate(items, 1):
            print(f"\n--[{i}/{len(items)}] {sub_name} --")
            # out_dir is out_root so _scrape_subcategory will create the actual subfolder inside out_root
            prods = _scrape_subcategory(driver, sub_name, sub_url, out_root, max_products, max_pages)
            saved = []
            for p in prods:
                if storage.is_processed(p.asin):
                    continue
                storage.mark_processed(p.asin, safe_filename(sub_name))
                saved.append(p)
            results.append((sub_name, sub_url, len(saved)))
            time.sleep(random.uniform(0.5, 1.2))

    finally:
        if created_driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            storage.close()
        except Exception:
            pass

    return results
