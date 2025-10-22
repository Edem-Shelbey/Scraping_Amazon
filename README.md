# 🕸️ Web_Scrap

**Projet universitaire de développement Python**

## 📘 Description

**Web_Scrap** est une application console en Python qui permet de **scraper des produits depuis Amazon** directement depuis le terminal.
Le but est de récupérer des informations clés sur les produits (image, nom, description, URL, vendeur, etc.) selon différents modes de scraping.

---

## ⚙️ Fonctionnalités principales

Le programme propose **trois modes de scraping** :

1. **Scraper par défaut**
   → Scrape la catégorie **Tech** d’Amazon.

2. **Scraper catégorie spécifique**
   → Permet de scraper **une catégorie précise** à partir du **lien Amazon** saisi par l’utilisateur.

3. **Scraper toutes les catégories**
   → Scrape **toutes les catégories enregistrées dans le fichier `main.py`**.

---

## 💾 Structure des données

Toutes les données collectées sont enregistrées dans le dossier **`/data`**, dans des **sous-dossiers distincts** selon le type de scraping effectué.
Un fichier **`rapport.txt`** est automatiquement généré pour répertorier les fichiers scrappés et leurs emplacements.

---

## 🧠 Architecture

Le projet respecte la **structure MVC (Model - View - Controller)**, assurant une bonne séparation du code et une maintenance simplifiée.

---

## 🧩 Technologies utilisées

* **Python 3.x**
* **Selenium**
* **BeautifulSoup (bs4)**

---

## 🚀 Installation

1. Clone le dépôt ou télécharge le projet.
2. Installe les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Exécution

Pour lancer le programme :

```bash
python main.py
```

L’application se lance dans le **terminal** et te guide pour choisir le type de scraping à effectuer.

---

## 📄 Sortie

* Les données extraites sont stockées dans le dossier `data/`.
* Un rapport global est généré dans `rapport.txt`.

---

## ⚠️ Avertissement

Ce projet est **strictement à but éducatif**.
Le scraping de sites web comme Amazon doit se faire dans le respect de leurs conditions d’utilisation.
Ne pas utiliser ce programme à des fins commerciales.

---

## 👨‍💻 Auteur

Projet universitaire réalisé par **Tossou Emmanuel**, étudiant en informatique.
Université : *IIT*
Année : *2025*
