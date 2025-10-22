from typing import List, Tuple
from ..fetcher import init_driver, fetch_page
from ..parser import extract_product_links, parse_product_page, get_subcategory_links_from_html
from ..utils import ensure_dir, safe_filename, jitter_sleep
from utils.downloader import download_image_to_dir
from view.progress import get_progress
import os, time, random


try:
    from ..parser import get_subcategory_links  # may not exist
except Exception:
    get_subcategory_links = None

def _get_subcats(driver, category_url, max_subcats=5):
    if get_subcategory_links is not None:
        try:
            return get_subcategory_links(driver, category_url, max_subcats=max_subcats)
        except Exception:
            pass
    html = ""
    try:
        html = fetch_page(driver, category_url)
    except Exception:
        try:
            html = getattr(driver, "page_source", "") or ""
        except Exception:
            html = ""
    try:
        return get_subcategory_links_from_html(html, max_subcats=max_subcats) or {}
    except Exception:
        return {}

def _scrape_subcategory(driver, name: str, url: str, out_dir: str,
                        max_products: int, max_pages: int) -> List[object]:
    safe_name = safe_filename(name)
    sub_dir = os.path.join(out_dir, safe_name)
    images_dir = os.path.join(sub_dir, "images")
    ensure_dir(sub_dir)
    ensure_dir(images_dir)

    products = []
    page_url = url
    page_count = 0
    collected = 0

    from ..saver import save_products_json

    with get_progress(total=max_products, desc=safe_name, unit="prod", ncols=80) as pbar:
        while page_url and page_count < max_pages and collected < max_products:
            html = fetch_page(driver, page_url)
            jitter_sleep(0.5, 1.2)
            links = extract_product_links(html)
            if not links:
                break

            for asin, p_url in links:
                if collected >= max_products:
                    break
                try:
                    prod_html = fetch_page(driver, p_url)
                    info = parse_product_page(prod_html)
                    namep = info.get("name")
                    if not namep:
                        continue

                    from model.product import Product
                    prod = Product(
                        asin=asin,
                        name=namep,
                        desc=info.get("description"),
                        price=info.get("price"),
                        url=p_url,
                        subcategory=name,
                    )
                    prod.brand = info.get("brand")
                    prod.image_url = info.get("image_url")

                    if prod.image_url:
                        saved = download_image_to_dir(prod.image_url, images_dir, prod.name, prod.asin, safe_filename)
                        prod.image_local = os.path.relpath(saved) if saved else None

                    products.append(prod)
                    collected += 1
                    try:
                        pbar.update(1)
                        pbar.set_description(f"{safe_name} {collected}/{max_products}")
                    except Exception:
                        pass

                except Exception as e:
                    try:
                        from tqdm import tqdm
                        tqdm.write(f"      Erreur produit {asin}: {e}")
                    except Exception:
                        print(f"      Erreur produit {asin}: {e}")
                    continue

                jitter_sleep(0.2, 0.6)

            page_count += 1
            page_url = None

    file_path = save_products_json(products, sub_dir)
    print(f"    Sauvegardé {len(products)} produits -> {file_path}")
    return products


def scrape_default(category_url: str, max_products: int, max_subcats: int, max_pages: int, headless: bool = True):
    """Auto-detect subcategories on category_url and scrape them."""
    # --- Cleanup legacy Auto_Detection folder if present (safe, non-raising) ---
    legacy = os.path.join("data", "ScraperDefault", "Auto_Detection")
    if os.path.exists(legacy):
        try:
            import shutil
            shutil.rmtree(legacy)
            print(f"Suppression du ancien dossier inutile : {legacy}")
        except Exception:
            # ne pas bloquer si échec de suppression
            pass

    # write subcategories directly under data/ScraperDefault/<sous-cat>
    base_dir = os.path.join("data", "ScraperDefault")
    ensure_dir(base_dir)
    print("=== Scrape par défaut ===")

    driver = init_driver(headless=headless)
    from ..saver import SimpleStorage
    storage = SimpleStorage(base_dir="data")
    results = []

    try:
        subcats = _get_subcats(driver, category_url, max_subcats=max_subcats)
        if not subcats:
            print("Aucune sous-catégorie détectée.")
            return results

        items = list(subcats.items())[:max_subcats]
        for i, (sub_name, sub_url) in enumerate(items, 1):
            print(f"\n--[{i}/{len(items)}] {sub_name}--")
            prods = _scrape_subcategory(driver, sub_name, sub_url, base_dir, max_products, max_pages)
            saved = []
            for p in prods:
                if storage.is_processed(p.asin):
                    continue
                storage.mark_processed(p.asin, sub_name)
                saved.append(p)
            results.append((sub_name, sub_url, len(saved)))
            time.sleep(random.uniform(0.6, 1.6))
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        try:
            storage.close()
        except Exception:
            pass

    return results
