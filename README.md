# Web Scraping Python - Exercices Avancés

Collection complète de 9 exercices progressifs implémentant les techniques avancées de web scraping avec BeautifulSoup.

## Objectifs

- Maîtriser BeautifulSoup et requests pour l'extraction de données web
- Implémenter des patterns robustes (retry, cache, logging)
- Gérer l'authentification et les sessions
- Nettoyer et valider les données extraites
- Créer des architectures modulaires et réutilisables

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/schwarzT404/scrapping.git
cd scrapping

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Menu interactif

```bash
python main_scraping_exercises.py
```

### Exercices individuels

```bash
python exercice_01_books_scraper.py
python exercice_02_quotes_graph.py
python exercice_03_fake_jobs.py
# ... etc
```

## Liste des exercices

| # | Exercice | Description | Durée |
|---|----------|-------------|-------|
| 1 | **Books to Scrape** | Extraction complète avec pagination (20 pages) | 3-4 min |
| 2 | **Quotes Graph** | Graphe relationnel avec cache (2 pages) | 30-45s |
| 3 | **Fake Jobs** | Filtres avancés et détection doublons | 10-15s |
| 4 | **Market Analysis** | Statistiques et visualisations matplotlib | 45-60s |
| 5 | **Category Navigation** | Arborescence catégories complète | 3-5 min |
| 6 | **Resilient Scraper** | Retry intelligent, logging, checkpoints | 2-3 min |
| 7 | **Data Cleaning** | Pipeline nettoyage et métriques qualité | 45-60s |
| 8 | **Multi-Source** | Architecture modulaire multi-sources | 1-2 min |
| 9 | **Authentication** | Gestion sessions et contenu protégé | 20-30s |

## Concepts couverts

### Techniques de base
- Sélecteurs CSS et XPath
- Navigation dans le DOM
- Extraction de données structurées
- Gestion des erreurs

### Patterns avancés
- Pagination automatique
- Système de cache
- Retry avec backoff exponentiel
- Rate limiting adaptatif
- Checkpoints et reprise

### Architecture
- Design patterns (Strategy, Plugin)
- Parallel processing (ThreadPoolExecutor)
- Configuration externe (YAML)
- Logging structuré

### Data Engineering
- Nettoyage et standardisation
- Détection d'anomalies
- Validation croisée
- Métriques qualité

## Sorties generees

Les exercices génèrent différents formats de sortie dans `./outputs/`:
- **JSON** : Données structurées avec métadonnées
- **CSV** : Export tabulaire (offres d'emploi, données nettoyées)
- **GraphML** : Graphes relationnels (importable dans Gephi)
- **PNG** : Visualisations matplotlib
- **LOG** : Journaux détaillés d'exécution

## Configuration

### Limites par défaut

Toutes les limites sont configurables pour optimiser le temps d'exécution:

```python
# Exercice 1
scraper = BooksScraperComplete(max_pages=20)  # Défaut: 20 pages

# Exercice 2
scraper = QuotesGraphScraper(max_pages=2)  # Défaut: 2 pages

# Exercice 3
scraper = FakeJobsScraper(max_jobs=100)  # Défaut: 100 offres
```

### Variables d'environnement

```bash
# Optionnel: timeout personnalisé
export SCRAPER_TIMEOUT=15

# Optionnel: délai entre requêtes
export SCRAPER_DELAY=2
```

## Bonnes pratiques

**Respecter les serveurs**
- Délais aléatoires entre requêtes (0.5-2s)
- User-Agent approprié
- Respect de `robots.txt`
- Rate limiting adaptatif

**Gestion d'erreurs robuste**
- Try-except complets
- Retry avec backoff exponentiel
- Timeout adaptatifs
- Logging détaillé

**Code maintenable**
- Architecture orientée objet
- Docstrings complètes
- Type hints (typing)
- Séparation des préoccupations

## Performance

### Métriques attendues

Total pour les 9 exercices: **~15-20 minutes**

Détails par exercice voir [LIMITATIONS_QUANTITATIVES.md](LIMITATIONS_QUANTITATIVES.md)

### Optimisations

- Session pooling (connexions réutilisées)
- Cache pour éviter requêtes dupliquées
- Parallel processing (Exercice 8)
- Checkpoints pour reprise rapide

## Tests

```bash
# Test rapide d'un exercice
python exercice_03_fake_jobs.py --keyword Python --max 10

# Test avec limite réduite
python exercice_01_books_scraper.py  # Modifier max_pages dans le code
```

## Dependances principales

- **requests** : Requêtes HTTP
- **beautifulsoup4** : Parsing HTML
- **lxml** : Parser rapide
- **pandas** : Manipulation données
- **matplotlib** : Visualisations
- **networkx** : Graphes
- **pyyaml** : Configuration

Voir [requirements.txt](requirements.txt) pour versions complètes.

## Contribution

Projet éducatif - Master 1 Algo 2025

## Avertissement

Ces exercices utilisent des sites web d'entraînement publics:
- https://books.toscrape.com/
- http://quotes.toscrape.com/
- https://realpython.github.io/fake-jobs/

**Important**: Pour scraper des sites en production:
1. Vérifier les conditions d'utilisation
2. Respecter `robots.txt`
3. Obtenir les autorisations nécessaires
4. Limiter la fréquence des requêtes

## Licence

Code éducatif - Utilisation libre dans cadre académique

© 2025 - Tous droits réservés

## Ressources

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [Requests Documentation](https://requests.readthedocs.io/)
- [Web Scraping Best Practices](https://github.com/topics/web-scraping)

---

**Auteur**: schwarzT404  
**Repository**: https://github.com/schwarzT404/scrapping
