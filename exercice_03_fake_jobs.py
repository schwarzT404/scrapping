"""
Exercice 3: Fake Jobs - Filtres avancés
Filtrage dynamique, détection doublons, statistiques
"""

import requests
from bs4 import BeautifulSoup
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin
import argparse
import re


class FakeJobsScraper:
    """Scraper offres d'emploi avec filtres avancés"""
    
    def __init__(self, 
                 base_url="https://realpython.github.io/fake-jobs/",
                 keyword_filter="Python",
                 location_filter=None,
                 max_jobs=100):
        """
        Initialisation scraper avec filtres
        
        Args:
            base_url: URL de base
            keyword_filter: Mot-clé à filtrer (défaut: "Python")
            location_filter: Filtre localisation optionnel
            max_jobs: Limite nombre d'offres (défaut: 100)
        """
        self.base_url = base_url
        self.keyword_filter = keyword_filter
        self.location_filter = location_filter
        self.max_jobs = max_jobs
        
        self.session = requests.Session()
        self.jobs = []
        self.seen_hashes: Set[str] = set()
        
        # Statistiques
        self.stats = {
            'total_scraped': 0,
            'filtered_keyword': 0,
            'duplicates_removed': 0,
            'by_contract_type': {},
            'by_location': {}
        }
    
    def _compute_job_hash(self, job: Dict) -> str:
        """Calcul hash unique pour détection doublons"""
        # Combinaison titre + entreprise + localisation
        unique_str = f"{job['title']}|{job['company']}|{job['location']}"
        return hashlib.sha256(unique_str.encode()).hexdigest()
    
    def _is_duplicate(self, job: Dict) -> bool:
        """Vérification si offre est un doublon"""
        job_hash = self._compute_job_hash(job)
        
        if job_hash in self.seen_hashes:
            self.stats['duplicates_removed'] += 1
            return True
        
        self.seen_hashes.add(job_hash)
        return False
    
    def _standardize_date(self, date_str: str) -> str:
        """Standardisation format date"""
        if not date_str or date_str.strip() == '':
            return 'N/A'
        
        # Nettoyage
        date_str = date_str.strip()
        
        # Patterns courants
        patterns = [
            (r'(\d{4})-(\d{2})-(\d{2})', r'\1-\2-\3'),  # YYYY-MM-DD
            (r'(\d{2})/(\d{2})/(\d{4})', r'\3-\1-\2'),  # MM/DD/YYYY → YYYY-MM-DD
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})', 'text_date'),  # 15 January 2024
        ]
        
        for pattern, replacement in patterns:
            if replacement == 'text_date':
                # Conversion date textuelle
                months = {
                    'january': '01', 'february': '02', 'march': '03', 'april': '04',
                    'may': '05', 'june': '06', 'july': '07', 'august': '08',
                    'september': '09', 'october': '10', 'november': '11', 'december': '12',
                    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                    'oct': '10', 'nov': '11', 'dec': '12'
                }
                
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day, month, year = match.groups()
                    month_num = months.get(month.lower(), '01')
                    return f"{year}-{month_num}-{day.zfill(2)}"
            else:
                match = re.search(pattern, date_str)
                if match:
                    return re.sub(pattern, replacement, date_str)
        
        return date_str
    
    def _classify_contract_type(self, description: str) -> str:
        """Classification type de contrat depuis description"""
        description_lower = description.lower()
        
        if 'full-time' in description_lower or 'full time' in description_lower:
            return 'Full-time'
        elif 'part-time' in description_lower or 'part time' in description_lower:
            return 'Part-time'
        elif 'contract' in description_lower:
            return 'Contract'
        elif 'freelance' in description_lower:
            return 'Freelance'
        elif 'internship' in description_lower or 'intern' in description_lower:
            return 'Internship'
        else:
            return 'Not specified'
    
    def _validate_url(self, url: str) -> bool:
        """Validation basique URL"""
        if not url or url == 'N/A':
            return False
        
        # Vérification pattern URL
        url_pattern = re.compile(
            r'^https?://'  # http:// ou https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domaine
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # port optionnel
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def _matches_keyword_filter(self, job: Dict) -> bool:
        """Vérification si offre correspond au filtre mot-clé"""
        if not self.keyword_filter:
            return True
        
        keyword_lower = self.keyword_filter.lower()
        
        # Recherche dans titre, description, entreprise
        searchable_text = f"{job['title']} {job['description']} {job['company']}".lower()
        
        return keyword_lower in searchable_text
    
    def _matches_location_filter(self, job: Dict) -> bool:
        """Vérification si offre correspond au filtre localisation"""
        if not self.location_filter:
            return True
        
        location_lower = self.location_filter.lower()
        job_location_lower = job['location'].lower()
        
        return location_lower in job_location_lower
    
    def scrape_jobs(self):
        """Extraction offres d'emploi avec filtres"""
        print(f"Scraping offres d'emploi...")
        print(f"  Filtre mot-clé: {self.keyword_filter or 'Aucun'}")
        print(f"  Filtre localisation: {self.location_filter or 'Aucun'}")
        print(f"  Limite: {self.max_jobs} offres\n")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            
            if response.status_code != 200:
                print(f"✗ Erreur: Status {response.status_code}")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction offres
            job_cards = soup.select('.card')
            
            for card in job_cards:
                if len(self.jobs) >= self.max_jobs:
                    print(f"Limite de {self.max_jobs} offres atteinte")
                    break
                
                # Extraction données
                title_tag = card.select_one('h2.title')
                title = title_tag.get_text(strip=True) if title_tag else 'N/A'
                
                company_tag = card.select_one('h3.company')
                company = company_tag.get_text(strip=True) if company_tag else 'N/A'
                
                location_tag = card.select_one('.location')
                location = location_tag.get_text(strip=True) if location_tag else 'N/A'
                
                date_tag = card.select_one('time')
                date_posted = date_tag.get_text(strip=True) if date_tag else 'N/A'
                date_posted = self._standardize_date(date_posted)
                
                description_tag = card.select_one('.description')
                description = description_tag.get_text(strip=True) if description_tag else 'N/A'
                
                apply_link_tag = card.select_one('a[href]')
                apply_url = apply_link_tag['href'] if apply_link_tag else 'N/A'
                apply_url = urljoin(self.base_url, apply_url)
                
                # Classification type contrat
                contract_type = self._classify_contract_type(description)
                
                # Validation URL
                url_valid = self._validate_url(apply_url)
                
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'date_posted': date_posted,
                    'description': description,
                    'contract_type': contract_type,
                    'apply_url': apply_url,
                    'url_valid': url_valid
                }
                
                self.stats['total_scraped'] += 1
                
                # Application filtres
                if not self._matches_keyword_filter(job_data):
                    continue
                
                if not self._matches_location_filter(job_data):
                    continue
                
                self.stats['filtered_keyword'] += 1
                
                # Vérification doublons
                if self._is_duplicate(job_data):
                    continue
                
                # Ajout offre
                self.jobs.append(job_data)
                
                # Statistiques
                self.stats['by_contract_type'][contract_type] = \
                    self.stats['by_contract_type'].get(contract_type, 0) + 1
                
                self.stats['by_location'][location] = \
                    self.stats['by_location'].get(location, 0) + 1
            
            print(f"✓ Extraction terminée:")
            print(f"  - {self.stats['total_scraped']} offres scrapées")
            print(f"  - {self.stats['filtered_keyword']} après filtre mot-clé")
            print(f"  - {self.stats['duplicates_removed']} doublons supprimés")
            print(f"  - {len(self.jobs)} offres finales")
            
        except Exception as e:
            print(f"✗ Erreur scraping: {e}")
    
    def generate_statistics(self):
        """Génération statistiques détaillées"""
        print("\n" + "=" * 70)
        print("STATISTIQUES")
        print("=" * 70)
        
        # Par type de contrat
        print("\n📊 Distribution par type de contrat:")
        for contract, count in sorted(self.stats['by_contract_type'].items(), 
                                      key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.jobs) * 100) if self.jobs else 0
            print(f"  {contract}: {count} ({percentage:.1f}%)")
        
        # Par localisation
        print("\n📍 Top 10 localisations:")
        sorted_locations = sorted(self.stats['by_location'].items(), 
                                 key=lambda x: x[1], reverse=True)[:10]
        
        for location, count in sorted_locations:
            percentage = (count / len(self.jobs) * 100) if self.jobs else 0
            print(f"  {location}: {count} ({percentage:.1f}%)")
        
        # URLs valides
        valid_urls = sum(1 for job in self.jobs if job['url_valid'])
        print(f"\n🔗 URLs valides: {valid_urls}/{len(self.jobs)}")
    
    def export_csv(self):
        """Export CSV UTF-8"""
        output_dir = Path('./outputs')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = output_dir / f'fake_jobs_{timestamp}.csv'
        
        if not self.jobs:
            print("\n✗ Aucune offre à exporter")
            return
        
        # En-têtes
        fieldnames = [
            'title', 'company', 'location', 'date_posted', 
            'contract_type', 'description', 'apply_url', 'url_valid'
        ]
        
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.jobs)
        
        print(f"\n✓ CSV exporté: {csv_file}")


def main():
    print("=" * 70)
    print("EXERCICE 3: Fake Jobs - Filtres avancés")
    print("=" * 70)
    
    # Parse arguments CLI
    parser = argparse.ArgumentParser(description='Scraper offres emploi avec filtres')
    parser.add_argument('--keyword', default='Python', help='Mot-clé à filtrer')
    parser.add_argument('--location', default=None, help='Filtre localisation')
    parser.add_argument('--max', type=int, default=100, help='Limite nombre offres')
    
    args = parser.parse_args()
    
    # Scraper avec filtres (limite par défaut: 100 offres)
    scraper = FakeJobsScraper(
        keyword_filter=args.keyword,
        location_filter=args.location,
        max_jobs=args.max
    )
    
    # Scraping
    scraper.scrape_jobs()
    
    # Statistiques
    scraper.generate_statistics()
    
    # Export CSV
    scraper.export_csv()
    
    print("\n" + "=" * 70)
    print("✓ Exercice 3 terminé avec succès")
    print("=" * 70)


if __name__ == "__main__":
    main()

