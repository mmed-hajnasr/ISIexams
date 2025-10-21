"""
Module de génération de PDF pour les documents de surveillance d'examens
Utilise WeasyPrint pour générer des documents français formatés
"""

import os
from pathlib import Path
from typing import List
from weasyprint import HTML, CSS
from datetime import datetime


def normalize_time_format(time_str: str) -> str:
    """
    Normalize time format to ensure consistent parsing
    Converts both HH:MM and HH:MM:SS to HH:MM:SS format
    """
    if not time_str:
        return "00:00:00"
    
    # If time already has seconds, return as is
    if len(time_str.split(':')) == 3:
        return time_str
    
    # If time only has hours and minutes, add seconds
    if len(time_str.split(':')) == 2:
        return f"{time_str}:00"
    
    # Fallback for any other format
    return "00:00:00"


class EnseignantEmploiGenerator:
    """
    Générateur d'emploi du temps pour les enseignants surveillants
    """
    
    def __init__(self, logo_path: str = None):
        """
        Initialise le générateur
        
        Args:
            logo_path: Chemin vers le logo ISI (optionnel, utilise le chemin par défaut)
        """
        if logo_path is None:
            # Chemin par défaut vers le logo
            current_dir = Path(__file__).parent.parent
            self.logo_path = current_dir / "static" / "isi-logo.jpg"
        else:
            self.logo_path = Path(logo_path)
    
    def generate_emploi(
        self,
        enseignant_name: str,
        schedule: List[tuple],
        output_path: str
    ) -> dict:
        """
        Génère un document PDF d'emploi du temps pour un enseignant
        
        Args:
            enseignant_name: Nom de l'enseignant
            schedule: Liste de tuples (date, h_debut, h_fin)
            output_path: Chemin de sortie du fichier PDF
            
        Returns:
            dict: Rapport de génération avec statut et informations
        """
        try:
            # Créer le répertoire de sortie si nécessaire
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Générer le HTML
            html_content = self._generate_html_content(enseignant_name, schedule)
            
            # Générer le CSS
            css_content = self._generate_css_styles()
            
            # Créer le PDF avec WeasyPrint
            html_doc = HTML(string=html_content, base_url=str(Path(__file__).parent.parent))
            css_doc = CSS(string=css_content)
            
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
            
            return {
                'status': 'success',
                'message': f'PDF généré avec succès: {output_path}',
                'output_path': output_path,
                'enseignant': enseignant_name,
                'schedule_count': len(schedule),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur lors de la génération du PDF: {str(e)}',
                'output_path': output_path,
                'enseignant': enseignant_name,
                'schedule_count': len(schedule) if schedule else 0,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _generate_html_content(
        self,
        enseignant_name: str,
        schedule: List[tuple]
    ) -> str:
        """
        Génère le contenu HTML du document
        """
        # Générer les lignes du tableau d'emploi
        table_rows = ""
        for date, h_debut, h_fin in schedule:
            # Normalize time formats and calculate duration
            h_debut_normalized = normalize_time_format(h_debut)
            h_fin_normalized = normalize_time_format(h_fin)
            
            debut = datetime.strptime(h_debut_normalized, "%H:%M:%S")
            fin = datetime.strptime(h_fin_normalized, "%H:%M:%S")
            duree = fin - debut
            duree_str = f"{duree.seconds // 3600}h{(duree.seconds % 3600) // 60:02d}"
            
            # Format times for display (remove seconds if they are :00)
            h_debut_display = h_debut[:-3]
            h_fin_display = h_fin[:-3]
            
            table_rows += f"""
                <tr>
                    <td class="date-cell">{date}</td>
                    <td class="heure-cell">{h_debut_display} - {h_fin_display}</td>
                    <td class="duree-cell">{duree_str}</td>
                </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Note à {enseignant_name}</title>
        </head>
        <body>
            <div class="page">
                <header class="page-header">
                    <div class="header-left">
                        <img src="{self.logo_path}" alt="Logo ISI" class="logo">
                    </div>
                    <div class="header-center">
                        <h1 class="main-title">GESTION DES EXAMENS ET DÉLIBÉRATIONS</h1>
                        <h2 class="sub-title">Procédure d'exécution des épreuves</h2>
                        <h3 class="list-title">Liste d'affectation des surveillants</h3>
                    </div>
                    <div class="header-right">
                        <span class="page-number">EXD-FR-08-01</span>
                    </div>
                </header>
                
                <main class="content">
                    <div class="note-title">
                        <h2><strong>Note à {enseignant_name}</strong></h2>
                    </div>
                    
                    <div class="message">
                        <p>Cher (e) Collègue,</p>
                        <p>Vous êtes prié (e) d'assurer la surveillance et (ou) la responsabilité des examens selon le calendrier ci joint.</p>
                    </div>
                    
                    <table class="emploi-table">
                        <thead>
                            <tr>
                                <th class="date-header">Date</th>
                                <th class="heure-header">Horaire</th>
                                <th class="duree-header">Durée</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </main>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_css_styles(self) -> str:
        """
        Génère les styles CSS pour le document
        """
        css_content = """
        @page {
            size: A4;
            margin: 2cm 1.5cm;
            @top-left {
                content: "";
            }
            @top-center {
                content: "";
            }
            @top-right {
                content: "Page " counter(page) "/" counter(pages);
                font-size: 12px;
                font-family: Arial, sans-serif;
            }
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .page {
            width: 100%;
            min-height: 100vh;
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #333;
            position: relative;
        }
        
        .header-left {
            flex: 1;
        }
        
        .logo {
            width: 180px;
            height: 120px;
            object-fit: contain;
        }
        
        .header-center {
            flex: 2;
            text-align: center;
            padding: 0 20px;
        }
        
        .main-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        
        .sub-title {
            font-size: 14px;
            font-weight: normal;
            margin-bottom: 3px;
        }
        
        .list-title {
            font-size: 12px;
            font-weight: normal;
            font-style: italic;
        }
        
        .header-right {
            flex: 1;
            text-align: right;
        }
        
        .page-number {
            font-size: 12px;
            font-weight: normal;
        }
        
        .content {
            margin-top: 20px;
        }
        
        .note-title {
            text-align: center;
            margin-bottom: 25px;
            padding: 10px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
        }
        
        .note-title h2 {
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        
        .message {
            margin-bottom: 25px;
            padding: 15px;
            line-height: 1.6;
        }
        
        .message p {
            margin-bottom: 10px;
        }
        
        .emploi-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .emploi-table th,
        .emploi-table td {
            border: 1px solid #333;
            padding: 10px 12px;
            text-align: center;
        }
        
        .emploi-table th {
            background-color: #e6e6e6;
            font-weight: bold;
        }
        
        .date-header,
        .date-cell {
            width: 40%;
        }
        
        .heure-header,
        .heure-cell {
            width: 30%;
        }
        
        .duree-header,
        .duree-cell {
            width: 30%;
        }
        
        .emploi-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .emploi-table tr:hover {
            background-color: #f0f0f0;
        }
        
        /* Gestion des sauts de page */
        .emploi-table {
            page-break-inside: auto;
        }
        
        .emploi-table tr {
            page-break-inside: avoid;
        }
        
        .emploi-table thead {
            display: table-header-group;
        }
        
        /* Répéter l'en-tête sur chaque page */
        @media print {
            .emploi-table thead {
                display: table-header-group;
            }
        }
        """
        
        return css_content


class SurveillanceReportGenerator:
    """
    Générateur de rapports de surveillance d'examens en PDF
    """
    
    def __init__(self, logo_path: str = None):
        """
        Initialise le générateur
        
        Args:
            logo_path: Chemin vers le logo ISI (optionnel, utilise le chemin par défaut)
        """
        if logo_path is None:
            # Chemin par défaut vers le logo
            current_dir = Path(__file__).parent.parent
            self.logo_path = current_dir / "static" / "isi-logo.jpg"
        else:
            self.logo_path = Path(logo_path)
    
    def generate_surveillance_list(
        self,
        enseignants: List[str],
        semester: str,
        exam_type: str,
        session: str,
        date: str,
        seance_name: str,
        output_path: str
    ) -> dict:
        """
        Génère un document PDF de liste d'affectation des surveillants
        
        Args:
            enseignants: Liste des noms des enseignants
            semester: Semestre (ex: "S1", "S2")
            exam_type: Type d'examen
            session: Type de session ("principal" ou "controle")
            date: Date de l'examen
            seance_name: Nom de la séance ("S1" ou "S2")
            output_path: Chemin de sortie du fichier PDF
            
        Returns:
            dict: Rapport de génération avec statut et informations
        """
        try:
            # Créer le répertoire de sortie si nécessaire
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Générer le HTML
            html_content = self._generate_html_content(
                enseignants, semester, exam_type, session, date, seance_name
            )
            
            # Générer le CSS
            css_content = self._generate_css_styles()
            
            # Créer le PDF avec WeasyPrint
            html_doc = HTML(string=html_content, base_url=str(Path(__file__).parent.parent))
            css_doc = CSS(string=css_content)
            
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
            
            return {
                'status': 'success',
                'message': f'PDF généré avec succès: {output_path}',
                'output_path': output_path,
                'enseignants_count': len(enseignants),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur lors de la génération du PDF: {str(e)}',
                'output_path': output_path,
                'enseignants_count': len(enseignants) if enseignants else 0,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _generate_html_content(
        self,
        enseignants: List[str],
        semester: str,
        exam_type: str,
        session: str,
        date: str,
        seance_name: str
    ) -> str:
        """
        Génère le contenu HTML du document
        """
        # Construire le titre
        title = f"{exam_type} {semester} - Session: {session} - Date: {date} - Séance: {seance_name}"
        
        # Générer les lignes du tableau des enseignants
        table_rows = ""
        for enseignant in enseignants:
            table_rows += f"""
                <tr>
                    <td class="enseignant-cell">{enseignant}</td>
                    <td class="salle-cell"></td>
                    <td class="signature-cell"></td>
                </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Liste d'affectation des surveillants</title>
        </head>
        <body>
            <div class="page">
                <header class="page-header">
                    <div class="header-left">
                        <img src="{self.logo_path}" alt="Logo ISI" class="logo">
                    </div>
                    <div class="header-center">
                        <h1 class="main-title">GESTION DES EXAMENS ET DÉLIBÉRATIONS</h1>
                        <h2 class="sub-title">Procédure d'exécution des épreuves</h2>
                        <h3 class="list-title">Liste d'affectation des surveillants</h3>
                    </div>
                    <div class="header-right">
                        <span class="page-number">EXD-FR-08-01</span>
                    </div>
                </header>
                
                <main class="content">
                    <div class="document-title">
                        <h2>{title}</h2>
                    </div>
                    
                    <table class="surveillance-table">
                        <thead>
                            <tr>
                                <th class="enseignant-header">Enseignant</th>
                                <th class="salle-header">Salle</th>
                                <th class="signature-header">Signature</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </main>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_css_styles(self) -> str:
        """
        Génère les styles CSS pour le document
        """
        css_content = """
        @page {
            size: A4;
            margin: 2cm 1.5cm;
            @top-left {
                content: "";
            }
            @top-center {
                content: "";
            }
            @top-right {
                content: "Page " counter(page) "/" counter(pages);
                font-size: 12px;
                font-family: Arial, sans-serif;
            }
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .page {
            width: 100%;
            min-height: 100vh;
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid #333;
            position: relative;
        }
        
        .header-left {
            flex: 1;
        }
        
        .logo {
            width: 180px;
            height: 120px;
            object-fit: contain;
        }
        
        .header-center {
            flex: 2;
            text-align: center;
            padding: 0 20px;
        }
        
        .main-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        
        .sub-title {
            font-size: 14px;
            font-weight: normal;
            margin-bottom: 3px;
        }
        
        .list-title {
            font-size: 12px;
            font-weight: normal;
            font-style: italic;
        }
        
        .header-right {
            flex: 1;
            text-align: right;
        }
        
        .page-number {
            font-size: 12px;
            font-weight: normal;
        }
        
        .content {
            margin-top: 20px;
        }
        
        .document-title {
            text-align: center;
            margin-bottom: 25px;
            padding: 10px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
        }
        
        .document-title h2 {
            font-size: 14px;
            font-weight: bold;
            color: #333;
        }
        
        .surveillance-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .surveillance-table th,
        .surveillance-table td {
            border: 1px solid #333;
            padding: 8px 12px;
            text-align: left;
        }
        
        .surveillance-table th {
            background-color: #e6e6e6;
            font-weight: bold;
            text-align: center;
        }
        
        .enseignant-header,
        .enseignant-cell {
            width: 40%;
        }
        
        .salle-header,
        .salle-cell {
            width: 25%;
        }
        
        .signature-header,
        .signature-cell {
            width: 35%;
        }
        
        .surveillance-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .surveillance-table tr:hover {
            background-color: #f0f0f0;
        }
        
        /* Gestion des sauts de page */
        .surveillance-table {
            page-break-inside: auto;
        }
        
        .surveillance-table tr {
            page-break-inside: avoid;
        }
        
        .surveillance-table thead {
            display: table-header-group;
        }
        
        /* Répéter l'en-tête sur chaque page */
        @media print {
            .surveillance-table thead {
                display: table-header-group;
            }
        }
        """
        
        return css_content


def create_surveillance_report(
    enseignants: List[str],
    semester: str,
    exam_type: str,
    session: str,
    date: str,
    seance_name: str,
    output_path: str,
    logo_path: str = None
) -> dict:
    """
    Fonction utilitaire pour créer un rapport de surveillance
    
    Args:
        enseignants: Liste des noms des enseignants
        semester: Semestre (ex: "S1", "S2")
        exam_type: Type d'examen
        session: Type de session ("principal" ou "controle")
        date: Date de l'examen
        seance_name: Nom de la séance ("S1" ou "S2")
        output_path: Chemin de sortie du fichier PDF
        logo_path: Chemin vers le logo (optionnel)
        
    Returns:
        dict: Rapport de génération
    """
    generator = SurveillanceReportGenerator(logo_path)
    return generator.generate_surveillance_list(
        enseignants, semester, exam_type, session, date, seance_name, output_path
    )


def create_enseignant_emploi(
    enseignant_name: str,
    schedule: List[tuple],
    output_path: str,
    logo_path: str = None
) -> dict:
    """
    Fonction utilitaire pour créer un emploi du temps d'enseignant
    
    Args:
        enseignant_name: Nom de l'enseignant
        schedule: Liste de tuples (date, h_debut, h_fin)
        output_path: Chemin de sortie du fichier PDF
        logo_path: Chemin vers le logo (optionnel)
        
    Returns:
        dict: Rapport de génération
    """
    generator = EnseignantEmploiGenerator(logo_path)
    return generator.generate_emploi(enseignant_name, schedule, output_path)
