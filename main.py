import os
import generate_html
from view.view import show_menu, show_message
from view.report import save_last_scrape, interactive_report_menu
from controller.scraper import scrape_default, scrape_category, scrape_all_categories


MAX_PRODUCTS = 5
MAX_SUBCATS = 4
MAX_PAGES = 1
HEADLESS = True

DEFAULT_CATEGORY_URL = "https://www.amazon.fr/b?node=13921051"

CATEGORY_URLS = {
    "technologie": "https://www.amazon.fr/b?node=13921051",
    "mode": "https://www.amazon.fr/b?node=11961521031",
    "maison": "https://www.amazon.fr/s?k=Maison",
    "jeux": "https://www.amazon.fr/s?k=jeux",
    "sport": "https://www.amazon.fr/s?k=sport"
}

ALL_CATEGORIES = ["technologie", "mode", "maison", "sport"]

def build_categories_list(names, mapping):
    return [(n, mapping[n]) for n in names if n in mapping]

def try_generate_site():
    try:

        generate_html.generate_site(data_dir="data", output_dir="site")
        show_message("Site statique généré dans ./site")
    except Exception as e:
        show_message(f"Erreur génération site : {e}")

def run():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        choix = show_menu()
        if choix == "1":
            results = scrape_default(DEFAULT_CATEGORY_URL, MAX_PRODUCTS, MAX_SUBCATS, MAX_PAGES, HEADLESS)
            save_last_scrape("default", results)
            try_generate_site()
            show_message("Scraping terminé ! Rapport enregistré.")
        elif choix == "2":
            url = input("URL de la catégorie : ").strip()
            if url:
                results = scrape_category(url, MAX_PRODUCTS, MAX_SUBCATS, MAX_PAGES, HEADLESS)
                save_last_scrape("categories", results)
                try_generate_site()
                show_message("Scraping terminé ! Rapport enregistré.")
            else:
                show_message("URL vide")
        elif choix == "3":
            cats = build_categories_list(ALL_CATEGORIES, CATEGORY_URLS)
            if not cats:
                show_message("Aucune catégorie valide.")
            else:
                results = scrape_all_categories(cats, MAX_PRODUCTS, MAX_SUBCATS, MAX_PAGES, HEADLESS)
                save_last_scrape("all_categories", results)
                try_generate_site()
                show_message("Scraping terminé ! Rapport enregistré.")
        elif choix == "4":
            interactive_report_menu()
        elif choix == "0":
            show_message("Au revoir !")
            break
        else:
            show_message("Choix invalide !")
        input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    run()
