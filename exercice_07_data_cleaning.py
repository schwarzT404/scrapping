"""
Exercice 7: Pipeline de data cleaning
Nettoyage, standardisation, validation, métriques qualité
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import time
import random
import statistics


class DataCleaningPipeline:
    """Pipeline complet nettoyage et validation données"""
    
    def __init__(self, base_url="https://books.toscrape.com/", max_pages=3):
        """
        Initialisation pipeline avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_pages: Limite nombre de pages (défaut: 3)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        
        # Données brutes et nettoyées
        self.raw_data = []
        self.cleaned_data = []
        
        # Rapports qualité
        self.quality_report = {
            'anomalies': [],
            'missing_values': {},
            'duplicates': [],
            'outliers': [],
            'validation_errors': []
        }
    
    def _respectful_delay(self):
        """Délai aléatoire entre requêtes"""
        time.sleep(random.uniform(0.5, 1.5))
    
    def _convert_rating(self, rating_classes: List[str]) -> int:
        """Conversion classe CSS rating en valeur numérique"""
        ratings_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        
        for cls in rating_classes:
            if cls in ratings_map:
                return ratings_map[cls]
        return None  # Retour None pour valeur manquante
    
    def scrape_raw_data(self):
        """Extraction données brutes (volontairement non nettoyées)"""
        print(f"Extraction données brutes (limite: {self.max_pages} pages)...\n")
        
        page_num = 1
        
        while page_num <= self.max_pages:
            if page_num == 1:
                page_url = f"{self.base_url}index.html"
            else:
                page_url = f"{self.base_url}catalogue/page-{page_num}.html"
            
            try:
                print(f"Page {page_num}/{self.max_pages}...")
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                book_elements = soup.select('.product_pod')
                
                if not book_elements:
                    break
                
                for book_elem in book_elements:
                    # Extraction brute sans nettoyage
                    title_tag = book_elem.select_one('h3 a')
                    title = title_tag['title'] if title_tag else None
                    
                    price_tag = book_elem.select_one('.price_color')
                    price = price_tag.get_text() if price_tag else None
                    
                    rating_tag = book_elem.select_one('.star-rating')
                    rating = rating_tag['class'][1] if rating_tag and len(rating_tag['class']) > 1 else None
                    
                    avail_tag = book_elem.select_one('.availability')
                    availability = avail_tag.get_text() if avail_tag else None
                    
                    raw_book = {
                        'title': title,
                        'price': price,
                        'rating': rating,
                        'availability': availability
                    }
                    
                    self.raw_data.append(raw_book)
                
                page_num += 1
                
                if page_num <= self.max_pages:
                    self._respectful_delay()
                
            except Exception as e:
                print(f"✗ Erreur page {page_num}: {e}")
                break
        
        print(f"\n✓ {len(self.raw_data)} enregistrements bruts extraits")
    
    def clean_title(self, title: Any) -> str:
        """Nettoyage et standardisation titres"""
        if title is None or title == '':
            return 'N/A'
        
        # Conversion string
        title = str(title)
        
        # Trim espaces
        title = title.strip()
        
        # Suppression espaces multiples
        title = re.sub(r'\s+', ' ', title)
        
        # Correction encodage problématique
        title = title.encode('utf-8', errors='ignore').decode('utf-8')
        
        return title
    
    def clean_price(self, price: Any) -> float:
        """Nettoyage et extraction prix"""
        if price is None or price == '':
            return None
        
        # Conversion string
        price = str(price)
        
        # Extraction valeur numérique
        match = re.search(r'[\d]+\.?[\d]*', price)
        
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        
        return None
    
    def clean_rating(self, rating: Any) -> int:
        """Nettoyage et conversion rating"""
        if rating is None or rating == '':
            return None
        
        # Mapping texte → numérique
        ratings_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5,
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5
        }
        
        # Si déjà numérique
        if isinstance(rating, int):
            return rating if 1 <= rating <= 5 else None
        
        # Conversion depuis texte
        rating_str = str(rating).strip()
        return ratings_map.get(rating_str, None)
    
    def clean_availability(self, availability: Any) -> int:
        """Extraction quantité stock depuis texte disponibilité"""
        if availability is None or availability == '':
            return 0
        
        availability = str(availability).strip()
        
        # Recherche pattern "X available"
        match = re.search(r'(\d+)\s+available', availability, re.IGNORECASE)
        
        if match:
            return int(match.group(1))
        
        # Si "In stock" sans nombre
        if 'in stock' in availability.lower():
            return 1  # Au moins 1 disponible
        
        return 0  # Rupture stock
    
    def clean_all_data(self):
        """Application pipeline nettoyage complet"""
        print("\nNettoyage données...")
        
        for raw_book in self.raw_data:
            cleaned_book = {
                'title': self.clean_title(raw_book['title']),
                'price': self.clean_price(raw_book['price']),
                'rating': self.clean_rating(raw_book['rating']),
                'stock': self.clean_availability(raw_book['availability'])
            }
            
            self.cleaned_data.append(cleaned_book)
        
        print(f"✓ {len(self.cleaned_data)} enregistrements nettoyés")
    
    def detect_missing_values(self):
        """Détection valeurs manquantes par champ"""
        print("\nDétection valeurs manquantes...")
        
        fields = ['title', 'price', 'rating', 'stock']
        
        for field in fields:
            missing_count = sum(
                1 for book in self.cleaned_data
                if book[field] is None or book[field] == 'N/A'
            )
            
            percentage = (missing_count / len(self.cleaned_data) * 100) if self.cleaned_data else 0
            
            self.quality_report['missing_values'][field] = {
                'count': missing_count,
                'percentage': round(percentage, 2)
            }
            
            print(f"  {field}: {missing_count} manquants ({percentage:.2f}%)")
    
    def detect_duplicates(self):
        """Détection doublons par titre"""
        print("\nDétection doublons...")
        
        seen_titles = set()
        duplicates = []
        
        for book in self.cleaned_data:
            title = book['title']
            if title != 'N/A' and title in seen_titles:
                duplicates.append(title)
            seen_titles.add(title)
        
        self.quality_report['duplicates'] = list(set(duplicates))
        print(f"  {len(self.quality_report['duplicates'])} doublons détectés")
    
    def detect_price_outliers(self):
        """Détection outliers prix (méthode IQR)"""
        print("\nDétection outliers prix (méthode IQR)...")
        
        # Filtrer prix valides
        prices = [book['price'] for book in self.cleaned_data if book['price'] is not None]
        
        if len(prices) < 4:
            print("  Données insuffisantes pour détection outliers")
            return
        
        # Calcul quartiles
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        q1 = sorted_prices[n // 4]
        q3 = sorted_prices[3 * n // 4]
        iqr = q3 - q1
        
        # Limites outliers
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        # Détection
        outliers = []
        for book in self.cleaned_data:
            price = book['price']
            if price is not None and (price < lower_bound or price > upper_bound):
                outliers.append({
                    'title': book['title'],
                    'price': price,
                    'type': 'low' if price < lower_bound else 'high'
                })
        
        self.quality_report['outliers'] = outliers
        print(f"  Q1: £{q1:.2f}, Q3: £{q3:.2f}, IQR: £{iqr:.2f}")
        print(f"  Limites: [£{lower_bound:.2f}, £{upper_bound:.2f}]")
        print(f"  {len(outliers)} outliers détectés")
    
    def impute_missing_values(self):
        """Imputation valeurs manquantes"""
        print("\nImputation valeurs manquantes...")
        
        # Calcul valeurs imputation
        valid_prices = [book['price'] for book in self.cleaned_data if book['price'] is not None]
        valid_ratings = [book['rating'] for book in self.cleaned_data if book['rating'] is not None]
        
        if valid_prices:
            price_median = statistics.median(valid_prices)
        else:
            price_median = 0
        
        if valid_ratings:
            # Mode rating (valeur la plus fréquente)
            from collections import Counter
            rating_mode = Counter(valid_ratings).most_common(1)[0][0]
        else:
            rating_mode = 3
        
        # Imputation
        imputed_count = {'price': 0, 'rating': 0, 'stock': 0}
        
        for book in self.cleaned_data:
            if book['price'] is None:
                book['price'] = price_median
                imputed_count['price'] += 1
            
            if book['rating'] is None:
                book['rating'] = rating_mode
                imputed_count['rating'] += 1
            
            if book['stock'] is None:
                book['stock'] = 0
                imputed_count['stock'] += 1
        
        print(f"  Prix (médiane £{price_median:.2f}): {imputed_count['price']} imputés")
        print(f"  Rating (mode {rating_mode}): {imputed_count['rating']} imputés")
        print(f"  Stock (défaut 0): {imputed_count['stock']} imputés")
    
    def validate_data_consistency(self):
        """Validation cohérence croisée données"""
        print("\nValidation cohérence données...")
        
        errors = []
        
        for idx, book in enumerate(self.cleaned_data):
            # Validation prix > 0
            if book['price'] is not None and book['price'] <= 0:
                errors.append({
                    'index': idx,
                    'field': 'price',
                    'value': book['price'],
                    'reason': 'Prix <= 0'
                })
            
            # Validation rating ∈ [1, 5]
            if book['rating'] is not None and not (1 <= book['rating'] <= 5):
                errors.append({
                    'index': idx,
                    'field': 'rating',
                    'value': book['rating'],
                    'reason': 'Rating hors intervalle [1,5]'
                })
            
            # Validation stock >= 0
            if book['stock'] is not None and book['stock'] < 0:
                errors.append({
                    'index': idx,
                    'field': 'stock',
                    'value': book['stock'],
                    'reason': 'Stock négatif'
                })
            
            # Validation titre non vide
            if book['title'] == 'N/A' or book['title'] == '':
                errors.append({
                    'index': idx,
                    'field': 'title',
                    'value': book['title'],
                    'reason': 'Titre vide'
                })
        
        self.quality_report['validation_errors'] = errors
        print(f"  {len(errors)} erreurs validation détectées")
    
    def calculate_quality_metrics(self) -> Dict:
        """Calcul métriques qualité automatisées"""
        print("\n" + "=" * 70)
        print("MÉTRIQUES QUALITÉ")
        print("=" * 70)
        
        total_records = len(self.cleaned_data)
        
        # 1. Complétude (% champs remplis)
        complete_records = sum(
            1 for book in self.cleaned_data
            if all(book[field] is not None and book[field] != 'N/A' 
                   for field in ['title', 'price', 'rating', 'stock'])
        )
        
        completeness = (complete_records / total_records * 100) if total_records > 0 else 0
        
        print(f"\n✓ Complétude: {completeness:.2f}%")
        print(f"  {complete_records}/{total_records} enregistrements complets")
        
        # 2. Validité (% enregistrements valides)
        valid_records = total_records - len(self.quality_report['validation_errors'])
        validity = (valid_records / total_records * 100) if total_records > 0 else 0
        
        print(f"\n✓ Validité: {validity:.2f}%")
        print(f"  {valid_records}/{total_records} enregistrements valides")
        
        # 3. Unicité (% sans doublons)
        unique_records = total_records - len(self.quality_report['duplicates'])
        uniqueness = (unique_records / total_records * 100) if total_records > 0 else 0
        
        print(f"\n✓ Unicité: {uniqueness:.2f}%")
        print(f"  {unique_records}/{total_records} titres uniques")
        
        # 4. Cohérence (corrélation prix/rating)
        prices = [book['price'] for book in self.cleaned_data if book['price'] is not None]
        ratings = [book['rating'] for book in self.cleaned_data if book['rating'] is not None]
        
        if len(prices) > 1 and len(ratings) > 1 and len(prices) == len(ratings):
            try:
                mean_price = statistics.mean(prices)
                mean_rating = statistics.mean(ratings)
                
                numerator = sum((prices[i] - mean_price) * (ratings[i] - mean_rating) 
                              for i in range(len(prices)))
                
                denominator = (
                    sum((prices[i] - mean_price) ** 2 for i in range(len(prices))) ** 0.5 *
                    sum((ratings[i] - mean_rating) ** 2 for i in range(len(ratings))) ** 0.5
                )
                
                correlation = numerator / denominator if denominator != 0 else 0
            except:
                correlation = 0
        else:
            correlation = 0
        
        print(f"\n✓ Cohérence (corrélation prix/rating): {correlation:.3f}")
        
        metrics = {
            'completeness': round(completeness, 2),
            'validity': round(validity, 2),
            'uniqueness': round(uniqueness, 2),
            'consistency_correlation': round(correlation, 3),
            'total_records': total_records,
            'complete_records': complete_records,
            'valid_records': valid_records,
            'unique_records': unique_records
        }
        
        return metrics
    
    def export_cleaned_data(self):
        """Export données nettoyées en CSV"""
        output_dir = Path('./outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = output_dir / f'books_cleaned_{timestamp}.csv'
        
        fieldnames = ['title', 'price', 'rating', 'stock']
        
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.cleaned_data)
        
        print(f"\n✓ Données nettoyées exportées: {csv_file}")
    
    def export_quality_report(self, metrics: Dict):
        """Export rapport qualité JSON"""
        output_dir = Path('./outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_dir / f'quality_report_{timestamp}.json'
        
        report = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_records': len(self.cleaned_data),
                'source': self.base_url
            },
            'metrics': metrics,
            'quality_report': self.quality_report
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Rapport qualité exporté: {report_file}")


def main():
    print("=" * 70)
    print("EXERCICE 7: Pipeline de data cleaning")
    print("=" * 70)
    
    # Pipeline avec limite par défaut (3 pages)
    pipeline = DataCleaningPipeline(max_pages=3)
    
    # 1. Extraction données brutes
    pipeline.scrape_raw_data()
    
    # 2. Nettoyage
    pipeline.clean_all_data()
    
    # 3. Détection anomalies
    pipeline.detect_missing_values()
    pipeline.detect_duplicates()
    pipeline.detect_price_outliers()
    
    # 4. Imputation
    pipeline.impute_missing_values()
    
    # 5. Validation
    pipeline.validate_data_consistency()
    
    # 6. Métriques qualité
    metrics = pipeline.calculate_quality_metrics()
    
    # 7. Exports
    pipeline.export_cleaned_data()
    pipeline.export_quality_report(metrics)
    
    print("\n" + "=" * 70)
    print("✓ Exercice 7 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

