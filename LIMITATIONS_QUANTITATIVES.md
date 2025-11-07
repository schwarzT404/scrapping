# Limitations Quantitatives - Exercices Web Scraping

## Vue d'ensemble

Optimisation temps d'exécution et volume de données pour usage pédagogique.
Chaque exercice limité à ~20-40 éléments selon thématique.

## Limitations par exercice

### Exercice 1: Books to Scrape
**Avant**: 46 pages (~1000 livres)  
**Après**: **20 pages max (~400 livres)**

```python
def scrape_all_pages(self, max_pages=20):  # Limitation explicite
```

**Durée estimée**: 3-4 minutes (au lieu de 8-10 minutes)

---

### Exercice 2: Quotes to Scrape
**Avant**: Toutes les pages (~100 quotes)  
**Après**: **2 pages max (~20 quotes)**

```python
def __init__(self, base_url="http://quotes.toscrape.com", max_pages=2):
    self.max_pages = max_pages  # Limite par défaut: 2 pages
```

**Durée estimée**: 30-45 secondes (au lieu de 2-3 minutes)

---

### Exercice 3: Fake Jobs
**Avant**: 1 page unique  
**Après**: **Limite 100 offres max**

```python
def __init__(self, ..., max_jobs=100):
    self.max_jobs = max_jobs  # Limite par défaut: 100 offres
```

**Durée estimée**: 10-15 secondes

---

### Exercice 4: Analyse Marché
**Avant**: 5 pages (~100 livres)  
**Après**: **3 pages (~60 livres)**

```python
def __init__(self, base_url="https://books.toscrape.com/", max_pages=3):
    self.max_pages = max_pages  # Limite par défaut: 3 pages
```

**Durée estimée**: 30-45 secondes (au lieu de 1-2 minutes)

---

### Exercice 5: Navigation Catégorielle
**Avant**: Toutes pages toutes catégories (~500+ livres)  
**Après**: **1 page par catégorie (~20 livres/catégorie)**

```python
def scrape_category_books(self, category_url, max_pages=1):
```

**Impact**: 
- ~50 catégories × 20 livres = ~1000 livres total
- Mais scraping séquentiel par catégorie
- Statistiques restent représentatives

**Durée estimée**: 3-5 minutes (au lieu de 10-15 minutes)

---

### Exercice 6: Scraper Résilient
**Avant**: 10 pages  
**Après**: **Inchangé - 10 pages (~200 livres)**

Déjà optimal pour démonstration résilience.

```python
def scrape_with_resilience(self, max_pages=10):
```

**Durée estimée**: 2-3 minutes

---

### Exercice 7: Data Cleaning
**Avant**: 3 pages (~60 livres)  
**Après**: **Inchangé - 3 pages (~60 livres)**

Suffisant pour démonstration nettoyage données.

```python
self._scrape_raw_data(max_pages=3)
```

**Durée estimée**: 45-60 secondes

---

### Exercice 8: Multi-sources
**Avant**: 
- Books: 3 pages
- Quotes: 3 pages
- Jobs: 1 page

**Après**:
- **Books: 2 pages (~40 livres)**
- **Quotes: 2 pages (~20 quotes)**
- **Jobs: 1 page (~50 jobs)**

Configuration par défaut:
```python
'max_pages': 2  # Books et Quotes
```

**Durée estimée**: 1-2 minutes (au lieu de 2-3 minutes)

---

### Exercice 9: Authentification
**Avant**: ~10 quotes  
**Après**: **Inchangé - ~10 quotes**

Exercice focalisé sur authentification, pas sur volume.

**Durée estimée**: 20-30 secondes

---

## Tableau comparatif

| Exercice | Avant | Après | Gain temps | Volume données |
|----------|-------|-------|------------|----------------|
| Ex 1 | 46 pages | **20 pages** | ~60% | ~400 livres |
| Ex 2 | ~10 pages | **2 pages** | ~80% | ~20 quotes |
| Ex 3 | 1 page | 1 page | - | ~50 jobs |
| Ex 4 | 5 pages | **2 pages** | ~60% | ~40 livres |
| Ex 5 | Multi-pages | **1 page/cat** | ~70% | ~1000 livres |
| Ex 6 | 10 pages | 10 pages | - | ~200 livres |
| Ex 7 | 3 pages | 3 pages | - | ~60 livres |
| Ex 8 | 7 pages | **5 pages** | ~30% | ~110 éléments |
| Ex 9 | 1 page | 1 page | - | ~10 quotes |

**Total durée avant**: ~35-45 minutes  
**Total durée après**: ~15-20 minutes  
**Gain global**: ~55% réduction temps

---

## Justification limitations

### Pédagogique
✓ Volumes suffisants pour démonstration techniques  
✓ Résultats statistiques représentatifs  
✓ Graphes et visualisations pertinents  
✓ Patterns de données diversifiés

### Performance
✓ Exécution complète en temps raisonnable  
✓ Réduction charge serveurs  
✓ Mémoire RAM optimisée  
✓ Tests itératifs facilités

### Pratique
✓ Fichiers output plus légers  
✓ Debug plus rapide  
✓ Logs plus lisibles  
✓ Démonstrations plus fluides

---

## Personnalisation

Modifier paramètres selon besoins:

### Augmenter volumes
```python
# Dans chaque exercice
scraper.scrape_all_pages(max_pages=50)  # Exemple augmentation
```

### Réduire volumes (test rapide)
```python
# Test ultra-rapide
scraper.scrape_all_pages(max_pages=1)
```

### Configuration globale
```python
# Exercice 8 - Modifier scraper_config.yaml
sources:
  - name: books
    max_pages: 5  # Au lieu de 2
```

---

## Métriques post-optimisation

### Volume données moyen par exercice
- **Petit** (10-50 items): Ex 3, 9
- **Moyen** (50-200 items): Ex 2, 4, 6, 7
- **Grand** (200-500 items): Ex 1, 8
- **Très grand** (500-1000 items): Ex 5

### Distribution temps exécution
```
Ex 3, 9  : ████░░░░░░ (< 1 min)
Ex 2, 4, 7, 8 : ███████░░░ (1-2 min)
Ex 6     : ████████░░ (2-3 min)
Ex 1, 5  : ██████████ (3-5 min)
```

---

## Impact qualité résultats

### Analyses statistiques
- Moyennes, médianes : **Très représentatif**
- Écarts-types : **Représentatif**
- Corrélations : **Représentatif**
- Outliers : **Partiellement représentatif**

### Visualisations
- Histogrammes : **Pertinent**
- Scatter plots : **Pertinent**
- Box plots : **Pertinent**
- Heatmaps : **Pertinent si >30 points**

### Graphes relationnels
- Nœuds : **Suffisant pour démonstration**
- Arêtes : **Patterns visibles**
- Clustering : **Détectable**
- Centralité : **Calculable**

---

## Recommandations usage

### En cours
Limitations actuelles **optimales** pour:
- Apprentissage techniques
- Démonstrations live
- Tests rapides
- Développement itératif

### En production
Supprimer limitations si:
- Analyse statistique rigoureuse requise
- Couverture exhaustive nécessaire
- Benchmark performance requis
- Dataset complet souhaité

### En recherche
Adapter selon:
- Hypothèses à tester
- Puissance statistique requise
- Temps calcul disponible
- Ressources machine

---

## Notes techniques

### Respect serveurs maintenu
✓ Délais entre requêtes inchangés  
✓ Rate limiting toujours actif  
✓ User-Agent approprié  
✓ Retry strategy conservée

### Backward compatibility
✓ Paramètres `max_pages` optionnels  
✓ Valeurs par défaut définies  
✓ Code legacy fonctionnel  
✓ API stable

---

**Version**: 2.1 (Optimisée quantités)  
**Date**: 2025-11-06  
**Auteur**: Correction suite feedback utilisateur
