"""
Exercice 4: Analyse de marché livresque
Statistiques avancées et visualisations avec matplotlib
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import statistics
from collections import Counter
import time
import random


class BookMarketAnalyzer:
    """Analyseur marché livresque avec statistiques et visualisations"""
    
    def __init__(self, base_url="https://books.toscrape.com/", max_pages=3):
        """
        Initialisation analyseur avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_pages: Limite nombre de pages à analyser (défaut: 3)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        self.books = []
        
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
    
    def _extract_stock_status(self, soup, book_element) -> Dict:
        """Extraction statut disponibilité"""
        availability_tag = book_element.select_one('.availability')
        
        if not availability_tag:
            return {'in_stock': False, 'quantity': 0}
        
        text = availability_tag.get_text(strip=True).lower()
        
        if 'in stock' in text:
            # Extraction quantité si disponible
            import re
            match = re.search(r'(\d+)\s+available', text)
            quantity = int(match.group(1)) if match else 1
            return {'in_stock': True, 'quantity': quantity}
        else:
            return {'in_stock': False, 'quantity': 0}
    
    def scrape_books(self):
        """Extraction données livres pour analyse"""
        print(f"Scraping livres (limite: {self.max_pages} pages)...\n")
        
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
                    print(f"Erreur page {page_num}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                book_elements = soup.select('.product_pod')
                
                if not book_elements:
                    break
                
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
                    
                    # Catégorie (navigation breadcrumb sur page principale)
                    category = 'General'  # Simplifié pour cette analyse
                    
                    # Disponibilité
                    avail_tag = book_elem.select_one('.availability')
                    in_stock = 'in stock' in avail_tag.get_text().lower() if avail_tag else False
                    
                    book_data = {
                        'title': title,
                        'price': price,
                        'rating': rating,
                        'category': category,
                        'in_stock': in_stock
                    }
                    
                    self.books.append(book_data)
                
                page_num += 1
                
                if page_num <= self.max_pages:
                    self._respectful_delay()
                
            except Exception as e:
                print(f"✗ Erreur scraping page {page_num}: {e}")
                break
        
        print(f"\n✓ {len(self.books)} livres extraits pour analyse")
    
    def calculate_price_statistics(self) -> Dict:
        """Calcul statistiques prix"""
        if not self.books:
            return {}
        
        prices = [book['price'] for book in self.books]
        
        # Statistiques de base
        price_stats = {
            'mean': statistics.mean(prices),
            'median': statistics.median(prices),
            'min': min(prices),
            'max': max(prices),
            'std_dev': statistics.stdev(prices) if len(prices) > 1 else 0
        }
        
        # Quartiles
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        price_stats['q1'] = sorted_prices[n // 4]
        price_stats['q3'] = sorted_prices[3 * n // 4]
        price_stats['iqr'] = price_stats['q3'] - price_stats['q1']
        
        return price_stats
    
    def calculate_price_by_rating(self) -> Dict:
        """Calcul prix moyen par rating"""
        prices_by_rating = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for book in self.books:
            rating = book['rating']
            if rating in prices_by_rating:
                prices_by_rating[rating].append(book['price'])
        
        avg_prices = {}
        for rating, prices in prices_by_rating.items():
            if prices:
                avg_prices[rating] = {
                    'mean': statistics.mean(prices),
                    'count': len(prices)
                }
            else:
                avg_prices[rating] = {
                    'mean': 0,
                    'count': 0
                }
        
        return avg_prices
    
    def calculate_price_by_category(self) -> Dict:
        """Calcul prix moyen par catégorie"""
        prices_by_category = {}
        
        for book in self.books:
            category = book['category']
            if category not in prices_by_category:
                prices_by_category[category] = []
            prices_by_category[category].append(book['price'])
        
        avg_prices = {}
        for category, prices in prices_by_category.items():
            if prices:
                avg_prices[category] = {
                    'mean': statistics.mean(prices),
                    'median': statistics.median(prices),
                    'count': len(prices)
                }
        
        return avg_prices
    
    def detect_out_of_stock(self) -> List[Dict]:
        """Détection livres en rupture de stock"""
        out_of_stock = [book for book in self.books if not book['in_stock']]
        return out_of_stock
    
    def analyze_rating_distribution(self) -> Dict:
        """Analyse distribution ratings"""
        ratings = [book['rating'] for book in self.books]
        rating_counts = Counter(ratings)
        
        total = len(ratings)
        distribution = {}
        
        for rating in [1, 2, 3, 4, 5]:
            count = rating_counts.get(rating, 0)
            percentage = (count / total * 100) if total > 0 else 0
            distribution[rating] = {
                'count': count,
                'percentage': percentage
            }
        
        return distribution
    
    def calculate_price_rating_correlation(self) -> float:
        """Calcul corrélation prix/rating (Pearson)"""
        if len(self.books) < 2:
            return 0.0
        
        prices = [book['price'] for book in self.books]
        ratings = [book['rating'] for book in self.books]
        
        try:
            # Calcul coefficient de corrélation de Pearson manuel
            n = len(prices)
            
            mean_price = statistics.mean(prices)
            mean_rating = statistics.mean(ratings)
            
            numerator = sum((prices[i] - mean_price) * (ratings[i] - mean_rating) 
                          for i in range(n))
            
            denominator = (
                sum((prices[i] - mean_price) ** 2 for i in range(n)) ** 0.5 *
                sum((ratings[i] - mean_rating) ** 2 for i in range(n)) ** 0.5
            )
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            return correlation
            
        except Exception:
            return 0.0
    
    def generate_analysis_report(self) -> Dict:
        """Génération rapport d'analyse complet"""
        print("\n" + "=" * 70)
        print("RAPPORT D'ANALYSE MARCHÉ")
        print("=" * 70)
        
        # Statistiques prix
        price_stats = self.calculate_price_statistics()
        print("\n📊 Statistiques Prix:")
        print(f"  Moyenne: £{price_stats['mean']:.2f}")
        print(f"  Médiane: £{price_stats['median']:.2f}")
        print(f"  Min: £{price_stats['min']:.2f}")
        print(f"  Max: £{price_stats['max']:.2f}")
        print(f"  Écart-type: £{price_stats['std_dev']:.2f}")
        print(f"  IQR: £{price_stats['iqr']:.2f}")
        
        # Prix par rating
        price_by_rating = self.calculate_price_by_rating()
        print("\n⭐ Prix moyen par rating:")
        for rating in sorted(price_by_rating.keys()):
            data = price_by_rating[rating]
            print(f"  {rating} étoiles: £{data['mean']:.2f} ({data['count']} livres)")
        
        # Distribution ratings
        rating_dist = self.analyze_rating_distribution()
        print("\n📈 Distribution ratings:")
        for rating in sorted(rating_dist.keys()):
            data = rating_dist[rating]
            print(f"  {rating} étoiles: {data['count']} livres ({data['percentage']:.1f}%)")
        
        # Corrélation prix/rating
        correlation = self.calculate_price_rating_correlation()
        print(f"\n🔗 Corrélation prix/rating: {correlation:.3f}")
        
        if abs(correlation) < 0.3:
            interpretation = "faible"
        elif abs(correlation) < 0.7:
            interpretation = "modérée"
        else:
            interpretation = "forte"
        
        print(f"  Interprétation: corrélation {interpretation}")
        
        # Ruptures de stock
        out_of_stock = self.detect_out_of_stock()
        print(f"\n📦 Livres en rupture: {len(out_of_stock)}/{len(self.books)}")
        
        # Construction rapport JSON
        report = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_books': len(self.books),
                'source': self.base_url,
                'pages_analyzed': self.max_pages
            },
            'price_statistics': price_stats,
            'price_by_rating': price_by_rating,
            'rating_distribution': rating_dist,
            'correlation_price_rating': correlation,
            'out_of_stock_count': len(out_of_stock)
        }
        
        return report
    
    def create_visualizations(self):
        """Génération visualisations matplotlib"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("\n✗ matplotlib non disponible - Visualisations ignorées")
            return
        
        print("\nGénération visualisations...")
        
        # Configuration style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Analyse Marché Livresque', fontsize=16, fontweight='bold')
        
        # 1. Histogramme distribution prix
        ax1 = axes[0, 0]
        prices = [book['price'] for book in self.books]
        ax1.hist(prices, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax1.set_title('Distribution des Prix')
        ax1.set_xlabel('Prix (£)')
        ax1.set_ylabel('Fréquence')
        ax1.axvline(statistics.mean(prices), color='red', linestyle='--', 
                    label=f'Moyenne: £{statistics.mean(prices):.2f}')
        ax1.legend()
        
        # 2. Bar chart prix moyen par rating
        ax2 = axes[0, 1]
        price_by_rating = self.calculate_price_by_rating()
        ratings = sorted(price_by_rating.keys())
        avg_prices = [price_by_rating[r]['mean'] for r in ratings]
        counts = [price_by_rating[r]['count'] for r in ratings]
        
        bars = ax2.bar(ratings, avg_prices, color='coral', edgecolor='black', alpha=0.7)
        ax2.set_title('Prix Moyen par Rating')
        ax2.set_xlabel('Rating (étoiles)')
        ax2.set_ylabel('Prix moyen (£)')
        ax2.set_xticks(ratings)
        
        # Annotations nombres de livres
        for i, (bar, count) in enumerate(zip(bars, counts)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'n={count}', ha='center', va='bottom', fontsize=8)
        
        # 3. Scatter plot corrélation prix/rating
        ax3 = axes[1, 0]
        prices = [book['price'] for book in self.books]
        ratings = [book['rating'] for book in self.books]
        
        ax3.scatter(ratings, prices, alpha=0.5, color='green')
        ax3.set_title('Corrélation Prix vs Rating')
        ax3.set_xlabel('Rating (étoiles)')
        ax3.set_ylabel('Prix (£)')
        
        # Ligne de tendance
        z = np.polyfit(ratings, prices, 1)
        p = np.poly1d(z)
        ax3.plot(sorted(set(ratings)), p(sorted(set(ratings))), 
                "r--", alpha=0.8, label='Tendance')
        
        correlation = self.calculate_price_rating_correlation()
        ax3.text(0.05, 0.95, f'r = {correlation:.3f}', 
                transform=ax3.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.5))
        ax3.legend()
        
        # 4. Pie chart distribution ratings
        ax4 = axes[1, 1]
        rating_dist = self.analyze_rating_distribution()
        labels = [f'{r}★' for r in sorted(rating_dist.keys())]
        sizes = [rating_dist[r]['count'] for r in sorted(rating_dist.keys())]
        colors = ['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff']
        
        wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors,
                                           autopct='%1.1f%%', startangle=90)
        ax4.set_title('Distribution des Ratings')
        
        # Style autotexts
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
        
        plt.tight_layout()
        
        # Sauvegarde
        output_dir = Path('./outputs/exercice_04')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_file = output_dir / f'book_market_analysis_{timestamp}.png'
        
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"✓ Visualisations sauvegardées: {plot_file}")
        
        plt.close()
    
    def export_report(self, report: Dict):
        """Export rapport JSON"""
        output_dir = Path('./outputs/exercice_04')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_dir / f'market_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Rapport exporté: {report_file}")


def main():
    print("=" * 70)
    print("EXERCICE 4: Analyse de marché livresque")
    print("=" * 70)
    
    # Analyseur avec limite par défaut (3 pages = ~60 livres)
    analyzer = BookMarketAnalyzer(max_pages=3)
    
    # Scraping données
    analyzer.scrape_books()
    
    # Analyse et rapport
    report = analyzer.generate_analysis_report()
    
    # Visualisations
    analyzer.create_visualizations()
    
    # Export rapport
    analyzer.export_report(report)
    
    print("\n" + "=" * 70)
    print("✓ Exercice 4 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

