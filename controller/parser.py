from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Tuple, Dict, Optional
from .utils import safe_filename


def build_subcategory_url(category_url: str, subcat_text: str, param_name: str = "k") -> str:
    # helper preserved from original (keeps behavior)
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(category_url)
    qs = parse_qs(parsed.query)
    qs[param_name] = [subcat_text]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def get_subcategory_links_from_html(page_source: str, base_domain: str = "https://www.amazon.fr", max_subcats: int = 10) -> Dict[str, str]:
    soup = BeautifulSoup(page_source, "lxml")
    links = {}
    BLACKLIST = ["cart", "bestsellers", "help", "gift-cards", "wishlist", "sign-in", "prime", "account"]
    for a in soup.select("a"):
        href = a.get("href")
        name = a.get_text(strip=True)
        if not href or not name:
            continue
        if any(b in href.lower() for b in BLACKLIST):
            continue
        if "/s?" in href or "i=" in href or "/b?" in href:
            if href.startswith("//"):
                full = "https:" + href
            elif href.startswith("/"):
                full = base_domain + href
            elif href.startswith("http"):
                full = href
            else:
                full = base_domain + "/" + href
            if 3 < len(name) < 60 and name.lower() not in ["tout", "voir plus"]:
                safe = safe_filename(name)
                if safe not in links:
                    links[safe] = full
                if len(links) >= max_subcats:
                    break
    if not links:
        for a in soup.select("a.a-link-normal"):
            href = a.get("href")
            name = a.get_text(strip=True)
            if href and name:
                full = href if href.startswith("http") else base_domain + href
                safe = safe_filename(name)
                links[safe] = full
                if len(links) >= max_subcats:
                    break
    return links


def extract_product_links(page_source: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(page_source, "lxml")
    items = soup.select("div[data-asin]") or soup.select("[data-component-type='s-search-result']")
    results = []
    for it in items:
        asin = it.get("data-asin")
        if not asin:
            continue
        a = it.select_one("a[href*='/dp/'], a[href*='/gp/']")
        if not a:
            continue
        href = a.get("href").split("?")[0]
        if href.startswith("/"):
            full = "https://www.amazon.fr" + href
        elif href.startswith("http"):
            full = href
        else:
            continue
        results.append((asin, full))
    return results


def parse_product_page(page_source: str) -> dict:
    soup = BeautifulSoup(page_source, "lxml")
    def text_of(selectors: List[str]):
        for s in selectors:
            n = soup.select_one(s)
            if n and n.get_text(strip=True):
                return n.get_text(" ", strip=True)
        return None
    name = text_of(["#productTitle", "#title", "span#title", "h1.a-size-large"]) 
    desc = None
    desc_node = soup.select_one("#productDescription") or soup.select_one("#feature-bullets")
    if desc_node:
        bullets = [li.get_text(strip=True) for li in desc_node.select("li") if li.get_text(strip=True)]
        desc = " ".join(bullets) if bullets else desc_node.get_text(" ", strip=True)
    price = text_of(["#priceblock_ourprice", "#priceblock_dealprice", ".a-price .a-offscreen", ".a-price-whole"])
    brand = None
    byline = soup.select_one("#bylineInfo")
    if byline and byline.get_text(strip=True):
        brand = byline.get_text(" ", strip=True)
    if not brand:
        for li in soup.select("#detailBullets_feature_div li, #productDetails_techSpec_section_1 tr"):
            txt = li.get_text(" ", strip=True)
            if "Marque" in txt or "Brand" in txt:
                parts = txt.split(":", 1)
                brand = parts[1].strip() if len(parts) > 1 else txt.strip()
                break
    seller = text_of(["#sellerProfileTriggerId", "#merchant-info"])
    color = None
    col = soup.select_one("#variation_color_name .selection") or soup.select_one(".swatchSelected")
    if col:
        color = col.get_text(strip=True)
    image_url = None
    img_node = soup.select_one("#landingImage") or soup.select_one("#imgTagWrapperId img") or soup.select_one("img#main-image")
    if img_node:
        image_url = img_node.get("data-old-hires") or img_node.get("data-src") or img_node.get("src")
    return {"name": name, "description": desc, "price": price, "brand": brand, "seller": seller, "color": color, "image_url": image_url}

