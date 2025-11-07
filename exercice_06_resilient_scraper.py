"""
Exercice 6: Scraper résilient
Système retry intelligent, logging, reprise sur interruption
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pickle
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ResilientScraper:
    """Scraper avec résilience maximale et reprise sur interruption"""
    
    def __init__(self, 
                 base_url="http://books.toscrape.com/",
                 max_pages=10,
                 checkpoint_file="scraper_checkpoint.pkl"):
        """
        Initialisation scraper résilient avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_pages: Limite nombre de pages (défaut: 10)
            checkpoint_file: Fichier sauvegarde progression
        """
        self.base_url = base_url
        self.max_pages = max_pages
        
        # Chemins
        self.data_dir = Path('./scraping_data')
        self.output_dir = Path('./outputs')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_file = self.data_dir / checkpoint_file
        
        # Session robuste
        self.session = self._create_robust_session()
        
        # Données
        self.books = []
        self.processed_pages = set()
        self.failed_pages = []
        
        # Métriques performance
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'total_duration': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Configuration logging
        self._setup_logging()
        
        # Tentative restauration checkpoint
        self._load_checkpoint()
    
    def _setup_logging(self):
        """Configuration système logging détaillé"""
        log_file = self.output_dir / 'scraper.log'
        
        # Configuration format
        log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Logger principal
        self.logger = logging.getLogger('ResilientScraper')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler fichier
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Éviter duplication si déjà configuré
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 70)
        self.logger.info("SCRAPER RÉSILIENT - DÉMARRAGE")
        self.logger.info("=" * 70)
    
    def _create_robust_session(self) -> requests.Session:
        """Création session avec stratégie retry intelligente"""
        session = requests.Session()
        
        # Stratégie retry avancée
        retry_strategy = Retry(
            total=5,  # 5 tentatives max
            backoff_factor=2,  # Backoff exponentiel: 2, 4, 8, 16, 32 secondes
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # User-Agent approprié
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Web Scraper)'
        })
        
        return session
    
    def _adaptive_delay(self, success: bool = True):
        """Délai adaptatif selon succès/échec"""
        if success:
            # Délai court si succès
            delay = random.uniform(0.5, 1.0)
        else:
            # Délai long si échec
            delay = random.uniform(2.0, 3.0)
        
        time.sleep(delay)
    
    def _adaptive_timeout(self, attempt: int) -> int:
        """Timeout adaptatif selon tentative"""
        base_timeout = 10
        return base_timeout + (attempt * 5)  # +5s par tentative
    
    def _save_checkpoint(self):
        """Sauvegarde progression automatique"""
        checkpoint_data = {
            'books': self.books,
            'processed_pages': self.processed_pages,
            'failed_pages': self.failed_pages,
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            self.logger.debug(f"Checkpoint sauvegardé: {len(self.books)} livres")
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde checkpoint: {e}")
    
    def _load_checkpoint(self) -> bool:
        """Chargement checkpoint précédent si disponible"""
        if not self.checkpoint_file.exists():
            self.logger.info("Aucun checkpoint trouvé - Démarrage nouveau scraping")
            return False
        
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            self.books = checkpoint_data.get('books', [])
            self.processed_pages = checkpoint_data.get('processed_pages', set())
            self.failed_pages = checkpoint_data.get('failed_pages', [])
            self.metrics = checkpoint_data.get('metrics', self.metrics)
            
            self.logger.info(f"✓ Checkpoint restauré: {len(self.books)} livres, "
                           f"{len(self.processed_pages)} pages traitées")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement checkpoint: {e}")
            return False
    
    def _convert_rating(self, rating_classes: List[str]) -> int:
        """Conversion classe CSS rating en valeur numérique"""
        ratings_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5
        }
        
        for cls in rating_classes:
            if cls in ratings_map:
                return ratings_map[cls]
        return 0
    
    def _scrape_page_with_retry(self, page_num: int, max_retries: int = 5) -> Optional[List[Dict]]:
        """Scraping page avec retry intelligent"""
        if page_num in self.processed_pages:
            self.logger.debug(f"Page {page_num} déjà traitée - Skip")
            return None
        
        # Construction URL
        if page_num == 1:
            page_url = f"{self.base_url}index.html"
        else:
            page_url = f"{self.base_url}catalogue/page-{page_num}.html"
        
        for attempt in range(1, max_retries + 1):
            try:
                self.metrics['total_requests'] += 1
                
                if attempt > 1:
                    self.metrics['retry_attempts'] += 1
                    self.logger.warning(f"Tentative {attempt}/{max_retries} - Page {page_num}")
                
                # Timeout adaptatif
                timeout = self._adaptive_timeout(attempt)
                
                self.logger.debug(f"GET {page_url} (timeout: {timeout}s)")
                response = self.session.get(page_url, timeout=timeout)
                
                # Détection rate limiting
                if response.status_code == 429:
                    self.logger.warning("Rate limit 429 détecté - Pause 60s")
                    time.sleep(60)
                    continue
                
                if response.status_code != 200:
                    self.logger.warning(f"Status {response.status_code} - Page {page_num}")
                    if attempt < max_retries:
                        self._adaptive_delay(success=False)
                        continue
                    else:
                        self.metrics['failed_requests'] += 1
                        self.failed_pages.append(page_num)
                        return None
                
                # Parsing
                soup = BeautifulSoup(response.content, 'html.parser')
                book_elements = soup.select('.product_pod')
                
                if not book_elements:
                    self.logger.info(f"Aucun livre page {page_num} - Fin pagination")
                    return None
                
                # Extraction
                page_books = []
                for book_elem in book_elements:
                    title_tag = book_elem.select_one('h3 a')
                    title = title_tag['title'] if title_tag else 'N/A'
                    
                    price_tag = book_elem.select_one('.price_color')
                    price_text = price_tag.get_text(strip=True) if price_tag else '£0.00'
                    price = float(price_text.replace('£', '').replace(',', ''))
                    
                    rating_tag = book_elem.select_one('.star-rating')
                    rating = self._convert_rating(rating_tag['class']) if rating_tag else 0
                    
                    page_books.append({
                        'title': title,
                        'price': price,
                        'rating': rating,
                        'page': page_num
                    })
                
                # Succès
                self.metrics['successful_requests'] += 1
                self.processed_pages.add(page_num)
                
                self.logger.info(f"✓ Page {page_num}: {len(page_books)} livres extraits")
                
                return page_books
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout page {page_num} (tentative {attempt}/{max_retries})")
                if attempt < max_retries:
                    self._adaptive_delay(success=False)
                else:
                    self.metrics['failed_requests'] += 1
                    self.failed_pages.append(page_num)
                    return None
            
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erreur requête page {page_num}: {e}")
                if attempt < max_retries:
                    self._adaptive_delay(success=False)
                else:
                    self.metrics['failed_requests'] += 1
                    self.failed_pages.append(page_num)
                    return None
            
            except Exception as e:
                self.logger.error(f"Erreur inattendue page {page_num}: {e}")
                self.metrics['failed_requests'] += 1
                self.failed_pages.append(page_num)
                return None
        
        return None
    
    def scrape_all_pages(self):
        """Scraping avec pagination et sauvegarde automatique"""
        self.logger.info(f"Début scraping (limite: {self.max_pages} pages)")
        self.metrics['start_time'] = datetime.now()
        
        try:
            for page_num in range(1, self.max_pages + 1):
                self.logger.info(f"\n--- Page {page_num}/{self.max_pages} ---")
                
                page_books = self._scrape_page_with_retry(page_num)
                
                if page_books is None and page_num not in self.processed_pages:
                    # Échec ou fin pagination
                    if page_num == 1:
                        self.logger.error("Échec page 1 - Arrêt")
                        break
                    else:
                        self.logger.info("Fin pagination détectée")
                        break
                
                if page_books:
                    self.books.extend(page_books)
                
                # Sauvegarde checkpoint régulière
                if page_num % 3 == 0:  # Tous les 3 pages
                    self._save_checkpoint()
                
                # Délai respectueux
                if page_num < self.max_pages:
                    self._adaptive_delay(success=True)
            
        except KeyboardInterrupt:
            self.logger.warning("\n⚠ INTERRUPTION UTILISATEUR (Ctrl+C)")
            self.logger.info("Sauvegarde progression...")
            self._save_checkpoint()
            self.logger.info("✓ Progression sauvegardée - Peut être reprise ultérieurement")
            raise
        
        finally:
            # Sauvegarde finale
            self._save_checkpoint()
            self.metrics['end_time'] = datetime.now()
        
        self.logger.info(f"\n✓ Scraping terminé: {len(self.books)} livres extraits")
    
    def generate_performance_report(self) -> Dict:
        """Génération rapport performance temps réel"""
        if self.metrics['start_time'] and self.metrics['end_time']:
            duration = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        else:
            duration = 0
        
        self.metrics['total_duration'] = duration
        
        # Calcul vitesse
        books_per_second = len(self.books) / duration if duration > 0 else 0
        
        report = {
            'summary': {
                'total_books': len(self.books),
                'pages_processed': len(self.processed_pages),
                'pages_failed': len(self.failed_pages),
                'duration_seconds': round(duration, 2),
                'extraction_speed': round(books_per_second, 2)
            },
            'requests': {
                'total': self.metrics['total_requests'],
                'successful': self.metrics['successful_requests'],
                'failed': self.metrics['failed_requests'],
                'retry_attempts': self.metrics['retry_attempts'],
                'success_rate': round(
                    (self.metrics['successful_requests'] / self.metrics['total_requests'] * 100)
                    if self.metrics['total_requests'] > 0 else 0, 2
                )
            },
            'failed_pages': self.failed_pages,
            'timestamp': datetime.now().isoformat()
        }
        
        # Logging rapport
        self.logger.info("\n" + "=" * 70)
        self.logger.info("RAPPORT PERFORMANCE")
        self.logger.info("=" * 70)
        self.logger.info(f"Livres extraits: {report['summary']['total_books']}")
        self.logger.info(f"Pages traitées: {report['summary']['pages_processed']}")
        self.logger.info(f"Pages échouées: {report['summary']['pages_failed']}")
        self.logger.info(f"Durée totale: {report['summary']['duration_seconds']:.2f}s")
        self.logger.info(f"Vitesse: {report['summary']['extraction_speed']:.2f} livres/sec")
        self.logger.info(f"Requêtes réussies: {report['requests']['successful']}/{report['requests']['total']}")
        self.logger.info(f"Taux succès: {report['requests']['success_rate']:.2f}%")
        self.logger.info(f"Tentatives retry: {report['requests']['retry_attempts']}")
        
        return report
    
    def export_data(self):
        """Export données et rapports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export livres
        books_file = self.output_dir / f'books_resilient_{timestamp}.json'
        with open(books_file, 'w', encoding='utf-8') as f:
            json.dump(self.books, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✓ Données exportées: {books_file}")
        
        # Export rapport performance
        report = self.generate_performance_report()
        report_file = self.output_dir / f'performance_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✓ Rapport exporté: {report_file}")
    
    def cleanup_checkpoint(self):
        """Nettoyage checkpoint après succès complet"""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                self.logger.info("✓ Checkpoint nettoyé")
            except Exception as e:
                self.logger.warning(f"Impossible nettoyer checkpoint: {e}")


def main():
    print("=" * 70)
    print("EXERCICE 6: Scraper résilient")
    print("=" * 70)
    
    # Scraper avec limite par défaut (10 pages)
    scraper = ResilientScraper(max_pages=10)
    
    try:
        # Scraping résilient
        scraper.scrape_all_pages()
        
        # Export données et rapports
        scraper.export_data()
        
        # Nettoyage checkpoint
        scraper.cleanup_checkpoint()
        
        print("\n" + "=" * 70)
        print("✓ Exercice 6 terminé avec succès")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("⚠ Interruption - Progression sauvegardée")
        print("Relancez le script pour reprendre")
        print("=" * 70)


if __name__ == "__main__":
    main()

