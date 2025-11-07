"""
Exercice 8: Scraping multi-sources
Architecture modulaire plugin-based avec parallel processing
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml


class ScraperPlugin(ABC):
    """Interface abstraite pour plugins scraper"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.data = []
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'records_extracted': 0,
            'success': False
        }
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Méthode scraping à implémenter par chaque plugin"""
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalisation schéma unifié"""
        pass
    
    def get_source_name(self) -> str:
        """Nom source"""
        return self.__class__.__name__.replace('ScraperPlugin', '')


class BooksScraperPlugin(ScraperPlugin):
    """Plugin scraping books.toscrape.com"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config.get('url', 'https://books.toscrape.com/')
        self.max_pages = config.get('max_pages', 2)
    
    def scrape(self) -> List[Dict]:
        """Scraping livres"""
        print(f"  [{self.get_source_name()}] Scraping (limite: {self.max_pages} pages)...")
        
        self.metrics['start_time'] = datetime.now()
        
        try:
            for page_num in range(1, self.max_pages + 1):
                if page_num == 1:
                    page_url = f"{self.base_url}index.html"
                else:
                    page_url = f"{self.base_url}catalogue/page-{page_num}.html"
                
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                books = soup.select('.product_pod')
                
                if not books:
                    break
                
                for book in books:
                    title_tag = book.select_one('h3 a')
                    title = title_tag['title'] if title_tag else 'N/A'
                    
                    price_tag = book.select_one('.price_color')
                    price_text = price_tag.get_text(strip=True) if price_tag else '£0.00'
                    price = float(price_text.replace('£', '').replace(',', ''))
                    
                    rating_tag = book.select_one('.star-rating')
                    rating_class = rating_tag['class'][1] if rating_tag and len(rating_tag['class']) > 1 else 'Zero'
                    
                    self.data.append({
                        'title': title,
                        'price': price,
                        'rating': rating_class,
                        'source': 'books.toscrape.com'
                    })
                
                time.sleep(0.5)
            
            self.metrics['success'] = True
            
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            self.metrics['success'] = False
        
        finally:
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration'] = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            self.metrics['records_extracted'] = len(self.data)
        
        print(f"  ✓ {len(self.data)} livres extraits en {self.metrics['duration']:.2f}s")
        return self.data
    
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalisation schéma unifié"""
        ratings_map = {
            'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5,
            'Zero': 0
        }
        
        normalized = []
        for item in raw_data:
            normalized.append({
                'type': 'book',
                'title': item['title'],
                'value': item['price'],
                'rating': ratings_map.get(item['rating'], 0),
                'source': item['source'],
                'metadata': {}
            })
        
        return normalized


class QuotesScraperPlugin(ScraperPlugin):
    """Plugin scraping quotes.toscrape.com"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config.get('url', 'http://quotes.toscrape.com/')
        self.max_pages = config.get('max_pages', 1)
    
    def scrape(self) -> List[Dict]:
        """Scraping citations"""
        print(f"  [{self.get_source_name()}] Scraping (limite: {self.max_pages} pages)...")
        
        self.metrics['start_time'] = datetime.now()
        
        try:
            for page_num in range(1, self.max_pages + 1):
                if page_num == 1:
                    page_url = self.base_url
                else:
                    page_url = f"{self.base_url}page/{page_num}/"
                
                response = self.session.get(page_url, timeout=10)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                quotes = soup.select('.quote')
                
                if not quotes:
                    break
                
                for quote in quotes:
                    text_tag = quote.select_one('.text')
                    text = text_tag.get_text(strip=True) if text_tag else 'N/A'
                    
                    author_tag = quote.select_one('.author')
                    author = author_tag.get_text(strip=True) if author_tag else 'Unknown'
                    
                    tags = [tag.get_text(strip=True) for tag in quote.select('.tag')]
                    
                    self.data.append({
                        'text': text,
                        'author': author,
                        'tags': tags,
                        'source': 'quotes.toscrape.com'
                    })
                
                time.sleep(0.5)
            
            self.metrics['success'] = True
            
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            self.metrics['success'] = False
        
        finally:
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration'] = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            self.metrics['records_extracted'] = len(self.data)
        
        print(f"  ✓ {len(self.data)} citations extraites en {self.metrics['duration']:.2f}s")
        return self.data
    
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalisation schéma unifié"""
        normalized = []
        for item in raw_data:
            normalized.append({
                'type': 'quote',
                'title': item['text'][:50] + '...' if len(item['text']) > 50 else item['text'],
                'value': 0,  # Pas de valeur monétaire
                'rating': 5,  # Rating par défaut pour citations
                'source': item['source'],
                'metadata': {
                    'author': item['author'],
                    'tags': item['tags']
                }
            })
        
        return normalized


class JobsScraperPlugin(ScraperPlugin):
    """Plugin scraping fake-jobs"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config.get('url', 'https://realpython.github.io/fake-jobs/')
        self.max_jobs = config.get('max_jobs', 20)
    
    def scrape(self) -> List[Dict]:
        """Scraping offres emploi"""
        print(f"  [{self.get_source_name()}] Scraping (limite: {self.max_jobs} offres)...")
        
        self.metrics['start_time'] = datetime.now()
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                self.metrics['success'] = False
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.select('.card')[:self.max_jobs]
            
            for card in job_cards:
                title_tag = card.select_one('h2.title')
                title = title_tag.get_text(strip=True) if title_tag else 'N/A'
                
                company_tag = card.select_one('h3.company')
                company = company_tag.get_text(strip=True) if company_tag else 'N/A'
                
                location_tag = card.select_one('.location')
                location = location_tag.get_text(strip=True) if location_tag else 'N/A'
                
                self.data.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'source': 'fake-jobs'
                })
            
            self.metrics['success'] = True
            
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            self.metrics['success'] = False
        
        finally:
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration'] = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            self.metrics['records_extracted'] = len(self.data)
        
        print(f"  ✓ {len(self.data)} offres extraites en {self.metrics['duration']:.2f}s")
        return self.data
    
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Normalisation schéma unifié"""
        normalized = []
        for item in raw_data:
            normalized.append({
                'type': 'job',
                'title': item['title'],
                'value': 0,  # Pas de valeur monétaire
                'rating': 0,  # Pas de rating
                'source': item['source'],
                'metadata': {
                    'company': item['company'],
                    'location': item['location']
                }
            })
        
        return normalized


class MultiSourceScraper:
    """Orchestrateur scraping multi-sources"""
    
    def __init__(self, config_file: str = None):
        """Initialisation avec configuration externe"""
        self.config_file = config_file or self._create_default_config()
        self.config = self._load_config()
        
        self.plugins: List[ScraperPlugin] = []
        self.all_data = []
        self.normalized_data = []
        
        self.output_dir = Path('./outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_default_config(self) -> Path:
        """Création configuration par défaut"""
        config_file = Path('./scraping_data/scraper_config.yaml')
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            'sources': {
                'books': {
                    'enabled': True,
                    'plugin': 'BooksScraperPlugin',
                    'url': 'https://books.toscrape.com/',
                    'max_pages': 2
                },
                'quotes': {
                    'enabled': True,
                    'plugin': 'QuotesScraperPlugin',
                    'url': 'http://quotes.toscrape.com/',
                    'max_pages': 1
                },
                'jobs': {
                    'enabled': True,
                    'plugin': 'JobsScraperPlugin',
                    'url': 'https://realpython.github.io/fake-jobs/',
                    'max_jobs': 20
                }
            },
            'parallel_processing': {
                'enabled': True,
                'max_workers': 3
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        print(f"✓ Configuration par défaut créée: {config_file}")
        return config_file
    
    def _load_config(self) -> Dict:
        """Chargement configuration YAML"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"✗ Erreur chargement config: {e}")
            return {}
    
    def _instantiate_plugin(self, plugin_name: str, config: Dict) -> ScraperPlugin:
        """Instanciation dynamique plugin"""
        plugin_classes = {
            'BooksScraperPlugin': BooksScraperPlugin,
            'QuotesScraperPlugin': QuotesScraperPlugin,
            'JobsScraperPlugin': JobsScraperPlugin
        }
        
        plugin_class = plugin_classes.get(plugin_name)
        if plugin_class:
            return plugin_class(config)
        
        raise ValueError(f"Plugin inconnu: {plugin_name}")
    
    def load_plugins(self):
        """Chargement plugins depuis configuration"""
        print("Chargement plugins...\n")
        
        sources = self.config.get('sources', {})
        
        for source_name, source_config in sources.items():
            if not source_config.get('enabled', False):
                print(f"  ⊗ {source_name}: désactivé")
                continue
            
            plugin_name = source_config.get('plugin')
            
            try:
                plugin = self._instantiate_plugin(plugin_name, source_config)
                self.plugins.append(plugin)
                print(f"  ✓ {source_name}: {plugin_name} chargé")
            except Exception as e:
                print(f"  ✗ {source_name}: Erreur chargement - {e}")
        
        print(f"\n{len(self.plugins)} plugins actifs")
    
    def scrape_all_sequential(self):
        """Scraping séquentiel toutes sources"""
        print("\n" + "=" * 70)
        print("SCRAPING SÉQUENTIEL")
        print("=" * 70 + "\n")
        
        for plugin in self.plugins:
            raw_data = plugin.scrape()
            normalized = plugin.normalize_data(raw_data)
            self.all_data.extend(raw_data)
            self.normalized_data.extend(normalized)
    
    def scrape_all_parallel(self):
        """Scraping parallèle toutes sources (ThreadPoolExecutor)"""
        print("\n" + "=" * 70)
        print("SCRAPING PARALLÈLE")
        print("=" * 70 + "\n")
        
        parallel_config = self.config.get('parallel_processing', {})
        max_workers = parallel_config.get('max_workers', 3)
        
        print(f"Utilisation {max_workers} workers parallèles\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumission tâches
            futures = {
                executor.submit(plugin.scrape): plugin
                for plugin in self.plugins
            }
            
            # Récupération résultats
            for future in as_completed(futures):
                plugin = futures[future]
                try:
                    raw_data = future.result()
                    normalized = plugin.normalize_data(raw_data)
                    self.all_data.extend(raw_data)
                    self.normalized_data.extend(normalized)
                except Exception as e:
                    print(f"  ✗ Erreur plugin {plugin.get_source_name()}: {e}")
    
    def aggregate_data(self):
        """Agrégation intelligente données multi-sources"""
        print("\n" + "=" * 70)
        print("AGRÉGATION DONNÉES")
        print("=" * 70)
        
        # Statistiques par type
        type_counts = {}
        for item in self.normalized_data:
            item_type = item['type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        print("\nDistribution par type:")
        for item_type, count in type_counts.items():
            print(f"  {item_type}: {count} records")
        
        # Statistiques par source
        source_counts = {}
        for item in self.normalized_data:
            source = item['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("\nDistribution par source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} records")
    
    def generate_performance_metrics(self) -> Dict:
        """Génération métriques performances comparatives"""
        print("\n" + "=" * 70)
        print("MÉTRIQUES PERFORMANCE")
        print("=" * 70)
        
        metrics_by_plugin = {}
        
        for plugin in self.plugins:
            plugin_name = plugin.get_source_name()
            metrics = plugin.metrics
            
            speed = (metrics['records_extracted'] / metrics['duration']) if metrics['duration'] > 0 else 0
            
            metrics_by_plugin[plugin_name] = {
                'duration_seconds': round(metrics['duration'], 2),
                'records_extracted': metrics['records_extracted'],
                'speed_records_per_sec': round(speed, 2),
                'success': metrics['success']
            }
            
            print(f"\n{plugin_name}:")
            print(f"  Durée: {metrics['duration']:.2f}s")
            print(f"  Records: {metrics['records_extracted']}")
            print(f"  Vitesse: {speed:.2f} records/sec")
            print(f"  Statut: {'✓ Succès' if metrics['success'] else '✗ Échec'}")
        
        return metrics_by_plugin
    
    def export_data(self):
        """Export données agrégées"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export JSON unifié
        data_file = self.output_dir / f'multi_source_data_{timestamp}.json'
        
        export_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_records': len(self.normalized_data),
                'sources_count': len(self.plugins)
            },
            'normalized_data': self.normalized_data
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Données exportées: {data_file}")
    
    def export_metrics(self, metrics: Dict):
        """Export métriques performance"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.output_dir / f'performance_metrics_{timestamp}.json'
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Métriques exportées: {metrics_file}")


def main():
    print("=" * 70)
    print("EXERCICE 8: Scraping multi-sources")
    print("=" * 70)
    
    # Orchestrateur avec configuration par défaut
    scraper = MultiSourceScraper()
    
    # Chargement plugins
    scraper.load_plugins()
    
    # Scraping parallèle (ou séquentiel si désiré)
    parallel_enabled = scraper.config.get('parallel_processing', {}).get('enabled', True)
    
    if parallel_enabled:
        scraper.scrape_all_parallel()
    else:
        scraper.scrape_all_sequential()
    
    # Agrégation
    scraper.aggregate_data()
    
    # Métriques
    metrics = scraper.generate_performance_metrics()
    
    # Exports
    scraper.export_data()
    scraper.export_metrics(metrics)
    
    print("\n" + "=" * 70)
    print("✓ Exercice 8 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

