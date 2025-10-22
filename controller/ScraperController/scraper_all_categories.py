from typing import List, Tuple
from ..fetcher import init_driver
from ..utils import ensure_dir, safe_filename
import os, time, random

def scrape_all_categories(categories_list: List[Tuple[str, str]], max_products: int, max_subcats: int, max_pages: int, headless: bool = True):
    """Scrape a list of categories (list of tuples (name, url)).
    Writes outputs under data/ScraperAllCategories/<category>/...
    """
    root = os.path.join("data", "ScraperAllCategories")
    ensure_dir(root)
    print("===================================")
    print("||Scrape de toutes les catégories||")
    print("===================================")

    driver = init_driver(headless=headless)
    results = []

    try:
        from .scraper_categories import scrape_category

        for i, (cat_name, cat_url) in enumerate(categories_list, 1):
            print(f"\n==== Category {i}/{len(categories_list)} : {cat_name} ====")
            base_dir = os.path.join(root, safe_filename(cat_name))
            ensure_dir(base_dir)

            # call scrape_category with base_dir (no fallback)
            cat_results = scrape_category(
                category_url=cat_url,
                max_products=max_products,
                max_subcats=max_subcats,
                max_pages=max_pages,
                headless=headless,
                driver=driver,
                base_dir=base_dir,
            )

            # Expect cat_results as iterable of (sub_name, sub_url, count)
            for item in cat_results:
                sub_name, sub_url, count = item[0], item[1], (item[2] if len(item) > 2 else 0)
                key = f"{cat_name}_{sub_name}" if sub_name != cat_name else cat_name
                results.append((key, sub_url, count))

            # polite pause between categories
            time.sleep(random.uniform(1.0, 2.0))

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return results
