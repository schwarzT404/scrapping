"""
Script principal exécution exercices web scraping
Menu interactif pour sélection et exécution exercices
"""

import subprocess
import sys


def print_menu():
    """Affichage menu principal"""
    menu = """
╔═══════════════════════════════════════════════════════════════╗
║          EXERCICES WEB SCRAPING - MENU PRINCIPAL              ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. Books to Scrape - Extraction complète                    ║
║     └─ Pagination automatique, JSON hiérarchique             ║
║                                                               ║
║  2. Quotes to Scrape - Graphe de données                     ║
║     └─ Relations entités, cache, export GraphML              ║
║                                                               ║
║  3. Fake Jobs - Filtres avancés                              ║
║     └─ Détection doublons, statistiques, CSV                 ║
║                                                               ║
║  4. Analyse marché livresque                                 ║
║     └─ Statistiques, visualisations, corrélations            ║
║                                                               ║
║  5. Navigation catégorielle avancée                          ║
║     └─ Arborescence, classements, recherche full-text        ║
║                                                               ║
║  6. Scraper résilient                                        ║
║     └─ Retry intelligent, logging, reprise interruption      ║
║                                                               ║
║  7. Pipeline data cleaning                                   ║
║     └─ Standardisation, validation, métriques qualité        ║
║                                                               ║
║  8. Scraping multi-sources                                   ║
║     └─ Architecture modulaire, parallel processing           ║
║                                                               ║
║  9. Authentification et sessions                             ║
║     └─ Login/logout, cookies, contenu protégé                ║
║                                                               ║
║  A. Exécuter TOUS les exercices                             ║
║                                                               ║
║  0. Quitter                                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(menu)


def execute_exercise(exercise_number):
    """Exécution exercice spécifique"""
    exercises = {
        '1': ('exercice_01_books_scraper.py', 'Exercice 1: Books to Scrape'),
        '2': ('exercice_02_quotes_graph.py', 'Exercice 2: Quotes Graph'),
        '3': ('exercice_03_fake_jobs.py', 'Exercice 3: Fake Jobs'),
        '4': ('exercice_04_market_analysis.py', 'Exercice 4: Market Analysis'),
        '5': ('exercice_05_category_navigation.py', 'Exercice 5: Category Navigation'),
        '6': ('exercice_06_resilient_scraper.py', 'Exercice 6: Resilient Scraper'),
        '7': ('exercice_07_data_cleaning.py', 'Exercice 7: Data Cleaning'),
        '8': ('exercice_08_multi_source.py', 'Exercice 8: Multi-Source'),
        '9': ('exercice_09_authentication.py', 'Exercice 9: Authentication'),
    }
    
    if exercise_number not in exercises:
        print(f"Exercice {exercise_number} invalide")
        return False
    
    script_path, exercise_name = exercises[exercise_number]
    
    print(f"\n{'='*70}")
    print(f"EXÉCUTION: {exercise_name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True,
            timeout=300  # Timeout 5 minutes
        )
        
        if result.returncode == 0:
            print(f"\n✓ {exercise_name} terminé avec succès")
            return True
        else:
            print(f"\n✗ {exercise_name} terminé avec erreurs (code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n✗ {exercise_name} - Timeout dépassé")
        return False
    except Exception as e:
        print(f"\n✗ Erreur exécution {exercise_name}: {e}")
        return False


def execute_all_exercises():
    """Exécution séquentielle tous exercices"""
    print("\n" + "="*70)
    print("EXÉCUTION COMPLÈTE - TOUS LES EXERCICES")
    print("="*70)
    
    results = {}
    
    for i in range(1, 10):
        success = execute_exercise(str(i))
        results[i] = success
        
        if i < 9:
            print("\n" + "-"*70)
            print("Pause 2 secondes avant exercice suivant...")
            print("-"*70 + "\n")
            import time
            time.sleep(2)
    
    # Rapport final
    print("\n\n" + "="*70)
    print("RAPPORT FINAL")
    print("="*70)
    
    for exercise_num, success in results.items():
        status = "✓ SUCCÈS" if success else "✗ ÉCHEC"
        print(f"Exercice {exercise_num}: {status}")
    
    total_success = sum(results.values())
    print(f"\nRésultat global: {total_success}/9 exercices réussis")


def main():
    """Boucle principale menu interactif"""
    
    print("\n" + "="*70)
    print("BIENVENUE - EXERCICES WEB SCRAPING PYTHON")
    print("="*70)
    print("\nTous les fichiers de sortie seront dans: ./outputs/")
    print("Note: Limites par défaut configurées pour usage pédagogique")
    
    while True:
        print_menu()
        
        choice = input("Sélection (0-9, A): ").strip().upper()
        
        if choice == '0':
            print("\n✓ Arrêt programme")
            break
        
        elif choice == 'A':
            execute_all_exercises()
            print("\n\nAppuyez sur Entrée pour continuer...")
            input()
        
        elif choice in [str(i) for i in range(1, 10)]:
            execute_exercise(choice)
            print("\n\nAppuyez sur Entrée pour continuer...")
            input()
        
        else:
            print(f"\n✗ Choix invalide: {choice}")
            print("Appuyez sur Entrée pour continuer...")
            input()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Interruption utilisateur - Arrêt programme")
    except Exception as e:
        print(f"\n✗ Erreur critique: {e}")
