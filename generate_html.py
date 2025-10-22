#!/usr/bin/env python3
# coding: utf-8
"""
generate_html.py
Génère site/static index.html à partir des products.json trouvés sous data/
Copie les images locales référencées par "image_local" dans site/assets/images/<category>/.
Expose generate_site(data_dir, output_dir) pour être appelé depuis main.py
"""

from pathlib import Path
import json
import shutil
import os
import html
import re

ROOT_IGNORE = {"ScraperCategories", "ScraperAllCategories", "ScraperDefault"}

# CSS fourni par toi (inséré tel quel ci-dessous)
PAGE_CSS = r"""
/* --- Ta CSS fournie --- */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Amazon Ember', Arial, sans-serif; background: #f3f3f3; }

/* Header */
.header { background: #232f3e; color: white; padding: 12px 20px; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.header-content { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 20px; }
.menu-toggle { background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 8px; }
.logo { font-size: 1.8rem; font-weight: bold; color: #ff9900; }
.search-bar { flex: 1; max-width: 600px; display: flex; }
.search-bar input { flex: 1; padding: 10px 15px; border: none; border-radius: 4px 0 0 4px; font-size: 16px; }
.search-btn { background: #ff9900; border: none; padding: 10px 15px; border-radius: 0 4px 4px 0; cursor: pointer; }

/* Sidebar */
.sidebar { position: fixed; left: -300px; top: 0; width: 300px; height: 100vh; background: white; z-index: 1001; transition: left 0.3s ease; box-shadow: 2px 0 5px rgba(0,0,0,0.1); overflow-y: auto; }
.sidebar.open { left: 0; }
.sidebar-header { background: #232f3e; color: white; padding: 20px; font-weight: bold; }
.sidebar-close { float: right; background: none; border: none; color: white; font-size: 20px; cursor: pointer; }
.category-list { padding: 20px 0; }
.category-item { display: block; padding: 12px 20px; color: #333; text-decoration: none; border-bottom: 1px solid #eee; transition: background 0.2s; }
.category-item:hover, .category-item.active { background: #f0f8ff; color: #007185; }
.overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; opacity: 0; visibility: hidden; transition: all 0.3s; }
.overlay.show { opacity: 1; visibility: visible; }

/* Main Content */
.container { max-width: 1200px; margin: 0 auto; padding: 20px; margin-top: 80px; }
.breadcrumb { margin-bottom: 20px; color: #666; font-size: 14px; display: none; }
.results-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; }
.results-count { font-weight: bold; color: #333; }
.filter-toggle { background: #007185; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }

/* Product Grid */
.category-section { margin-bottom: 40px; }
.category-title { background: white; padding: 15px 20px; margin-bottom: 20px; border-radius: 8px; font-size: 1.4rem; color: #232f3e; border-left: 4px solid #ff9900; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }

/* Product Cards - Fixed Height */
.product { background: white; border-radius: 8px; overflow: hidden; transition: all 0.3s ease; border: 1px solid #ddd; display: flex; flex-direction: column; height: 480px; }
.product:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-2px); }
.product img { width: 100%; height: 200px; object-fit: contain; background: #f8f9fa; border-bottom: 1px solid #eee; }
.product-info { padding: 15px; flex: 1; display: flex; flex-direction: column; }
.product-title { font-size: 14px; font-weight: 600; color: #0066c0; margin-bottom: 8px; line-height: 1.3; height: 40px; overflow: hidden; }
.product-description { font-size: 13px; color: #565959; line-height: 1.4; margin-bottom: 10px; flex: 1; position: relative; }
.description-short { display: block; }
.description-full { display: none; max-height: 80px; overflow-y: auto; background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 5px; border: 1px solid #eee; }
.description-toggle { color: #007185; cursor: pointer; font-size: 13px; margin-top: 5px; }
.product-price { font-size: 18px; font-weight: bold; color: #B12704; margin: 10px 0; }
.product-meta { font-size: 12px; color: #666; margin-bottom: 15px; }
.product-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.tag { background: #e7f3ff; color: #007185; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
.product-actions { margin-top: auto; }
.btn-primary { display: block; width: 100%; padding: 8px; background: #ff9900; color: white; text-decoration: none; text-align: center; border-radius: 4px; font-weight: bold; transition: background 0.2s; }
.btn-primary:hover { background: #e47911; }

/* Responsive */
@media (max-width: 768px) {
  .menu-toggle { display: block; }
  .search-bar { max-width: none; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 15px; }
  .container { padding: 15px; }
  .results-info { flex-direction: column; gap: 10px; align-items: stretch; }
}

.empty-state { text-align: center; color: #666; background: white; padding: 40px; border-radius: 8px; }
"""

# JS fourni (légèrement adapté pour être dynamique)
PAGE_JS_TEMPLATE = r"""
/* --- JS fourni + dynamique categories (injected) --- */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.querySelector('.overlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('show');
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.querySelector('.overlay').classList.remove('show');
}

// Category filtering
function showCategory(category, event) {
  if (event) event.preventDefault();
  const sections = document.querySelectorAll('.category-section');
  const items = document.querySelectorAll('.category-item');

  // Remove active class from all items
  items.forEach(item => item.classList.remove('active'));
  // Add active class to clicked item
  if (event && event.currentTarget) {
    event.currentTarget.classList.add('active');
  }

  if (category === 'all') {
    sections.forEach(section => section.style.display = 'block');
  } else {
    sections.forEach(section => {
      section.style.display = section.dataset.category === category ? 'block' : 'none';
    });
  }
  updateResultsCount();
  closeSidebar();
}

// Search functionality
function filterProducts() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase();
  const products = document.querySelectorAll('.product');
  let visibleCount = 0;

  products.forEach(product => {
    const section = product.closest('.category-section');
    if (section && section.style.display === 'none') {
      return; // Skip products in hidden categories
    }

    const title = product.querySelector('.product-title').textContent.toLowerCase();
    const descElement = product.querySelector('.product-description');
    const desc = descElement ? descElement.textContent.toLowerCase() : '';
    const visible = title.includes(searchTerm) || desc.includes(searchTerm);
    product.style.display = visible ? 'flex' : 'none';
    if (visible) visibleCount++;
  });

  document.getElementById('resultsCount').textContent = `${visibleCount} produit(s) trouvé(s)`;
}

// Description toggle
function toggleDescription(btn) {
  const container = btn.closest('.product-info');
  const shortDesc = container.querySelector('.description-short');
  const fullDesc = container.querySelector('.description-full');

  if (fullDesc && (fullDesc.style.display === 'none' || !fullDesc.style.display)) {
    if (shortDesc) shortDesc.style.display = 'none';
    if (fullDesc) fullDesc.style.display = 'block';
    btn.textContent = 'Voir moins';
  } else {
    if (shortDesc) shortDesc.style.display = 'block';
    if (fullDesc) fullDesc.style.display = 'none';
    btn.textContent = 'Voir plus';
  }
}

// Update results count
function updateResultsCount() {
  const visibleProducts = document.querySelectorAll('.product:not([style*="display: none"]):not([style*="display:none"])').length;
  document.getElementById('resultsCount').textContent = `${visibleProducts} produit(s) affichés sur ${totalProducts} total`;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
  const categoryList = document.getElementById('categoryList');

  // categories variable injected by generate_html.py (array of {slug,label})
  if (typeof categories !== 'undefined' && Array.isArray(categories)) {
    categories.forEach(c => {
      const newCat = document.createElement('a');
      newCat.href = '#';
      newCat.className = 'category-item';
      newCat.textContent = c.label;
      newCat.onclick = function(e) { showCategory(c.slug, e); };
      categoryList.appendChild(newCat);
    });
  }

  updateResultsCount();

  // wire search input
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', filterProducts);
  }
});
"""

# helpers
def slugify(s: str) -> str:
    s = str(s)
    s = s.strip()
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-À-ž]", "_", s)
    s = re.sub(r"__+", "_", s)
    return s

def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def copy_image_to_site(src: Path, dst_dir: Path):
    try:
        ensure_dir(dst_dir)
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        return dst
    except Exception:
        return None

def safe_html(s):
    return html.escape(str(s)) if s is not None else ""

def make_product_card(prod, image_rel_path):
    # prod fields: asin, name, description, price, url, brand, subcategory
    title = safe_html(prod.get("name") or prod.get("title") or prod.get("asin") or "Produit")
    price = safe_html(prod.get("price") or "")
    description = prod.get("description") or ""
    short = safe_html(description[:160] + ("..." if len(description) > 160 else ""))
    full = safe_html(description)
    brand = safe_html(prod.get("brand") or "")
    tags_html = ""
    if brand:
        tags_html = f'<div class="product-tags"><span class="tag">{brand}</span></div>'
    # image_rel_path may be None (use placeholder)
    if image_rel_path:
        img_src = image_rel_path.replace("\\", "/")
        img_html = f'<img src="{html.escape(img_src)}" alt="{title}">'
    else:
        img_html = '<div style="height:200px;display:flex;align-items:center;justify-content:center;color:#666">Pas d\'image</div>'

    url = safe_html(prod.get("url") or prod.get("product_url") or "")

    card = f'''
    <div class="product">
      {img_html}
      <div class="product-info">
        <div class="product-title">{title}</div>
        <div class="product-description">
          <span class="description-short">{short}</span>
          <div class="description-full">{full}</div>
        </div>
        <div class="product-price">{price}</div>
        <div class="product-meta">ASIN: {safe_html(prod.get("asin") or "")}</div>
        {tags_html}
        <div class="product-actions">
          <a class="btn-primary" href="{url}" target="_blank" rel="noopener">Voir produit</a>
          <div style="margin-top:6px;text-align:right">
            <button onclick="toggleDescription(this)" class="description-toggle">Voir plus</button>
          </div>
        </div>
      </div>
    </div>
    '''
    return card

def generate_site(data_dir="data", output_dir="site"):
    data_path = Path(data_dir)
    out_path = Path(output_dir)
    if not data_path.exists():
        print(f"[generate_html] Dossier data introuvable: {data_dir}")
        return

    # find all products.json
    all_jsons = list(data_path.rglob("products.json"))
    categories = {}  # slug -> {label, products: [] , images_dir}
    for jp in all_jsons:
        # determine category name: parent name, unless parent is root ignore then parent.parent
        parent = jp.parent
        category_name = parent.name
        if category_name in ROOT_IGNORE and parent.parent:
            category_name = parent.parent.name
        if category_name in ROOT_IGNORE:
            category_name = "autres"
        slug = slugify(category_name)
        prods = read_json(jp)
        if prods is None:
            continue
        if isinstance(prods, dict):
            # may be wrapped
            for key in ("products", "items", "results"):
                if key in prods and isinstance(prods[key], list):
                    prods = prods[key]
                    break
            else:
                # single product -> wrap
                prods = [prods]
        # ensure list
        if not isinstance(prods, list):
            continue
        categories.setdefault(slug, {"label": category_name, "products": [], "src_paths": []})
        # record products with reference to jp.parent for image resolution
        for p in prods:
            p["_source_dir"] = str(jp.parent)
            categories[slug]["products"].append(p)

    if not categories:
        print("[generate_html] Aucun products.json trouvé.")
        return

    # prepare output dirs
    assets_images_dir = out_path / "assets" / "images"
    ensure_dir(assets_images_dir)

    # copy images and prepare per-product image paths
    total_products = 0
    for slug, meta in categories.items():
        cat_img_dir = assets_images_dir / slug
        ensure_dir(cat_img_dir)
        for p in meta["products"]:
            total_products += 1
            img_local = p.get("image_local") or p.get("image_path") or p.get("image")  # support several keys
            chosen_rel = None
            if img_local:
                # convert backslashes and try to find the file relative to project root or as given
                img_path = Path(str(img_local).replace("\\", os.sep))
                if not img_path.exists():
                    # maybe it's relative to source dir
                    src_dir = Path(p.get("_source_dir", ""))
                    candidate = src_dir / Path(str(img_local).replace("\\", "/")).name
                    if candidate.exists():
                        img_path = candidate
                if img_path.exists():
                    copied = copy_image_to_site(img_path, cat_img_dir)
                    if copied:
                        chosen_rel = os.path.relpath(copied, start=out_path).replace("\\", "/")
            # fallback to image_url (external)
            if not chosen_rel:
                img_url = p.get("image_url") or p.get("image")
                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                    chosen_rel = img_url
            p["_image_ref"] = chosen_rel

    # build HTML
    ensure_dir(out_path)
    index_html = []
    index_html.append("<!doctype html>")
    index_html.append("<html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>")
    index_html.append("<title>Catalogue scrappé</title>")
    index_html.append("<style>")
    index_html.append(PAGE_CSS)
    index_html.append("</style>")
    index_html.append("</head><body>")

    # header + sidebar skeleton
    header = f"""
    <div class="header">
      <div class="header-content">
        <button class="menu-toggle" onclick="toggleSidebar()">☰</button>
        <div class="logo">Mon Catalogue</div>
        <div class="search-bar">
          <input id="searchInput" placeholder="Rechercher un produit...">
          <button class="search-btn" onclick="filterProducts()">Rechercher</button>
        </div>
      </div>
    </div>
    """
    index_html.append(header)

    sidebar = """
    <div id="sidebar" class="sidebar">
      <div class="sidebar-header">Catégories <button class="sidebar-close" onclick="closeSidebar()">✕</button></div>
      <div class="category-list" id="categoryList"></div>
    </div>
    <div class="overlay" onclick="closeSidebar()"></div>
    """
    index_html.append(sidebar)

    # main container: results info + categories sections
    index_html.append('<div class="container">')
    index_html.append('<div class="results-info"><div id="resultsCount" class="results-count"></div><div><button class="filter-toggle" onclick="toggleSidebar()">Filtrer</button></div></div>')

    # for each category, create a section
    for slug, meta in sorted(categories.items(), key=lambda kv: kv[1]["label"].lower()):
        label = meta["label"]
        products = meta["products"]
        index_html.append(f'<section class="category-section" data-category="{slug}">')
        index_html.append(f'<div class="category-title">{html.escape(label)} ({len(products)})</div>')
        index_html.append('<div class="grid">')
        for p in products:
            card = make_product_card(p, p.get("_image_ref"))
            index_html.append(card)
        index_html.append('</div>')  # grid
        index_html.append('</section>')

    index_html.append('</div>')  # container

    # inject categories array and totalProducts into JS
    categories_js_array = []
    for slug, meta in categories.items():
        label = f"{meta['label']} ({len(meta['products'])})"
        categories_js_array.append({"slug": slug, "label": label})

    index_html.append("<script>")
    index_html.append("const categories = " + json.dumps(categories_js_array, ensure_ascii=False) + ";")
    index_html.append("const totalProducts = " + str(total_products) + ";")
    index_html.append(PAGE_JS_TEMPLATE)
    index_html.append("</script>")

    index_html.append("</body></html>")

    (out_path / "index.html").write_text("\n".join(index_html), encoding="utf-8")
    print(f"[generate_html] Site généré: {out_path.resolve() / 'index.html'} (images copiées dans {assets_images_dir})")

# allow usage as script
if __name__ == "__main__":
    generate_site("data", "site")
