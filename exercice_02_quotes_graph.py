"""
Exercice 2: Quotes to Scrape - Graphe de données
Construction graphe relationnel avec cache et export GraphML
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin
from pathlib import Path
from typing import Dict, List, Set
import hashlib


class QuotesGraphScraper:
    """Extracteur citations avec graphe relationnel et système cache"""
    
    def __init__(self, base_url="http://quotes.toscrape.com", max_pages=2):
        """
        Initialisation scraper avec limite par défaut
        
        Args:
            base_url: URL de base du site
            max_pages: Limite nombre de pages à scraper (défaut: 2)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        
        self.quotes = []
        self.authors = {}
        self.tags = set()
        
        self.cache_dir = Path('./outputs/exercice_02/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.author_cache = {}
        
        self.graph = {
            'nodes': [],
            'edges': []
        }
        
        self.stats = {
            'total_quotes': 0,
            'total_authors': 0,
            'total_tags': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _respectful_delay(self):
        """Délai aléatoire entre requêtes"""
        time.sleep(random.uniform(0.5, 1.5))
    
    def _get_cache_key(self, author_name: str) -> str:
        """Génération clé cache pour auteur"""
        return hashlib.md5(author_name.encode()).hexdigest()
    
    def _load_author_from_cache(self, author_name: str) -> Dict:
        """Chargement données auteur depuis cache"""
        cache_key = self._get_cache_key(author_name)
        cache_file = self.cache_dir / f'author_{cache_key}.json'
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.stats['cache_hits'] += 1
                return json.load(f)
        return None
    
    def _save_author_to_cache(self, author_name: str, author_data: Dict):
        """Sauvegarde données auteur dans cache"""
        cache_key = self._get_cache_key(author_name)
        cache_file = self.cache_dir / f'author_{cache_key}.json'
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(author_data, f, ensure_ascii=False, indent=2)
    
    def _scrape_author_details(self, author_url: str, author_name: str) -> Dict:
        """Extraction détails auteur depuis page biographie"""
        cached_author = self._load_author_from_cache(author_name)
        if cached_author:
            print(f"  ↳ Cache HIT: {author_name}")
            return cached_author
        
        print(f"  ↳ Cache MISS: Scraping {author_name}")
        self.stats['cache_misses'] += 1
        
        try:
            full_url = urljoin(self.base_url, author_url)
            response = self.session.get(full_url, timeout=10)
            
            if response.status_code != 200:
                return self._get_default_author_data(author_name)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            bio_tag = soup.select_one('.author-description')
            bio = bio_tag.get_text(strip=True) if bio_tag else 'N/A'
            
            born_date_tag = soup.select_one('.author-born-date')
            born_date = born_date_tag.get_text(strip=True) if born_date_tag else 'N/A'
            
            born_location_tag = soup.select_one('.author-born-location')
            born_location = born_location_tag.get_text(strip=True) if born_location_tag else 'N/A'
            
            author_data = {
                'name': author_name,
                'biography': bio,
                'born_date': born_date,
                'born_location': born_location,
                'death_date': 'N/A',  # Pas toujours disponible
                'url': full_url
            }
            
            self._save_author_to_cache(author_name, author_data)
            
            self._respectful_delay()
            return author_data
            
        except Exception as e:
            print(f"  ✗ Erreur scraping auteur {author_name}: {e}")
            return self._get_default_author_data(author_name)
    
    def _get_default_author_data(self, author_name: str) -> Dict:
        """Données auteur par défaut en cas d'erreur"""
        return {
            'name': author_name,
            'biography': 'N/A',
            'born_date': 'N/A',
            'born_location': 'N/A',
            'death_date': 'N/A',
            'url': 'N/A'
        }
    
    def _scrape_page(self, page_url: str) -> List[Dict]:
        """Extraction citations depuis page"""
        try:
            response = self.session.get(page_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            quote_blocks = soup.select('.quote')
            
            page_quotes = []
            
            for block in quote_blocks:
                text_tag = block.select_one('.text')
                text = text_tag.get_text(strip=True) if text_tag else 'N/A'
                
                author_tag = block.select_one('.author')
                author_name = author_tag.get_text(strip=True) if author_tag else 'Unknown'
                
                author_link_tag = block.select_one('a[href*="/author/"]')
                author_url = author_link_tag['href'] if author_link_tag else None
                
                tag_elements = block.select('.tag')
                quote_tags = [tag.get_text(strip=True) for tag in tag_elements]
                
                if author_name not in self.authors:
                    if author_url:
                        author_data = self._scrape_author_details(author_url, author_name)
                        self.authors[author_name] = author_data
                    else:
                        self.authors[author_name] = self._get_default_author_data(author_name)
                
                self.tags.update(quote_tags)
                
                quote_data = {
                    'text': text,
                    'author': author_name,
                    'tags': quote_tags
                }
                
                page_quotes.append(quote_data)
            
            return page_quotes
            
        except Exception as e:
            print(f"✗ Erreur scraping page {page_url}: {e}")
            return []
    
    def scrape_all_pages(self):
        """Pagination automatique avec limite"""
        page_num = 1
        
        print(f"Début scraping (limite: {self.max_pages} pages)...\n")
        
        while page_num <= self.max_pages:
            if page_num == 1:
                page_url = self.base_url
            else:
                page_url = urljoin(self.base_url, f'page/{page_num}/')
            
            print(f"Page {page_num}/{self.max_pages}...")
            quotes = self._scrape_page(page_url)
            
            if not quotes:
                print(f"Aucune citation page {page_num} - Arrêt")
                break
            
            self.quotes.extend(quotes)
            page_num += 1
            
            if page_num <= self.max_pages:
                self._respectful_delay()
        
        self.stats['total_quotes'] = len(self.quotes)
        self.stats['total_authors'] = len(self.authors)
        self.stats['total_tags'] = len(self.tags)
        
        print(f"\n✓ Extraction terminée:")
        print(f"  - {self.stats['total_quotes']} citations")
        print(f"  - {self.stats['total_authors']} auteurs")
        print(f"  - {self.stats['total_tags']} tags uniques")
        print(f"  - Cache: {self.stats['cache_hits']} hits / {self.stats['cache_misses']} misses")
    
    def build_graph(self):
        """Construction graphe relationnel Citation → Auteur → Tags"""
        print("\nConstruction graphe relationnel...")
        
        for author_name, author_data in self.authors.items():
            self.graph['nodes'].append({
                'id': f"author_{author_name}",
                'type': 'author',
                'label': author_name,
                'data': author_data
            })
        
        for tag in self.tags:
            self.graph['nodes'].append({
                'id': f"tag_{tag}",
                'type': 'tag',
                'label': tag
            })
        
        for idx, quote in enumerate(self.quotes):
            quote_id = f"quote_{idx}"
            
            self.graph['nodes'].append({
                'id': quote_id,
                'type': 'quote',
                'label': quote['text'][:50] + '...',
                'text': quote['text']
            })
            
            self.graph['edges'].append({
                'source': quote_id,
                'target': f"author_{quote['author']}",
                'type': 'authored_by'
            })
            
            for tag in quote['tags']:
                self.graph['edges'].append({
                    'source': quote_id,
                    'target': f"tag_{tag}",
                    'type': 'tagged_with'
                })
        
        print(f"✓ Graphe construit: {len(self.graph['nodes'])} nœuds, {len(self.graph['edges'])} arêtes")
    
    def detect_most_cited_authors(self) -> List[Dict]:
        """Détection auteurs les plus cités"""
        author_counts = {}
        
        for quote in self.quotes:
            author = quote['author']
            author_counts[author] = author_counts.get(author, 0) + 1
        
        sorted_authors = sorted(
            author_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        print("\n🏆 Top auteurs les plus cités:")
        for author, count in sorted_authors[:5]:
            print(f"  {author}: {count} citations")
        
        return sorted_authors
    
    def export_graphml(self):
        """Export graphe au format GraphML (importable Gephi/NetworkX)"""
        output_dir = Path('./outputs/exercice_02')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        graphml_file = output_dir / 'quotes_graph.graphml'
        
        graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
        graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        graphml.append('  <key id="type" for="node" attr.name="type" attr.type="string"/>')
        graphml.append('  <key id="label" for="node" attr.name="label" attr.type="string"/>')
        graphml.append('  <graph id="G" edgedefault="directed">')
        
        for node in self.graph['nodes']:
            graphml.append(f'    <node id="{node["id"]}">')
            graphml.append(f'      <data key="type">{node["type"]}</data>')
            graphml.append(f'      <data key="label">{self._escape_xml(node["label"])}</data>')
            graphml.append('    </node>')
        
        for idx, edge in enumerate(self.graph['edges']):
            graphml.append(f'    <edge id="e{idx}" source="{edge["source"]}" target="{edge["target"]}"/>')
        
        graphml.append('  </graph>')
        graphml.append('</graphml>')
        
        with open(graphml_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(graphml))
        
        print(f"\n✓ GraphML exporté: {graphml_file}")
    
    def _escape_xml(self, text: str) -> str:
        """Échappement caractères XML"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    def export_json(self):
        """Export JSON complet avec métadonnées"""
        output_dir = Path('./outputs/exercice_02')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = output_dir / f'quotes_data_{timestamp}.json'
        
        output_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'source': self.base_url,
                'pages_scraped': self.max_pages,
                'statistics': self.stats
            },
            'quotes': self.quotes,
            'authors': self.authors,
            'tags': list(self.tags),
            'graph': self.graph
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ JSON exporté: {json_file}")


def main():
    print("=" * 70)
    print("EXERCICE 2: Quotes to Scrape - Graphe de données")
    print("=" * 70)
    
    scraper = QuotesGraphScraper(max_pages=2)
    scraper.scrape_all_pages()
    scraper.build_graph()
    scraper.detect_most_cited_authors()
    scraper.export_graphml()
    scraper.export_json()
    
    print("\n" + "=" * 70)
    print("✓ Exercice 2 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

