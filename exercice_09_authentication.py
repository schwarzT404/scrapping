"""
Exercice 9: Authentification et sessions
Gestion complète authentification, sessions, contenu protégé
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time
from typing import Optional, Dict
import os
from pathlib import Path


class AuthenticatedScraper:
    """Scraper avec gestion authentification complète"""
    
    def __init__(self, base_url="http://quotes.toscrape.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False
        self.auth_token = None
        
        # Chemins cross-platform
        self.data_dir = Path('./scraping_data')
        self.output_dir = Path('./outputs')
        self._ensure_directories()
        
        self.credentials = self._load_credentials()
    
    def _ensure_directories(self):
        """Création répertoires nécessaires"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_credentials(self) -> Dict[str, str]:
        """Chargement sécurisé credentials"""
        # Configuration par défaut pour quotes.toscrape
        credentials_file = self.data_dir / 'credentials.json'
        
        default_credentials = {
            'username': 'admin',  # Credentials test site
            'password': 'admin'
        }
        
        try:
            if credentials_file.exists():
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            else:
                # Création fichier credentials
                with open(credentials_file, 'w') as f:
                    json.dump(default_credentials, f, indent=2)
                # Permissions lecture seule propriétaire (Unix uniquement)
                try:
                    os.chmod(credentials_file, 0o600)
                except (OSError, AttributeError):
                    pass  # Windows ou permissions non supportées
                return default_credentials
        except Exception as e:
            print(f"Erreur chargement credentials: {e}")
            return default_credentials
    
    def _extract_csrf_token(self, soup: BeautifulSoup) -> Optional[str]:
        """Extraction CSRF token depuis formulaire"""
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            return csrf_input.get('value')
        return None
    
    def login(self) -> bool:
        """Authentification et initialisation session"""
        login_url = urljoin(self.base_url, '/login')
        
        try:
            # 1. Récupération formulaire login
            print(f"Accès page login: {login_url}")
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code != 200:
                print(f"✗ Erreur accès login: {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 2. Extraction CSRF token si présent
            csrf_token = self._extract_csrf_token(soup)
            
            # 3. Préparation données login
            login_data = {
                'username': self.credentials['username'],
                'password': self.credentials['password']
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
                print(f"CSRF token détecté: {csrf_token[:20]}...")
            
            # 4. Soumission formulaire
            print(f"Tentative authentification: {self.credentials['username']}")
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            # 5. Vérification succès authentification
            if response.status_code == 200:
                # Détection indicateurs authentification réussie
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Recherche éléments post-login
                logout_link = soup.find('a', href='/logout')
                welcome_message = soup.find(string=lambda t: 'logout' in str(t).lower())
                
                if logout_link or welcome_message:
                    self.authenticated = True
                    print("✓ Authentification réussie")
                    
                    # Sauvegarde cookies session
                    self._store_session_cookies()
                    
                    return True
                else:
                    print("✗ Authentification échouée (pas d'indicateur logout)")
                    return False
            else:
                print(f"✗ Authentification échouée: {response.status_code}")
                return False
            
        except Exception as e:
            print(f"✗ Erreur authentification: {e}")
            return False
    
    def _store_session_cookies(self):
        """Sauvegarde cookies session"""
        cookies_file = self.data_dir / 'session_cookies.json'
        
        cookies_dict = {
            cookie.name: cookie.value 
            for cookie in self.session.cookies
        }
        
        try:
            with open(cookies_file, 'w') as f:
                json.dump(cookies_dict, f, indent=2)
            print(f"Cookies session sauvegardés: {len(cookies_dict)} cookies")
        except Exception as e:
            print(f"Erreur sauvegarde cookies: {e}")
    
    def _load_session_cookies(self) -> bool:
        """Chargement cookies session précédente"""
        cookies_file = self.data_dir / 'session_cookies.json'
        
        try:
            if cookies_file.exists():
                with open(cookies_file, 'r') as f:
                    cookies_dict = json.load(f)
                
                for name, value in cookies_dict.items():
                    self.session.cookies.set(name, value)
                
                print(f"✓ Cookies session restaurés: {len(cookies_dict)} cookies")
                return True
        except Exception as e:
            print(f"Erreur chargement cookies: {e}")
        
        return False
    
    def check_session_validity(self) -> bool:
        """Vérification validité session active"""
        try:
            # Tentative accès page protégée
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Détection si toujours authentifié
            logout_link = soup.find('a', href='/logout')
            
            if logout_link:
                self.authenticated = True
                print("✓ Session valide")
                return True
            else:
                self.authenticated = False
                print("✗ Session expirée")
                return False
                
        except Exception as e:
            print(f"Erreur vérification session: {e}")
            return False
    
    def refresh_session(self):
        """Refresh automatique session si expirée"""
        if not self.check_session_validity():
            print("Session expirée - Réauthentification...")
            return self.login()
        return True
    
    def scrape_protected_content(self):
        """Accès contenu protégé nécessitant authentification"""
        if not self.authenticated:
            print("Non authentifié - Tentative login...")
            if not self.login():
                print("Impossible d'accéder au contenu protégé")
                return []
        
        # Refresh session si nécessaire
        self.refresh_session()
        
        protected_data = []
        
        try:
            # Accès pages nécessitant authentification
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction contenu
            quotes = soup.select('.quote')
            
            for quote in quotes:
                text = quote.select_one('.text').get_text(strip=True)
                author = quote.select_one('.author').get_text(strip=True)
                
                protected_data.append({
                    'text': text,
                    'author': author,
                    'session_authenticated': True
                })
            
            print(f"✓ Contenu protégé extrait: {len(protected_data)} éléments")
            
        except Exception as e:
            print(f"✗ Erreur extraction contenu protégé: {e}")
        
        return protected_data
    
    def logout(self) -> bool:
        """Déconnexion et nettoyage session"""
        logout_url = urljoin(self.base_url, '/logout')
        
        try:
            response = self.session.get(logout_url, timeout=10)
            
            if response.status_code == 200:
                self.authenticated = False
                self.session.cookies.clear()
                
                # Suppression cookies sauvegardés
                cookies_file = self.data_dir / 'session_cookies.json'
                if cookies_file.exists():
                    cookies_file.unlink()
                
                print("✓ Déconnexion réussie")
                return True
            else:
                print(f"✗ Erreur déconnexion: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Erreur logout: {e}")
            return False
    
    def session_lifecycle_demo(self):
        """Démonstration cycle complet session"""
        print("\n=== Démonstration cycle vie session ===\n")
        
        # 1. Login initial
        print("1. Authentification initiale")
        if self.login():
            
            # 2. Scraping contenu protégé
            print("\n2. Accès contenu protégé")
            data = self.scrape_protected_content()
            
            # 3. Sauvegarde session
            print("\n3. Sauvegarde état session")
            self._store_session_cookies()
            
            # 4. Simulation expiration
            print("\n4. Simulation vérification session")
            time.sleep(2)
            self.check_session_validity()
            
            # 5. Refresh session
            print("\n5. Refresh automatique session")
            self.refresh_session()
            
            # 6. Export données
            print("\n6. Export données")
            self._export_data(data)
            
            # 7. Logout propre
            print("\n7. Déconnexion")
            self.logout()
            
        else:
            print("Échec authentification - Arrêt démonstration")
    
    def _export_data(self, data):
        """Export données scrapées"""
        output_file = self.output_dir / 'authenticated_scraping_data.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Données exportées: {output_file}")


class SessionManager:
    """Gestionnaire avancé sessions multiples"""
    
    def __init__(self):
        self.active_sessions = {}
        
    def create_session(self, session_id: str, base_url: str):
        """Création session authentifiée"""
        scraper = AuthenticatedScraper(base_url)
        if scraper.login():
            self.active_sessions[session_id] = scraper
            print(f"Session créée: {session_id}")
            return scraper
        return None
    
    def get_session(self, session_id: str) -> Optional[AuthenticatedScraper]:
        """Récupération session active"""
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Fermeture session"""
        if session_id in self.active_sessions:
            scraper = self.active_sessions[session_id]
            scraper.logout()
            del self.active_sessions[session_id]
            print(f"Session fermée: {session_id}")
    
    def close_all_sessions(self):
        """Fermeture toutes sessions"""
        for session_id in list(self.active_sessions.keys()):
            self.close_session(session_id)


def main():
    print("=== Exercice 9: Authentification et Sessions ===\n")
    
    # Test scraper authentifié
    scraper = AuthenticatedScraper()
    scraper.session_lifecycle_demo()
    
    # Test gestionnaire sessions
    print("\n\n=== Test gestionnaire sessions multiples ===")
    manager = SessionManager()
    
    # Création sessions multiples
    session1 = manager.create_session('session_1', 'http://quotes.toscrape.com')
    
    if session1:
        data = session1.scrape_protected_content()
        print(f"Session 1 - Données extraites: {len(data)}")
    
    # Fermeture toutes sessions
    manager.close_all_sessions()
    
    print("\n=== Démonstration terminée ===")


if __name__ == "__main__":
    main()
