from dataclasses import dataclass, field
from typing import Dict, Set, List, Tuple
from enseignants import Enseignants


@dataclass
class Configuration:
    """Configuration class that manages grade-to-hours mapping and surveillance requirements"""
    grade_hours: Dict[str, int] = field(default_factory=dict)
    teachers_per_room: int = 2
    surplus_teachers_per_room: float = 0.5
    
    def set_grade_hours(self, grade: str, hours: int):
        """Set the number of hours for a specific grade"""
        if hours < 0:
            raise ValueError("Hours cannot be negative")
        self.grade_hours[grade] = hours
    
    def set_teachers_per_room(self, teachers_per_room: int):
        """Set the number of teachers required per room"""
        if teachers_per_room < 1:
            raise ValueError("Teachers per room must be at least 1")
        self.teachers_per_room = teachers_per_room
    
    def set_surplus_teachers_per_room(self, surplus_teachers_per_room: float):
        """Set the number of surplus teachers per room"""
        if surplus_teachers_per_room < 0:
            raise ValueError("Surplus teachers per room cannot be negative")
        self.surplus_teachers_per_room = surplus_teachers_per_room
    
    def get_grade_hours(self, grade: str) -> int:
        """Get the number of hours for a specific grade"""
        return self.grade_hours.get(grade, 0)
    
    def remove_grade(self, grade: str) -> bool:
        """Remove a grade from the configuration. Returns True if grade was removed, False if not found"""
        if grade in self.grade_hours:
            del self.grade_hours[grade]
            return True
        return False
    
    def get_all_configured_grades(self) -> Set[str]:
        """Get all grades that have been configured"""
        return set(self.grade_hours.keys())
    
    def check_all_grades_configured(self, enseignants: Enseignants) -> Dict[str, bool]:
        """
        Check if all grades from Enseignants have been configured with hours.
        
        Args:
            enseignants: Enseignants object containing teacher data
            
        Returns:
            Dict where key is grade and value is True if configured, False otherwise
        """
        result = {}
        for grade in enseignants.unique_grades:
            result[grade] = grade in self.grade_hours
        return result
    
    def get_missing_grades(self, enseignants: Enseignants) -> Set[str]:
        """
        Get all grades from Enseignants that haven't been configured yet.
        
        Args:
            enseignants: Enseignants object containing teacher data
            
        Returns:
            Set of grades that are missing configuration
        """
        return enseignants.unique_grades - self.get_all_configured_grades()
    
    def get_extra_grades(self, enseignants: Enseignants) -> Set[str]:
        """
        Get all grades that are configured but don't exist in Enseignants.
        
        Args:
            enseignants: Enseignants object containing teacher data
            
        Returns:
            Set of grades that are configured but not used
        """
        return self.get_all_configured_grades() - enseignants.unique_grades
    
    def is_fully_configured(self, enseignants: Enseignants) -> bool:
        """
        Check if all grades from Enseignants have been configured.
        
        Args:
            enseignants: Enseignants object containing teacher data
            
        Returns:
            True if all grades are configured, False otherwise
        """
        return len(self.get_missing_grades(enseignants)) == 0
    
    def calculate_teacher_requirements(self, seances) -> Dict[Tuple[int, int], int]:
        """
        Calculate how many teachers are needed for each seance based on number of rooms.
        
        Args:
            seances: Seances object containing exam session data
            
        Returns:
            Dictionary with (day_number, seance_number) as key and required teachers as value
        """
        requirements = {}
        
        for day_idx, date in enumerate(seances.dates, 1):  # Start from day 1
            date_seances = seances.get_seances_by_date(date)
            for seance_idx, seance in enumerate(date_seances, 1):  # Start from seance 1
                num_rooms = len(seance.salles)
                required_teachers = num_rooms * self.teachers_per_room
                requirements[(day_idx, seance_idx)] = required_teachers
        
        return requirements
    
    def get_configuration_summary(self, enseignants: Enseignants) -> Dict[str, any]:
        """
        Get a comprehensive summary of the configuration status.
        
        Args:
            enseignants: Enseignants object containing teacher data
            
        Returns:
            Dictionary with configuration summary
        """
        missing_grades = self.get_missing_grades(enseignants)
        extra_grades = self.get_extra_grades(enseignants)
        
        return {
            'total_grades_in_system': len(enseignants.unique_grades),
            'total_configured_grades': len(self.grade_hours),
            'is_fully_configured': len(missing_grades) == 0,
            'missing_grades': list(missing_grades),
            'extra_grades': list(extra_grades),
            'configured_grades': dict(self.grade_hours),
            'total_hours_configured': sum(self.grade_hours.values()),
            'teachers_per_room': self.teachers_per_room,
            'surplus_teachers_per_room': self.surplus_teachers_per_room
        }
    
    def to_dict(self) -> Dict[str, any]:
        """Convert configuration to dictionary for serialization"""
        return {
            'grade_hours': dict(self.grade_hours),
            'teachers_per_room': self.teachers_per_room,
            'surplus_teachers_per_room': self.surplus_teachers_per_room
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Configuration':
        """Create Configuration from dictionary"""
        config = cls()
        if isinstance(data, dict) and 'grade_hours' in data:
            # New format with grade_hours, teachers_per_room, and surplus_teachers_per_room
            config.grade_hours = dict(data.get('grade_hours', {}))
            config.teachers_per_room = data.get('teachers_per_room', 2)
            config.surplus_teachers_per_room = data.get('surplus_teachers_per_room', 0.5)
        else:
            # Legacy format - assume data is just grade_hours
            config.grade_hours = dict(data)
            config.teachers_per_room = 2
            config.surplus_teachers_per_room = 0.5
        return config
    
    def __str__(self) -> str:
        """String representation of the configuration"""
        result = "Configuration:\n"
        result += f"Teachers per room: {self.teachers_per_room}\n"
        result += f"Surplus teachers per room: {self.surplus_teachers_per_room}\n"
        
        if not self.grade_hours:
            result += "No grades configured\n"
        else:
            result += "Grade Hours Configuration:\n"
            for grade in sorted(self.grade_hours.keys()):
                hours = self.grade_hours[grade]
                result += f"  {grade}: {hours} hours\n"
            result += f"Total configured grades: {len(self.grade_hours)}\n"
            result += f"Total hours: {sum(self.grade_hours.values())}"
        return result


# Example usage
if __name__ == "__main__":
    from enseignants import Enseignants
    from seances import Seances
    
    # Load enseignants data
    enseignants = Enseignants.from_csv('data/enseignants.csv')
    
    # Create configuration
    config = Configuration()
    
    # Set teachers per room
    config.set_teachers_per_room(2)
    
    # Set some grade hours
    config.set_grade_hours('PR', 8)
    config.set_grade_hours('MCF', 6)
    config.set_grade_hours('ATER', 4)
    
    print("Configuration:")
    print(config)
    print()
    
    # Check configuration status
    summary = config.get_configuration_summary(enseignants)
    print("Configuration Summary:")
    print(f"Total grades in system: {summary['total_grades_in_system']}")
    print(f"Total configured grades: {summary['total_configured_grades']}")
    print(f"Is fully configured: {summary['is_fully_configured']}")
    print(f"Missing grades: {summary['missing_grades']}")
    print(f"Extra grades: {summary['extra_grades']}")
    print(f"Total hours configured: {summary['total_hours_configured']}")
    print(f"Teachers per room: {summary['teachers_per_room']}")
    print()
    
    # Check individual grades
    grade_status = config.check_all_grades_configured(enseignants)
    print("Grade-by-grade status:")
    for grade, is_configured in grade_status.items():
        status = "✓" if is_configured else "✗"
        hours = config.get_grade_hours(grade)
        print(f"  {status} {grade}: {hours} hours")
    print()
    
    # Load and analyze seances
    try:
        seances = Seances.from_csv('data/seances.csv')
        print("Teacher Requirements Analysis:")
        requirements = config.calculate_teacher_requirements(seances)
        
        total_teachers_needed = 0
        for (day, seance_num), teachers_needed in requirements.items():
            print(f"Day {day}, S{seance_num}: {teachers_needed} teachers needed")
            total_teachers_needed += teachers_needed
        
        print(f"\nTotal teacher-hours needed: {total_teachers_needed}")
        available_teachers = len(enseignants.get_enseignants_participating_surveillance())
        print(f"Available teachers: {available_teachers}")
        
        if available_teachers > 0:
            avg_hours_per_teacher = total_teachers_needed / available_teachers
            print(f"Average hours per teacher: {avg_hours_per_teacher:.1f}")
    except FileNotFoundError:
        print("Seances CSV file not found - skipping teacher requirements analysis")