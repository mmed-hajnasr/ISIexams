from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
import csv
import os


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


@dataclass
class Seance:
    """Represents a single exam session"""
    h_debut: str
    h_fin: str
    salles: Set[str] = field(default_factory=set)  # Unique room codes
    responsables: Set[int] = field(default_factory=set)  # Unique teacher IDs
    
    def add_salle(self, salle: str):
        """Add a room to this session"""
        self.salles.add(salle)
    
    def add_enseignant(self, enseignant: int):
        """Add a teacher to this session"""
        self.responsables.add(enseignant)


@dataclass
class Seances:
    """Main structure containing all exam sessions"""
    semester: Optional[str] = None
    dates: List[str] = field(default_factory=list)  # Ordered list of exam dates
    date_seances: Dict[str, List[Seance]] = field(default_factory=dict)  # date -> ordered list of seances
    exam_type: Optional[str] = None  # "Examen" or "Devoir surveillé"
    session: Optional[str] = None  # "Principal" or "Contrôle"
    
    def add_seance(self, date: str, seance: Seance):
        """Add a session to a specific date"""
        if date not in self.date_seances:
            self.date_seances[date] = []
            if date not in self.dates:
                self.dates.append(date)
        self.date_seances[date].append(seance)
    
    def get_seances_by_date(self, date: str) -> List[Seance]:
        """Get all sessions for a specific date"""
        return self.date_seances.get(date, [])
    
    def get_seance_by_date_and_index(self, date: str, index: int) -> Optional[Seance]:
        """Get a session by date and index (0-based)"""
        seances = self.get_seances_by_date(date)
        if 0 <= index < len(seances):
            return seances[index]
        return None
    
    def get_seance_name(self, date: str, index: int) -> str:
        """Get the name (S1, S2, etc.) for a seance based on its position"""
        return f"S{index + 1}"
    
    @classmethod
    def from_csv(cls, csv_file_path: str) -> 'Seances':
        """Create a Seances object from CSV or XLSX file"""
        seances_obj = cls()
        
        # Track sessions by date and time
        date_time_sessions = {}  # (date, h_debut, h_fin) -> seance
        
        # Read data from CSV or XLSX file
        rows = read_data_file(csv_file_path)
        
        for row in rows:
            date_exam = row['dateExam']
            # Extract only time part from h_debut and h_fin (format: "30/12/1999 HH:MM:SS")
            h_debut = row['h_debut'].split(' ')[1] if ' ' in row['h_debut'] else row['h_debut']
            h_fin = row['h_fin'].split(' ')[1] if ' ' in row['h_fin'] else row['h_fin']
            session_type = row['session']
            type_ex = row['type ex']
            semestre = row['semestre']
            enseignant = int(row['enseignant'])
            cod_salle = row['cod_salle']
            
            # Set metadata from first row
            if seances_obj.semester is None:
                seances_obj.semester = semestre if semestre else None
                # Map session type
                if session_type == 'P':
                    seances_obj.session = "Principal"
                elif session_type == 'C':
                    seances_obj.session = "Contrôle"
                else:
                    seances_obj.session = session_type
                
                # Map exam type
                if type_ex == 'E':
                    seances_obj.exam_type = "Examen"
                elif type_ex == 'DS':
                    seances_obj.exam_type = "Devoir surveillé"
                else:
                    seances_obj.exam_type = type_ex
            
            # Create unique key for this time slot
            time_key = (date_exam, h_debut, h_fin)
            
            if time_key not in date_time_sessions:
                # Create new session
                seance = Seance(
                    h_debut=h_debut,
                    h_fin=h_fin
                )
                seance.add_enseignant(enseignant)
                seance.add_salle(cod_salle)
                
                date_time_sessions[time_key] = seance
                seances_obj.add_seance(date_exam, seance)
            else:
                # Add to existing session
                existing_seance = date_time_sessions[time_key]
                existing_seance.add_enseignant(enseignant)
                existing_seance.add_salle(cod_salle)
        
        # Sort dates to maintain order
        seances_obj.dates.sort()
        
        # Sort seances within each date by start time
        for date in seances_obj.dates:
            seances_obj.date_seances[date].sort(key=lambda s: s.h_debut)
        
        return seances_obj
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        seances_by_date = {}
        for date in self.dates:
            seances_by_date[date] = [
                {
                    'name': self.get_seance_name(date, i),
                    'h_debut': s.h_debut,
                    'h_fin': s.h_fin,
                    'salles': list(s.salles),
                    'enseignants': list(s.responsables)
                }
                for i, s in enumerate(self.date_seances[date])
            ]
        
        return {
            'semester': self.semester,
            'dates': self.dates,
            'exam_type': self.exam_type,
            'session': self.session,
            'seances_by_date': seances_by_date
        }
    
    def get_day_seance_teachers_mapping(self) -> Dict[tuple[int, int], List[int]]:
        """
        Returns a dictionary mapping (day_index, seance_index) tuples to lists of responsible teachers.
        
        Returns:
            Dict with keys as (day_index, seance_index) tuples and values as lists of teacher IDs
            where day_index is 0-based index in self.dates and seance_index is 0-based index
            within that day's sessions
        """
        mapping = {}
        
        for day_index, date in enumerate(self.dates):
            for seance_index, seance in enumerate(self.date_seances[date]):
                key = (day_index, seance_index)
                mapping[key] = list(seance.responsables)
        
        return mapping
    
    def __str__(self) -> str:
        """String representation"""
        total_sessions = sum(len(sessions) for sessions in self.date_seances.values())
        result = f"Seances - {self.semester} ({self.exam_type}, {self.session})\n"
        result += f"Dates: {', '.join(self.dates)}\n"
        result += f"Total sessions: {total_sessions}\n\n"
        
        for date in self.dates:
            result += f"Date: {date}\n"
            for i, seance in enumerate(self.date_seances[date]):
                session_name = self.get_seance_name(date, i)
                result += f"  {session_name}: {seance.h_debut}-{seance.h_fin}\n"
                result += f"    Rooms: {', '.join(sorted(seance.salles))}\n"
                result += f"    Teachers: {', '.join(map(str, sorted(seance.responsables)))}\n"
            result += "\n"
        
        return result


# Example usage
if __name__ == "__main__":
    # Load seances from XLSX
    seances = Seances.from_csv('data/salle.xlsx')
    
    # Print summary
    print(seances)
    
    # Example: Get sessions for first date
    if seances.dates:
        first_date = seances.dates[0]
        first_date_sessions = seances.get_seances_by_date(first_date)
        print(f"Date {first_date} has {len(first_date_sessions)} sessions")
        
        # Example: Get specific session (first session of first date)
        s1 = seances.get_seance_by_date_and_index(first_date, 0)
        if s1:
            session_name = seances.get_seance_name(first_date, 0)
            print(f"{session_name}: {s1.h_debut}-{s1.h_fin} with {len(s1.salles)} rooms and {len(s1.responsables)} teachers")
