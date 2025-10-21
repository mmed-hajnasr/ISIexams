"""
Exemple d'utilisation du module de génération de rapports de surveillance
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour permettre l'import
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_generation.surveillance_report import create_surveillance_report, SurveillanceReportGenerator, create_enseignant_emploi, EnseignantEmploiGenerator

# Exemple d'utilisation simple avec la fonction utilitaire
def example_simple_usage():
    """Exemple simple d'utilisation"""
    
    # Liste exemple d'enseignants
    enseignants = [
        "Dr. Ahmed BENALI",
        "Prof. Fatima ZOUARI",
        "M. Mohamed GHARBI",
        "Mme. Leila MANSOURI",
        "Dr. Karim BELHAJ",
        "Prof. Nadia SLIM",
        "M. Youssef TRABELSI"
    ]
    
    # Paramètres de l'examen
    semester = "S1"
    exam_type = "Examen Final"
    session = "principale"
    date = "15 Janvier 2024"
    seance_name = "S1"
    output_path = "data/rapport_surveillance_exemple.pdf"
    
    # Générer le rapport
    result = create_surveillance_report(
        enseignants=enseignants,
        semester=semester,
        exam_type=exam_type,
        session=session,
        date=date,
        seance_name=seance_name,
        output_path=output_path
    )
    
    print("Résultat de la génération:")
    print(f"Statut: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Nombre d'enseignants: {result['enseignants_count']}")
    print(f"Généré le: {result['generated_at']}")
    
    return result

# Exemple d'utilisation avec la classe pour plus de contrôle
def example_class_usage():
    """Exemple d'utilisation avec la classe"""
    
    # Créer une instance du générateur
    generator = SurveillanceReportGenerator()
    
    # Liste d'enseignants plus longue pour tester la pagination
    enseignants = [
        f"Enseignant {i+1:02d}" for i in range(25)
    ]
    
    # Générer le rapport
    result = generator.generate_surveillance_list(
        enseignants=enseignants,
        semester="S2",
        exam_type="Contrôle Continu",
        session="controle",
        date="20 Mars 2024",
        seance_name="S2",
        output_path="data/rapport_surveillance_long.pdf"
    )
    
    return result

# Exemple d'utilisation du générateur d'emploi du temps enseignant
def example_enseignant_emploi():
    """Exemple de génération d'emploi du temps pour un enseignant"""
    
    # Nom de l'enseignant
    enseignant_name = "Dr. Ahmed BENALI"
    
    # Planning d'exemple avec des créneaux de surveillance
    schedule = [
        ("15 Janvier 2024", "08:00", "10:00"),
        ("16 Janvier 2024", "14:00", "16:30"),
        ("20 Janvier 2024", "09:00", "11:00"),
        ("22 Janvier 2024", "13:30", "15:30"),
        ("25 Janvier 2024", "08:30", "10:30")
    ]
    
    output_path = "data/emploi_ahmed_benali.pdf"
    
    # Générer l'emploi du temps
    result = create_enseignant_emploi(
        enseignant_name=enseignant_name,
        schedule=schedule,
        output_path=output_path
    )
    
    print("Résultat de la génération d'emploi:")
    print(f"Statut: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Enseignant: {result['enseignant']}")
    print(f"Nombre de créneaux: {result['schedule_count']}")
    print(f"Généré le: {result['generated_at']}")
    
    return result

# Exemple d'utilisation avec la classe EnseignantEmploiGenerator
def example_emploi_class_usage():
    """Exemple d'utilisation avec la classe EnseignantEmploiGenerator"""
    
    # Créer une instance du générateur
    generator = EnseignantEmploiGenerator()
    
    # Planning pour plusieurs jours avec horaires variés
    schedule = [
        ("10 Mars 2024", "08:00", "10:00"),
        ("11 Mars 2024", "10:30", "12:30"),
        ("12 Mars 2024", "14:00", "17:00"),
        ("15 Mars 2024", "08:30", "10:30"),
        ("16 Mars 2024", "13:00", "15:00"),
        ("18 Mars 2024", "09:00", "12:00"),
        ("20 Mars 2024", "14:30", "16:30")
    ]
    
    # Générer l'emploi du temps
    result = generator.generate_emploi(
        enseignant_name="Prof. Fatima ZOUARI",
        schedule=schedule,
        output_path="data/emploi_fatima_zouari.pdf"
    )
    
    print("Résultat avec classe:")
    print(f"Statut: {result['status']}")
    print(f"Enseignant: {result['enseignant']}")
    print(f"Nombre de créneaux: {result['schedule_count']}")
    
    return result

if __name__ == "__main__":
    print("=== Exemple d'utilisation du générateur de rapports de surveillance ===")
    print()
    
    print("1. Génération d'un rapport simple:")
    result1 = example_simple_usage()
    print()
    
    print("2. Génération d'un rapport avec liste longue:")
    result2 = example_class_usage()
    print()
    
    print("3. Génération d'emploi du temps pour enseignant:")
    result3 = example_enseignant_emploi()
    print()
    
    print("4. Génération d'emploi du temps avec classe:")
    result4 = example_emploi_class_usage()
    print()
    
    print("Exemples terminés!")
