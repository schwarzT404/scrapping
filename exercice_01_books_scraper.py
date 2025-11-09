"""
Exercice 1: Books to Scrape - Extraction complète
Architecture robuste avec pagination automatique et gestion d'erreurs
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BooksScraperComplete:
    """Extracteur complet de données bibliographiques avec pagination"""
    
    def __init__(self, base_url="https://books.toscrape.com/", max_pages=20):
        """
        Initialisation scraper avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_pages: Limite nombre de pages à scraper (défaut: 20)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = self._create_robust_session()
        self.books_data = []
        
    def _create_robust_session(self):
        """Configuration session avec stratégie de retry"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _respectful_delay(self):
        """Délai aléatoire entre requêtes"""
        time.sleep(random.uniform(1, 2))
    
    def _convert_rating(self, rating_class):
        """Conversion classe CSS rating en valeur numérique"""
        ratings_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        for word, value in ratings_map.items():
            if word in rating_class:
                return value
        return 0
    
    def _extract_stock_number(self, stock_text):
        """Extraction nombre d'exemplaires depuis texte"""
        import re
        match = re.search(r'\d+', stock_text)
        return int(match.group()) if match else 0
    
    def _scrape_book_detail(self, detail_url):
        """Extraction données page détail livre"""
        try:
            response = self.session.get(detail_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            description_tag = soup.select_one('#product_description + p')
            description = description_tag.get_text(strip=True) if description_tag else 'N/A'
            
            breadcrumb = soup.select('.breadcrumb li')
            category_main = breadcrumb[2].get_text(strip=True) if len(breadcrumb) > 2 else 'N/A'
            
            stock_tag = soup.select_one('.instock.availability')
            stock_text = stock_tag.get_text(strip=True) if stock_tag else ''
            stock_number = self._extract_stock_number(stock_text)
            
            img_tag = soup.select_one('#product_gallery img')
            img_url = urljoin(self.base_url, img_tag['src']) if img_tag else 'N/A'
            
            return {
                'description': description,
                'category_main': category_main,
                'stock_available': stock_number,
                'image_hd_url': img_url
            }
            
        except requests.exceptions.RequestException:
            return None
    
    def _scrape_page(self, page_url):
        """Extraction livres depuis page catalogue"""
        try:
            response = self.session.get(page_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            books = soup.select('.product_pod')
            
            page_books = []
            for book in books:
                title_tag = book.select_one('h3 a')
                title = title_tag['title'] if title_tag else 'N/A'
                
                book_url = urljoin(page_url, title_tag['href']) if title_tag else 'N/A'
                
                price_tag = book.select_one('.price_color')
                price_text = price_tag.get_text(strip=True) if price_tag else '£0.00'
                price = float(price_text.replace('£', '').replace(',', ''))
                
                rating_tag = book.select_one('.star-rating')
                rating = self._convert_rating(rating_tag['class']) if rating_tag else 0
                
                detail_data = self._scrape_book_detail(book_url)
                self._respectful_delay()
                
                book_data = {
                    'title': title,
                    'url': book_url,
                    'price': price,
                    'rating': rating
                }
                
                if detail_data:
                    book_data.update(detail_data)
                else:
                    book_data.update({
                        'description': 'N/A',
                        'category_main': 'N/A',
                        'stock_available': 0,
                        'image_hd_url': 'N/A'
                    })
                
                page_books.append(book_data)
            
            return page_books
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur scraping page {page_url}: {e}")
            return []
    
    def scrape_all_pages(self):
        """Pagination automatique et extraction complète"""
        page_num = 1
        
        print(f"Début scraping (limite: {self.max_pages} pages)...\n")
        
        while page_num <= self.max_pages:
            if page_num == 1:
                page_url = urljoin(self.base_url, 'index.html')
            else:
                page_url = urljoin(self.base_url, f'catalogue/page-{page_num}.html')
            
            print(f"Scraping page {page_num}/{self.max_pages}...")
            books = self._scrape_page(page_url)
            
            if not books:
                print(f"Pas de livres trouvés page {page_num} - Arrêt")
                break
            
            self.books_data.extend(books)
            page_num += 1
            
            if page_num <= self.max_pages:
                self._respectful_delay()
        
        print(f"\nExtraction terminée: {len(self.books_data)} livres ({page_num-1} pages)")
    
    def save_to_json(self):
        """Sauvegarde JSON hiérarchique avec timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        from pathlib import Path
        output_dir = Path('./outputs/exercice_01')
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = str(output_dir / f'books_data_{timestamp}.json')
        
        output_structure = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_books': len(self.books_data),
                'source': self.base_url
            },
            'books': self.books_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, ensure_ascii=False, indent=2)
        
        print(f"Données sauvegardées: {filename}")
        return filename


def main():
    print("=" * 70)
    print("EXERCICE 1: Books to Scrape - Extraction complète")
    print("=" * 70)
    
    scraper = BooksScraperComplete(max_pages=20)
    scraper.scrape_all_pages()
    scraper.save_to_json()
    
    print("\n" + "=" * 70)
    print("✓ Exercice 1 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()