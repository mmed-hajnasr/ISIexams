from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Tuple
import csv
import os
from datetime import datetime


def read_data_file(file_path: str):
    """Read data from CSV or XLSX file and return rows as dictionaries"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.xlsx':
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl library is required for Excel files. Install it with: pip install openpyxl")
        
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        
        # Get header row
        headers = [cell.value for cell in sheet[1]]
        
        # Read data rows
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(cell is not None for cell in row):  # Skip empty rows
                row_dict = {headers[i]: str(row[i]) if row[i] is not None else '' for i in range(len(headers))}
                rows.append(row_dict)
        
        workbook.close()
        return rows
        
    elif file_ext == '.csv':
        rows = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                rows.append(row)
        return rows
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Only .csv and .xlsx are supported.")


def get_weekday_from_date(date_str: str) -> int:
    """Convert date string (DD/MM/YYYY) to weekday number (0=Monday, 6=Sunday)"""
    try:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.weekday()
    except ValueError:
        return -1


def map_french_weekday_to_number(jour: str) -> int:
    """Map French weekday names to numbers (0=Monday, 6=Sunday)"""
    weekdays = {
        'Lundi': 0, 'lundi': 0,
        'Mardi': 1, 'mardi': 1,
        'Mercredi': 2, 'mercredi': 2,
        'Jeudi': 3, 'jeudi': 3,
        'Vendredi': 4, 'vendredi': 4,
        'Samedi': 5, 'samedi': 5,
        'Dimanche': 6, 'dimanche': 6
    }
    return weekdays.get(jour, -1)


@dataclass
class Souhaits:
    """Represents the preferences of a teacher for days and sessions they don't want to work"""
    semestre: str
    session: str  # e.g., "Partiel"
    unavailable_slots: Set[Tuple[int, int]] = field(default_factory=set)  # Set of (day_number, session_number) tuples
    
    def add_unavailable_slot(self, day: int, seance: int):
        """Add a day and session combination that the teacher wants to avoid"""
        self.unavailable_slots.add((day, seance))
    
    def is_available(self, day: int, seance: int) -> bool:
        """Check if the teacher is available for a specific day and session"""
        return (day, seance) not in self.unavailable_slots
    
    def get_unavailable_days(self) -> Set[int]:
        """Get all days the teacher is unavailable"""
        return {day for day, _ in self.unavailable_slots}
    
    def get_unavailable_sessions_for_day(self, day: int) -> Set[int]:
        """Get all sessions the teacher is unavailable for on a specific day"""
        return {seance for d, seance in self.unavailable_slots if d == day}


@dataclass
class Enseignant:
    """Represents a single teacher"""
    nom: str
    prenom: str
    email: str  # Must be unique
    grade: str
    code: Optional[int] = None
    participe_surveillance: bool = False
    souhaits: Optional[Souhaits] = None
    
    def __post_init__(self):
        """Convert string boolean to actual boolean for participe_surveillance"""
        if isinstance(self.participe_surveillance, str):
            self.participe_surveillance = self.participe_surveillance.upper() == 'TRUE'
    
    def add_souhaits(self, souhaits: Souhaits):
        """Add preferences for this teacher"""
        self.souhaits = souhaits
    
    def is_available(self, day: int, seance: int) -> bool:
        """Check if the teacher is available for a specific day and session"""
        if self.souhaits is None:
            return True  # No preferences means available for all slots
        return self.souhaits.is_available(day, seance)


@dataclass
class Enseignants:
    """Main structure containing all teachers"""
    enseignants_list: List[Enseignant] = field(default_factory=list)
    unique_grades: Set[str] = field(default_factory=set)
    
    def get_used_codes(self) -> Set[int]:
        """Get all codes that are currently in use"""
        used_codes = set()
        for enseignant in self.enseignants_list:
            if enseignant.code is not None:
                used_codes.add(enseignant.code)
        return used_codes
    
    def get_next_available_code(self, start_from: int = 1) -> int:
        """Get the next available code starting from start_from"""
        used_codes = self.get_used_codes()
        code = start_from
        while code in used_codes:
            code += 1
        return code
    
    def add_enseignant(self, enseignant: Enseignant):
        """Add a teacher to the list and update unique grades"""
        # Check for unique email
        if self.get_enseignant_by_email(enseignant.email) is not None:
            raise ValueError(f"Email {enseignant.email} already exists")
        
        # Auto-assign code if not provided or if code is already in use
        if enseignant.code is None:
            enseignant.code = self.get_next_available_code()
        else:
            # Check if the provided code is already in use
            if self.get_enseignant_by_code(enseignant.code) is not None:
                # Code is already in use, assign a new one
                old_code = enseignant.code
                enseignant.code = self.get_next_available_code()
                print(f"Warning: Code {old_code} already in use for {enseignant.prenom} {enseignant.nom}. Assigned new code: {enseignant.code}")
        
        self.enseignants_list.append(enseignant)
        self.unique_grades.add(enseignant.grade)
    
    def get_enseignant_by_email(self, email: str) -> Optional[Enseignant]:
        """Get a teacher by their email address"""
        for enseignant in self.enseignants_list:
            if enseignant.email == email:
                return enseignant
        return None
    
    def get_enseignant_by_code(self, code: int) -> Optional[Enseignant]:
        """Get a teacher by their code"""
        for enseignant in self.enseignants_list:
            if enseignant.code == code:
                return enseignant
        return None
    
    def get_enseignant_by_name(self, nom: str, prenom: str) -> Optional[Enseignant]:
        """Get a teacher by their full name"""
        for enseignant in self.enseignants_list:
            if enseignant.nom == nom and enseignant.prenom == prenom:
                return enseignant
        return None
    
    def get_enseignants_by_grade(self, grade: str) -> List[Enseignant]:
        """Get all teachers with a specific grade"""
        return [ens for ens in self.enseignants_list if ens.grade == grade]
    
    def get_enseignants_participating_surveillance(self) -> List[Enseignant]:
        """Get all teachers who participate in surveillance"""
        return [ens for ens in self.enseignants_list if ens.participe_surveillance]
    
    def get_enseignants_not_participating_surveillance(self) -> List[Enseignant]:
        """Get all teachers who don't participate in surveillance"""
        return [ens for ens in self.enseignants_list if not ens.participe_surveillance]
    
    def add_souhaits_to_enseignant(self, nom: str, prenom: str, souhaits: Souhaits) -> bool:
        """Add preferences to a specific teacher. Returns True if successful, False if teacher not found"""
        enseignant = self.get_enseignant_by_name(nom, prenom)
        if enseignant is None:
            return False
        enseignant.add_souhaits(souhaits)
        return True
    
    def clear_all_souhaits(self):
        """Clear all souhaits for all teachers"""
        for enseignant in self.enseignants_list:
            enseignant.souhaits = None
    
    def load_souhaits_from_csv(self, csv_file_path: str, seances_data, clear_existing: bool = True) -> Dict[str, List[str]]:
        """Load teacher preferences from CSV or XLSX file. Returns dict of errors by teacher name
        
        Args:
            csv_file_path: Path to the CSV or XLSX file
            seances_data: Seances object to map weekdays to actual exam dates
            clear_existing: If True, clear all existing souhaits before loading new ones
        """
        errors = {}
        
        # Clear existing souhaits if requested
        if clear_existing:
            self.clear_all_souhaits()
        
        if not seances_data or not seances_data.dates:
            errors['System'] = ['No seances data available for mapping weekdays to dates']
            return errors
        
        # Create mapping from weekday numbers to day indices in seances
        weekday_to_day_index = {}
        for day_index, date in enumerate(seances_data.dates):
            weekday = get_weekday_from_date(date)
            if weekday != -1:
                if weekday not in weekday_to_day_index:
                    weekday_to_day_index[weekday] = []
                # Store 0-based day_index for internal use, will convert to 1-based later
                weekday_to_day_index[weekday].append(day_index)
        
        # Group souhaits by teacher
        teacher_souhaits = {}
        
        # Read data from CSV or XLSX file
        rows = read_data_file(csv_file_path)
        
        for row in rows:
            enseignant_name = row['Enseignant'].strip()
            semestre = row['Semestre'].strip()
            session = row['Session'].strip()
            jour = row['Jour'].strip()
            seances_str = row['Séances'].strip()
                
            # Parse teacher name (format: "Prenom.NOM" or "Prenom NOM")
            # Examples from souhait.csv: "N.BEN HARIZ", "A.NAFTI", etc.
            if '.' in enseignant_name:
                parts = enseignant_name.split('.', 1)  # Split only on first dot
                prenom_initial = parts[0].strip()
                nom = parts[1].strip()
                
                # Find teacher by matching last name and first initial
                matching_teacher = None
                for teacher in self.enseignants_list:
                    # Check if last name matches exactly
                    if teacher.nom.upper() == nom.upper():
                        # Check if first initial matches
                        if teacher.prenom and teacher.prenom[0].upper() == prenom_initial.upper():
                            matching_teacher = teacher
                            break
                
                if matching_teacher:
                    nom = matching_teacher.nom
                    prenom = matching_teacher.prenom
                else:
                    # If no match found, set error and continue
                    if enseignant_name not in errors:
                        errors[enseignant_name] = []
                    errors[enseignant_name].append(f"Teacher not found: no match for '{prenom_initial}.{nom}'")
                    continue
            else:
                # If no dot, try splitting by space and take last as nom
                parts = enseignant_name.split()
                if len(parts) >= 2:
                    prenom = ' '.join(parts[:-1])
                    nom = parts[-1]
                else:
                    # If can't parse, use the whole string as nom
                    prenom = ""
                    nom = enseignant_name
            
            # Map French weekday to weekday number
            weekday_num = map_french_weekday_to_number(jour)
            if weekday_num == -1:
                if enseignant_name not in errors:
                    errors[enseignant_name] = []
                errors[enseignant_name].append(f"Unknown weekday: {jour}")
                continue
            
            # Get corresponding day indices for this weekday
            day_indices = weekday_to_day_index.get(weekday_num, [])
            if not day_indices:
                if enseignant_name not in errors:
                    errors[enseignant_name] = []
                errors[enseignant_name].append(f"No exam dates found for {jour}")
                continue
            
            # Parse sessions (format: "S1,S2,S3" or "S1")
            seance_numbers = []
            for seance_str in seances_str.split(','):
                seance_str = seance_str.strip()
                if seance_str.startswith('S') and len(seance_str) > 1:
                    try:
                        seance_num = int(seance_str[1:])  # Keep 1-based indexing
                        seance_numbers.append(seance_num)
                    except ValueError:
                        if enseignant_name not in errors:
                            errors[enseignant_name] = []
                        errors[enseignant_name].append(f"Invalid session format: {seance_str}")
            
            # Create entries for each day that matches this weekday
            teacher_key = (nom, prenom, semestre, session)
            if teacher_key not in teacher_souhaits:
                teacher_souhaits[teacher_key] = []
            
            for day_index in day_indices:
                for seance_index in seance_numbers:
                    # Convert to 1-based indexing for both day and seance
                    teacher_souhaits[teacher_key].append((day_index + 1, seance_index))
        
        # Create Souhaits objects and assign to teachers
        for (nom, prenom, semestre, session), slots in teacher_souhaits.items():
            # Check if teacher exists
            enseignant = self.get_enseignant_by_name(nom, prenom)
            if enseignant is None:
                teacher_name = f"{prenom} {nom}"
                if teacher_name not in errors:
                    errors[teacher_name] = []
                errors[teacher_name].append(f"Teacher not found in database")
                continue
            
            # Clear existing souhaits and create new ones
            # This ensures we don't have duplicate or conflicting souhaits
            enseignant.souhaits = Souhaits(semestre=semestre, session=session)
            
            # Add all unavailable slots
            for day_index, seance_index in slots:
                enseignant.souhaits.add_unavailable_slot(day_index, seance_index)
        
        return errors
    
    @classmethod
    def from_csv(cls, csv_file_path: str) -> 'Enseignants':
        """Create an Enseignants object from CSV or XLSX file"""
        enseignants_obj = cls()
        
        # Read data from CSV or XLSX file
        rows = read_data_file(csv_file_path)
        
        for row in rows:
            nom = row['nom_ens'].strip()
            prenom = row['prenom_ens'].strip()
            email = row['email_ens'].strip()
            grade = row['grade_code_ens'].strip()
            code_str = row['code_smartex_ens'].strip()
            participe = row['participe_surveillance'].strip()
            
            # Handle empty code - will be auto-assigned in add_enseignant
            code = None
            if code_str and code_str.isdigit():
                code = int(code_str)
            
            # Create enseignant
            enseignant = Enseignant(
                nom=nom,
                prenom=prenom,
                email=email,
                grade=grade,
                code=code,
                participe_surveillance=participe
            )
            
            # Track if code was missing for informational message
            code_was_missing = (code is None)
            
            try:
                enseignants_obj.add_enseignant(enseignant)
                # Inform about auto-assigned codes
                if code_was_missing:
                    print(f"Info: Auto-assigned code {enseignant.code} to {enseignant.prenom} {enseignant.nom}")
            except ValueError as e:
                print(f"Warning: Skipping duplicate email - {e}")
        
        return enseignants_obj
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'unique_grades': list(self.unique_grades),
            'total_enseignants': len(self.enseignants_list),
            'participating_surveillance': len(self.get_enseignants_participating_surveillance()),
            'enseignants': [
                {
                    'nom': ens.nom,
                    'prenom': ens.prenom,
                    'email': ens.email,
                    'grade': ens.grade,
                    'code': ens.code,
                    'participe_surveillance': ens.participe_surveillance,
                    'souhaits': {
                        'semestre': ens.souhaits.semestre,
                        'session': ens.souhaits.session,
                        'unavailable_slots': list(ens.souhaits.unavailable_slots)
                    } if ens.souhaits else None
                }
                for ens in self.enseignants_list
            ]
        }
    
    def __str__(self) -> str:
        """String representation"""
        participating = len(self.get_enseignants_participating_surveillance())
        not_participating = len(self.get_enseignants_not_participating_surveillance())
        
        result = f"Enseignants Database\n"
        result += f"Total teachers: {len(self.enseignants_list)}\n"
        result += f"Participating in surveillance: {participating}\n"
        result += f"Not participating in surveillance: {not_participating}\n"
        result += f"Unique grades: {', '.join(sorted(self.unique_grades))}\n\n"
        
        # Group by grade
        for grade in sorted(self.unique_grades):
            grade_teachers = self.get_enseignants_by_grade(grade)
            result += f"Grade {grade} ({len(grade_teachers)} teachers):\n"
            for ens in grade_teachers:
                surveillance_status = "✓" if ens.participe_surveillance else "✗"
                code_str = str(ens.code) if ens.code is not None else "N/A"
                souhaits_info = ""
                if ens.souhaits:
                    unavailable_count = len(ens.souhaits.unavailable_slots)
                    souhaits_info = f" [Souhaits: {unavailable_count} unavailable slots]"
                result += f"  {surveillance_status} {ens.nom}, {ens.prenom} (Code: {code_str}) - {ens.email}{souhaits_info}\n"
            result += "\n"
        
        return result
    
    def get_statistics(self) -> dict:
        """Get statistics about the teachers"""
        stats = {
            'total': len(self.enseignants_list),
            'participating_surveillance': len(self.get_enseignants_participating_surveillance()),
            'not_participating_surveillance': len(self.get_enseignants_not_participating_surveillance()),
            'by_grade': {}
        }
        
        for grade in self.unique_grades:
            grade_teachers = self.get_enseignants_by_grade(grade)
            participating = len([t for t in grade_teachers if t.participe_surveillance])
            stats['by_grade'][grade] = {
                'total': len(grade_teachers),
                'participating': participating,
                'not_participating': len(grade_teachers) - participating
            }
        
        return stats


# Example usage
if __name__ == "__main__":
    # Import Seances for testing
    from seances import Seances
    
    # Load enseignants from CSV
    enseignants = Enseignants.from_csv('data/enseignant.csv')
    
    # Print summary
    print(enseignants)
    
    # Get statistics
    stats = enseignants.get_statistics()
    print("Statistics:")
    print(f"Total: {stats['total']}")
    print(f"Surveillance participation rate: {stats['participating_surveillance']}/{stats['total']} ({stats['participating_surveillance']/stats['total']*100:.1f}%)")
    
    # Example: Find a specific teacher
    teacher = enseignants.get_enseignant_by_code(375)
    if teacher:
        print(f"\nTeacher with code 375: {teacher.prenom} {teacher.nom} ({teacher.email})")
    
    # Example: Get all professors
    professors = enseignants.get_enseignants_by_grade('PR')
    print(f"\nProfessors: {len(professors)} found")
    for prof in professors:
        print(f"  - {prof.prenom} {prof.nom}")
    
    # Load seances data first (required for souhaits mapping)
    print("\n" + "="*50)
    print("Loading seances from CSV...")
    seances_data = Seances.from_csv('data/salle.csv')
    print(f"Loaded {len(seances_data.dates)} exam dates")
    
    # Load souhaits from CSV
    print("Loading souhaits from CSV...")
    errors = enseignants.load_souhaits_from_csv('data/souhait.csv', seances_data)
    
    if errors:
        print("Errors encountered:")
        for teacher, error_list in errors.items():
            print(f"  {teacher}: {', '.join(error_list)}")
    else:
        print("All souhaits loaded successfully!")
    
    # Show teachers with souhaits
    teachers_with_souhaits = [ens for ens in enseignants.enseignants_list if ens.souhaits]
    print(f"\nTeachers with preferences: {len(teachers_with_souhaits)}")
    for teacher in teachers_with_souhaits:
        unavailable = len(teacher.souhaits.unavailable_slots)
        print(f"  - {teacher.prenom} {teacher.nom}: {unavailable} unavailable slots")
        if unavailable > 0:
            for day, seance in sorted(teacher.souhaits.unavailable_slots):
                print(f"    Day {day}, S{seance}")  # Display as 1-based
    
    # Example: Check availability
    if teachers_with_souhaits:
        teacher = teachers_with_souhaits[0]
        print(f"\nAvailability check for {teacher.prenom} {teacher.nom}:")
        print(f"  Available Day 1, S1: {teacher.is_available(1, 1)}")
        print(f"  Available Day 1, S4: {teacher.is_available(1, 4)}")