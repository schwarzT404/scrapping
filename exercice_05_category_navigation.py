"""
Exercice 5: Navigation catégorielle avancée
Cartographie arborescence catégories et statistiques
"""

import sys
import io

# Configuration encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import time
import random
import statistics


class CategoryNavigator:
    """Navigateur et analyseur arborescence catégories"""
    
    def __init__(self, base_url="https://books.toscrape.com/", max_books_per_category=20):
        """
        Initialisation navigateur avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_books_per_category: Limite livres par catégorie (défaut: 20)
        """
        self.base_url = base_url
        self.max_books_per_category = max_books_per_category
        self.session = requests.Session()
        
        self.categories = {}
        self.all_books = []
        
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
        return 0
    
    def discover_categories(self):
        """Découverte toutes les catégories disponibles"""
        print("Découverte catégories...\n")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Navigation latérale catégories
            category_links = soup.select('.side_categories ul li ul li a')
            
            for link in category_links:
                category_name = link.get_text(strip=True)
                category_url = self.base_url + link['href']
                
                self.categories[category_name] = {
                    'name': category_name,
                    'url': category_url,
                    'books': [],
                    'statistics': {}
                }
            
            print(f"✓ {len(self.categories)} catégories découvertes")
            
        except Exception as e:
            print(f"✗ Erreur découverte catégories: {e}")
    
    def scrape_category(self, category_name: str, category_data: Dict):
        """Scraping livres d'une catégorie spécifique"""
        print(f"  Scraping: {category_name}...", end=' ')
        
        try:
            response = self.session.get(category_data['url'], timeout=10)
            
            if response.status_code != 200:
                print(f"Erreur {response.status_code}")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            book_elements = soup.select('.product_pod')
            
            # Limite nombre de livres par catégorie
            book_elements = book_elements[:self.max_books_per_category]
            
            for book_elem in book_elements:
                # Titre
                title_tag = book_elem.select_one('h3 a')
                title = title_tag['title'] if title_tag else 'N/A'
                
                # Prix
                price_tag = book_elem.select_one('.price_color')
                price_text = price_tag.get_text(strip=True) if price_tag else '£0.00'
                price = float(price_text.replace('£', '').replace(',', ''))
                
                # Rating
                rating_tag = book_elem.select_one('.star-rating')
                rating = self._convert_rating(rating_tag['class']) if rating_tag else 0
                
                # Disponibilité
                avail_tag = book_elem.select_one('.availability')
                in_stock = 'in stock' in avail_tag.get_text().lower() if avail_tag else False
                
                book_data = {
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'in_stock': in_stock,
                    'category': category_name
                }
                
                category_data['books'].append(book_data)
                self.all_books.append(book_data)
            
            print(f"{len(category_data['books'])} livres")
            
        except Exception as e:
            print(f"Erreur: {e}")
    
    def scrape_all_categories(self):
        """Scraping tous les livres de toutes catégories"""
        print(f"\nScraping catégories (limite: {self.max_books_per_category} livres/catégorie)...\n")
        
        for idx, (category_name, category_data) in enumerate(self.categories.items(), 1):
            print(f"[{idx}/{len(self.categories)}]", end=' ')
            self.scrape_category(category_name, category_data)
            
            # Délai entre catégories
            if idx < len(self.categories):
                self._respectful_delay()
        
        print(f"\n✓ Total: {len(self.all_books)} livres extraits")
    
    def calculate_category_statistics(self):
        """Calcul statistiques par catégorie"""
        print("\nCalcul statistiques par catégorie...")
        
        for category_name, category_data in self.categories.items():
            books = category_data['books']
            
            if not books:
                category_data['statistics'] = {
                    'total_books': 0,
                    'avg_price': 0,
                    'min_price': 0,
                    'max_price': 0,
                    'avg_rating': 0,
                    'weighted_score': 0,
                    'in_stock_percentage': 0
                }
                continue
            
            prices = [book['price'] for book in books]
            ratings = [book['rating'] for book in books]
            in_stock_count = sum(1 for book in books if book['in_stock'])
            
            avg_price = statistics.mean(prices)
            avg_rating = statistics.mean(ratings) if ratings else 0
            
            # Score pondéré: (prix moyen × rating moyen)
            weighted_score = avg_price * avg_rating
            
            category_data['statistics'] = {
                'total_books': len(books),
                'avg_price': round(avg_price, 2),
                'min_price': round(min(prices), 2),
                'max_price': round(max(prices), 2),
                'avg_rating': round(avg_rating, 2),
                'weighted_score': round(weighted_score, 2),
                'in_stock_percentage': round((in_stock_count / len(books) * 100), 1)
            }
        
        print("✓ Statistiques calculées")
    
    def generate_category_rankings(self):
        """Génération classements catégories multi-critères"""
        print("\n" + "=" * 70)
        print("CLASSEMENTS CATÉGORIES")
        print("=" * 70)
        
        # Filtrer catégories avec livres
        valid_categories = {
            name: data for name, data in self.categories.items()
            if data['statistics']['total_books'] > 0
        }
        
        # 1. Plus grand nombre de livres
        print("\n📚 Top 5 - Plus de livres:")
        sorted_by_books = sorted(
            valid_categories.items(),
            key=lambda x: x[1]['statistics']['total_books'],
            reverse=True
        )[:5]
        
        for rank, (name, data) in enumerate(sorted_by_books, 1):
            stats = data['statistics']
            print(f"  {rank}. {name}: {stats['total_books']} livres")
        
        # 2. Prix moyen le plus élevé
        print("\n💰 Top 5 - Prix moyen le plus élevé:")
        sorted_by_price = sorted(
            valid_categories.items(),
            key=lambda x: x[1]['statistics']['avg_price'],
            reverse=True
        )[:5]
        
        for rank, (name, data) in enumerate(sorted_by_price, 1):
            stats = data['statistics']
            print(f"  {rank}. {name}: £{stats['avg_price']:.2f}")
        
        # 3. Meilleur rating moyen
        print("\n⭐ Top 5 - Meilleur rating moyen:")
        sorted_by_rating = sorted(
            valid_categories.items(),
            key=lambda x: x[1]['statistics']['avg_rating'],
            reverse=True
        )[:5]
        
        for rank, (name, data) in enumerate(sorted_by_rating, 1):
            stats = data['statistics']
            print(f"  {rank}. {name}: {stats['avg_rating']:.2f}★")
        
        # 4. Meilleur score pondéré
        print("\n🏆 Top 5 - Score pondéré (prix × rating):")
        sorted_by_weighted = sorted(
            valid_categories.items(),
            key=lambda x: x[1]['statistics']['weighted_score'],
            reverse=True
        )[:5]
        
        for rank, (name, data) in enumerate(sorted_by_weighted, 1):
            stats = data['statistics']
            print(f"  {rank}. {name}: {stats['weighted_score']:.2f}")
    
    def detect_underrepresented_categories(self):
        """Détection catégories sous-représentées"""
        print("\n📉 Catégories sous-représentées (<= 5 livres):")
        
        underrepresented = [
            (name, data['statistics']['total_books'])
            for name, data in self.categories.items()
            if data['statistics']['total_books'] <= 5
        ]
        
        if not underrepresented:
            print("  Aucune catégorie sous-représentée")
        else:
            for name, count in sorted(underrepresented, key=lambda x: x[1]):
                print(f"  - {name}: {count} livres")
    
    def full_text_search(self, query: str) -> List[Dict]:
        """Recherche full-text dans corpus complet"""
        query_lower = query.lower()
        results = []
        
        for book in self.all_books:
            if query_lower in book['title'].lower():
                results.append(book)
        
        return results
    
    def demo_full_text_search(self):
        """Démonstration recherche full-text"""
        print("\n🔍 Démonstration recherche full-text:")
        
        test_queries = ['the', 'python', 'love', 'dark']
        
        for query in test_queries:
            results = self.full_text_search(query)
            print(f"  '{query}': {len(results)} résultats")
            
            if results:
                # Affichage premier résultat
                first = results[0]
                print(f"    Ex: {first['title'][:50]}... ({first['category']})")
    
    def build_hierarchy_structure(self) -> Dict:
        """Construction structure arborescente hiérarchique"""
        hierarchy = {
            'root': 'Books',
            'total_categories': len(self.categories),
            'total_books': len(self.all_books),
            'categories': []
        }
        
        for category_name, category_data in self.categories.items():
            category_node = {
                'name': category_name,
                'statistics': category_data['statistics'],
                'books_sample': [
                    {
                        'title': book['title'],
                        'price': book['price'],
                        'rating': book['rating']
                    }
                    for book in category_data['books'][:5]  # Échantillon 5 livres
                ]
            }
            hierarchy['categories'].append(category_node)
        
        return hierarchy
    
    def export_hierarchy_json(self):
        """Export arborescence JSON nested"""
        output_dir = Path('./outputs/exercice_05')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hierarchy_file = output_dir / f'categories_hierarchy_{timestamp}.json'
        
        hierarchy = self.build_hierarchy_structure()
        
        with open(hierarchy_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Hiérarchie exportée: {hierarchy_file}")
    
    def export_statistics_json(self):
        """Export statistiques détaillées"""
        output_dir = Path('./outputs/exercice_05')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = output_dir / f'categories_statistics_{timestamp}.json'
        
        statistics_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_categories': len(self.categories),
                'total_books': len(self.all_books),
                'max_books_per_category': self.max_books_per_category
            },
            'categories': {
                name: {
                    'name': name,
                    'url': data['url'],
                    'statistics': data['statistics']
                }
                for name, data in self.categories.items()
            }
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(statistics_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Statistiques exportées: {stats_file}")


def main():
    print("=" * 70)
    print("EXERCICE 5: Navigation catégorielle avancée")
    print("=" * 70)
    
    # Navigateur avec limite par défaut (20 livres/catégorie)
    navigator = CategoryNavigator(max_books_per_category=20)
    
    # Découverte catégories
    navigator.discover_categories()
    
    # Scraping toutes catégories
    navigator.scrape_all_categories()
    
    # Calcul statistiques
    navigator.calculate_category_statistics()
    
    # Classements
    navigator.generate_category_rankings()
    
    # Détection sous-représentation
    navigator.detect_underrepresented_categories()
    
    # Démonstration recherche full-text
    navigator.demo_full_text_search()
    
    # Exports
    navigator.export_hierarchy_json()
    navigator.export_statistics_json()
    
    print("\n" + "=" * 70)
    print("✓ Exercice 5 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

