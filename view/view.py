# view/view.py
def show_menu():
    print("=====================================")
    print("|| BIENVENU DANS LE SCRAPER AMAZON ||")
    print("=====================================")
    print("\n")
    print("1) Lancer le scraper de la catégorie High-Tech")
    print("2) Scraper une catégorie spécifique (inserer votre url)")
    print("3) Scraper toutes les catégories")
    print("4) Afficher les derniers rapports enregistré")
    print("0) Quitter")
    print ("\n")
    return input("Choisissez une option : ").strip()

def show_message(msg):
    print("\n" + "="*6 + " " + msg + " " + "="*6 + "\n")
