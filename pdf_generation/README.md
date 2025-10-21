# Module de Génération de PDF - Surveillance d'Examens

Ce module permet de générer des documents PDF français pour la gestion des examens et de la surveillance, en utilisant WeasyPrint.

## Fonctionnalités

- Génération de listes d'affectation des surveillants
- Format PDF professionnel avec en-têtes et pieds de page
- Pagination automatique pour les longues listes
- Logo ISI intégré
- Style français professionnel

## Installation

Assurez-vous que WeasyPrint est installé :

```bash
pip install weasyprint
```

## Utilisation

### Utilisation Simple

```python
from pdf_generation.surveillance_report import create_surveillance_report

# Liste des enseignants
enseignants = [
    "Dr. Ahmed BENALI",
    "Prof. Fatima ZOUARI",
    "M. Mohamed GHARBI"
]

# Générer le rapport
result = create_surveillance_report(
    enseignants=enseignants,
    semester="S1",
    exam_type="Examen Final",
    session="principale",
    date="15 Janvier 2024",
    seance_name="S1",
    output_path="rapport_surveillance.pdf"
)

print(f"Statut: {result['status']}")
print(f"Message: {result['message']}")
```

### Utilisation Avancée

```python
from pdf_generation.surveillance_report import SurveillanceReportGenerator

# Créer une instance avec logo personnalisé
generator = SurveillanceReportGenerator(logo_path="chemin/vers/logo.png")

# Générer le rapport
result = generator.generate_surveillance_list(
    enseignants=enseignants,
    semester="S2",
    exam_type="Contrôle Continu",
    session="controle",
    date="20 Mars 2024",
    seance_name="S2",
    output_path="rapport.pdf"
)
```

## Paramètres

### Paramètres Obligatoires

- `enseignants` (List[str]): Liste des noms des enseignants
- `semester` (str): Semestre (ex: "S1", "S2")
- `exam_type` (str): Type d'examen
- `session` (str): Type de session ("principale" ou "controle")
- `date` (str): Date de l'examen
- `seance_name` (str): Nom de la séance ("S1" ou "S2")
- `output_path` (str): Chemin de sortie du fichier PDF

### Paramètres Optionnels

- `logo_path` (str): Chemin vers le logo (utilise le logo ISI par défaut)

## Format du Document

Le document généré contient :

1. **En-tête de chaque page** :
   - Logo ISI (en haut à gauche)
   - Numéro de page (en haut à droite)
   - Titre principal : "GESTION DES EXAMENS ET DÉLIBÉRATIONS"
   - Sous-titre : "Procédure d'exécution des épreuves"
   - Type de document : "Liste d'affectation des surveillants"

2. **Titre du document** :
   - Format : "{semester} - Session: {session} - Date: {date} - Séance: {seance_name}"

3. **Tableau des surveillants** :
   - Colonnes : Enseignant, Salle, Signature
   - Pagination automatique
   - En-têtes répétés sur chaque page

## Valeur de Retour

La fonction retourne un dictionnaire avec :

```python
{
    'status': 'success' | 'error',
    'message': 'Description du résultat',
    'output_path': 'Chemin du fichier généré',
    'enseignants_count': nombre_enseignants,
    'generated_at': 'Date et heure de génération'
}
```

## Exemple d'Exécution

Exécutez le fichier d'exemple :

```bash
python pdf_generation/example_usage.py
```

Cela générera deux fichiers PDF d'exemple dans le dossier `data/`.

## Structure des Fichiers

```text
pdf_generation/
├── __init__.py
├── surveillance_report.py    # Module principal
├── example_usage.py         # Exemples d'utilisation
└── README.md               # Cette documentation
```

## Dépendances

- WeasyPrint : Génération de PDF
- pathlib : Gestion des chemins
- datetime : Horodatage
- typing : Annotations de type

## Notes

- Le module est conçu pour être intégré avec le système Seances existant
- Les imports de Seances ne sont pas inclus pour permettre une intégration flexible
- Le logo ISI par défaut est recherché dans `static/isi-logo.jpg`
- Le format est optimisé pour l'impression A4
