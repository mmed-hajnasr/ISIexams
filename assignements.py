from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enseignants import Enseignants, Enseignant
from seances import Seances, Seance
from configuration import Configuration
from ortools.sat.python import cp_model


@dataclass
class Assignements:
    """Manages teacher assignments to exam sessions"""
    
    # Core data structures
    enseignants: Enseignants
    seances: Seances
    configuration: Configuration
    
    # Assignment data: (day, seance) -> list of assigned teacher IDs
    assignments: Dict[Tuple[int, int], List[int]] = field(default_factory=dict)
    
    # Requirements: (day, seance) -> number of teachers needed
    requirements: Dict[Tuple[int, int], int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the assignment structure"""
        self._initialize_requirements()
        self._initialize_assignments()
    
    def _initialize_requirements(self):
        """Calculate and store teacher requirements for each seance using F = teachers_per_room + surplus_teacher_per_room"""
        import math
        
        # Calculate F = teachers_per_room + surplus_teacher_per_room
        F = self.configuration.teachers_per_room + self.configuration.surplus_teachers_per_room
        
        for day_idx, date in enumerate(self.seances.dates, 1):
            date_seances = self.seances.get_seances_by_date(date)
            for seance_idx, seance in enumerate(date_seances, 1):
                num_rooms = len(seance.salles)
                # Use ceiling(Rj * F) as the maximum teachers for this seance
                max_teachers = math.ceil(num_rooms * F)
                self.requirements[(day_idx, seance_idx)] = max_teachers
    
    def _initialize_assignments(self):
        """Initialize empty assignments for all seances that don't have assignments yet"""
        for seance_key in self.requirements.keys():
            if seance_key not in self.assignments:
                self.assignments[seance_key] = []
    
    def assign_teacher_to_seance(self, day: int, seance: int, teacher_id: int, force_unavailable: bool = False) -> Dict[str, any]:
        """
        Manually assign a teacher to a specific seance.
        
        Args:
            day: Day number (1-based)
            seance: Seance number (1-based)
            teacher_id: Teacher ID to assign
            force_unavailable: If True, allow assignment even when teacher is unavailable
            
        Returns:
            Dictionary with assignment result and conflict information
        """
        seance_key = (day, seance)
        
        # Validate inputs
        if seance_key not in self.requirements:
            return {"success": False, "error": "Invalid seance"}
        
        teacher = self.enseignants.get_enseignant_by_code(teacher_id)
        if not teacher or not teacher.participe_surveillance:
            return {"success": False, "error": "Teacher not found or not participating"}
        
        # Check if teacher has quota remaining
        current_surveillances = self.get_teacher_total_surveillances(teacher_id)
        quota = self.get_teacher_quota(teacher_id)
        if current_surveillances >= quota:
            return {"success": False, "error": "Teacher quota exceeded"}
        
        # Check if teacher is already assigned to this seance
        current_assignments = self.assignments[seance_key]
        if teacher_id in current_assignments:
            return {"success": False, "error": "Teacher already assigned"}
        
        # Check availability
        is_available = teacher.is_available(day, seance)
        if not is_available and not force_unavailable:
            return {"success": False, "error": "Teacher unavailable", "is_conflict": True}
        
        # Add assignment (allow over-assignment beyond required number)
        self.assignments[seance_key].append(teacher_id)
        
        return {
            "success": True, 
            "is_conflict": not is_available,
            "teacher_name": f"{teacher.prenom} {teacher.nom}"
        }
    
    def remove_teacher_from_seance(self, day: int, seance: int, teacher_id: int) -> bool:
        """
        Remove a teacher from a specific seance.
        
        Args:
            day: Day number (1-based)
            seance: Seance number (1-based)
            teacher_id: Teacher ID to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        seance_key = (day, seance)
        
        if seance_key not in self.assignments:
            return False
        
        if teacher_id in self.assignments[seance_key]:
            self.assignments[seance_key].remove(teacher_id)
            return True
        
        return False
    
    def get_teacher_total_surveillances(self, teacher_id: int) -> int:
        """Calculate total assigned surveillances for a teacher"""
        total_surveillances = 0
        for assignments in self.assignments.values():
            if teacher_id in assignments:
                total_surveillances += 1
        return total_surveillances
    
    def get_teacher_quota(self, teacher_id: int) -> int:
        """Get the maximum surveillances a teacher can be assigned based on their grade"""
        teacher = self.enseignants.get_enseignant_by_code(teacher_id)
        if not teacher:
            return 0
        # Return surveillance count quota based on grade configuration
        return self.configuration.get_grade_hours(teacher.grade)
    
    def get_all_conflicts(self) -> List[Dict[str, any]]:
        """Get all assignment conflicts (teachers assigned to unavailable seances) - Dynamic check"""
        conflicts_list = []
        
        # Dynamically check all assignments for conflicts
        for (day, seance), teacher_ids in self.assignments.items():
            for teacher_id in teacher_ids:
                teacher = self.enseignants.get_enseignant_by_code(teacher_id)
                if teacher and not teacher.is_available(day, seance):
                    conflicts_list.append({
                        'day': day,
                        'seance': seance,
                        'teacher_id': teacher_id,
                        'teacher_name': f"{teacher.prenom} {teacher.nom}",
                        'teacher_email': teacher.email,
                        'grade': teacher.grade
                    })
        
        return conflicts_list
    
    def is_assignment_conflict(self, day: int, seance: int, teacher_id: int) -> bool:
        """Check if a specific assignment is a conflict - Dynamic check"""
        # Check if teacher is assigned to this seance
        seance_key = (day, seance)
        if seance_key not in self.assignments or teacher_id not in self.assignments[seance_key]:
            return False
        
        # Check if teacher is available for this time slot
        teacher = self.enseignants.get_enseignant_by_code(teacher_id)
        if not teacher:
            return False
        
        return not teacher.is_available(day, seance)
    
    def auto_assign_teachers(self) -> Dict[str, any]:
        """
        Automatically assign teachers to seances using a two-phase approach:
        
        Phase 1: Calculate optimal assignments per grade using greedy algorithm
        Phase 2: Use OR-Tools CP-SAT solver for specific teacher assignments
        
        System based on:
        - N = total assignments needed = sum(ceiling(Rj * F)) for all seances
        - ni = number of teachers per grade i
        - Qi = quota per teacher in grade i
        - Si = optimal assignments per teacher in grade i (calculated in Phase 1)
        
        Hard constraints:
        1. Teachers must be assigned exactly Si assignments (based on their grade)
        2. Seances must have at least ceiling(Rj * F) teachers
        
        Soft constraints (priority order):
        3. HIGH: Assign responsible teachers to their seances
        4. MEDIUM: Avoid unavailable slots
        5. LOW: Prefer consecutive seances for same teacher
        
        Returns:
            Dictionary with assignment results and potential issues
        """
        import math
        
        # Configuration constants
        TIMEOUT_SECONDS = 60.0  # 1 minute timeout
        
        # Objective function weights (priority order)
        WEIGHT_RESPONSIBLE_TEACHERS = 100000  
        WEIGHT_AVAILABILITY_BONUS =   10000  
        WEIGHT_AVAILABILITY_PENALTY = -5000  
        WEIGHT_CONSECUTIVE =          1000 
        
        # Get participating teachers
        participating_teachers = [t for t in self.enseignants.enseignants_list if t.participe_surveillance and t.code is not None]
        teacher_ids = [t.code for t in participating_teachers]
        
        # Get all seances
        seance_keys = list(self.requirements.keys())
        
        if not teacher_ids or not seance_keys:
            return {
                'status': 'complete_success',
                'assignments_made': 0,
                'unsatisfied_seances': [],
                'message': 'No teachers or seances to assign.',
                'solver_status': 'TRIVIAL',
                'grade_assignments': {}
            }
        
        # Calculate F = teachers_per_room + surplus_teacher_per_room
        F = self.configuration.teachers_per_room + self.configuration.surplus_teachers_per_room
        
        # PHASE 1: Calculate total assignments needed (N)
        N = 0
        for seance_key in seance_keys:
            day, seance = seance_key
            date = self.seances.dates[day - 1]
            seances_for_date = self.seances.get_seances_by_date(date)
            if seance - 1 < len(seances_for_date):
                seance_obj = seances_for_date[seance - 1]
                room_count = len(seance_obj.salles)  # Rj
                max_teachers = math.ceil(room_count * F)
                current_assigned = len(self.assignments[seance_key])
                # Only count remaining capacity needed
                remaining_needed = max(0, max_teachers - current_assigned)
                N += remaining_needed
        
        # Group teachers by grade and calculate parameters
        grade_info = {}  # grade -> {'ni': count, 'Qi': quota, 'teachers': [teacher_ids], 'current_total': assignments}
        
        for teacher in participating_teachers:
            grade = teacher.grade
            teacher_id = teacher.code
            
            if grade not in grade_info:
                grade_info[grade] = {
                    'ni': 0,
                    'Qi': self.configuration.get_grade_hours(grade),
                    'teachers': [],
                    'current_total': 0
                }
            
            grade_info[grade]['ni'] += 1
            grade_info[grade]['teachers'].append(teacher_id)
            grade_info[grade]['current_total'] += self.get_teacher_total_surveillances(teacher_id)
        
        # PHASE 1: Calculate optimal Si per grade using greedy algorithm
        grade_assignments = {}  # grade -> Si (assignments per teacher in this grade)
        
        # Initialize all grades to 0 assignments
        for grade in grade_info.keys():
            grade_assignments[grade] = 0
        
        remaining = N
        
        # Greedy assignment: repeatedly assign to grade with lowest utilization ratio
        while remaining > 0:
            # Find grade with lowest current ratio Ai/Qi
            best_grade = None
            best_ratio = float('inf')
            
            for grade, info in grade_info.items():
                if info['Qi'] > 0:  # Only consider grades with positive quota
                    # Calculate current assignments per teacher in this grade
                    current_per_teacher = (info['current_total'] / info['ni']) if info['ni'] > 0 else 0
                    # Add planned assignments from our algorithm
                    planned_per_teacher = grade_assignments[grade]
                    total_per_teacher = current_per_teacher + planned_per_teacher
                    
                    ratio = total_per_teacher / info['Qi']
                    
                    # Only assign if we haven't exceeded quota
                    if total_per_teacher < info['Qi'] and ratio < best_ratio:
                        best_ratio = ratio
                        best_grade = grade
            
            if best_grade is None:
                # No grade can accept more assignments - break to avoid infinite loop
                break
            
            # Assign one more assignment to each teacher in the best grade
            grade_assignments[best_grade] += 1
            remaining -= grade_info[best_grade]['ni']
        
        # PHASE 2: Use OR-Tools to assign specific teachers based on calculated Si values
        model = cp_model.CpModel()
        
        # Decision variables: teacher_assigned[teacher_id][seance_key] = 1 if assigned
        teacher_assigned = {}
        for teacher_id in teacher_ids:
            teacher_assigned[teacher_id] = {}
            for seance_key in seance_keys:
                day, seance = seance_key
                teacher_assigned[teacher_id][seance_key] = model.NewBoolVar(f'teacher_{teacher_id}_day_{day}_seance_{seance}')
        
        # HARD CONSTRAINT 1: Teachers must be assigned exactly Si assignments (based on their grade)
        for teacher_id in teacher_ids:
            teacher = self.enseignants.get_enseignant_by_code(teacher_id)
            if not teacher:
                continue
            
            grade = teacher.grade
            target_assignments = grade_assignments.get(grade, 0)
            current_assigned = self.get_teacher_total_surveillances(teacher_id)
            
            # Calculate how many new assignments this teacher should get
            total_target = current_assigned + target_assignments
            quota = self.get_teacher_quota(teacher_id)
            
            # Don't exceed quota, but try to reach target
            new_assignments_needed = min(target_assignments, max(0, quota - current_assigned))
            
            if new_assignments_needed > 0:
                # Get all possible new assignments for this teacher
                possible_assignments = []
                for seance_key in seance_keys:
                    if teacher_id not in self.assignments[seance_key]:
                        possible_assignments.append(teacher_assigned[teacher_id][seance_key])
                
                if possible_assignments:
                    model.Add(sum(possible_assignments) == new_assignments_needed)
            else:
                # No new assignments needed/possible
                for seance_key in seance_keys:
                    if teacher_id not in self.assignments[seance_key]:
                        model.Add(teacher_assigned[teacher_id][seance_key] == 0)
        
        # HARD CONSTRAINT 2: Teachers cannot be assigned to slots where already assigned
        for teacher_id in teacher_ids:
            for seance_key in seance_keys:
                if teacher_id in self.assignments[seance_key]:
                    model.Add(teacher_assigned[teacher_id][seance_key] == 0)
        
        # HARD CONSTRAINT 3: Seances must have at least ceiling(Rj * F) teachers
        for seance_key in seance_keys:
            day, seance = seance_key
            date = self.seances.dates[day - 1]
            seances_for_date = self.seances.get_seances_by_date(date)
            if seance - 1 < len(seances_for_date):
                seance_obj = seances_for_date[seance - 1]
                room_count = len(seance_obj.salles)  # Rj
                min_teachers = math.ceil(room_count * F)
                
                current_assigned = len(self.assignments[seance_key])
                remaining_needed = max(0, min_teachers - current_assigned)
                
                if remaining_needed > 0:
                    new_assignments = [teacher_assigned[teacher_id][seance_key] for teacher_id in teacher_ids 
                                     if teacher_id not in self.assignments[seance_key]]
                    if new_assignments:
                        model.Add(sum(new_assignments) >= remaining_needed)
        
        # OBJECTIVE FUNCTION with prioritized weights
        objective_terms = []
        
        # HIGH PRIORITY: Responsible teachers bonus
        responsible_mapping = self.seances.get_day_seance_teachers_mapping()
        for (day_idx, seance_idx), responsible_teachers in responsible_mapping.items():
            actual_day = day_idx + 1  # Convert from 0-based to 1-based
            actual_seance = seance_idx + 1  # Convert from 0-based to 1-based
            seance_key = (actual_day, actual_seance)
            
            if seance_key in seance_keys:
                for teacher_id in responsible_teachers:
                    if teacher_id in teacher_ids and teacher_id not in self.assignments[seance_key]:
                        objective_terms.append(teacher_assigned[teacher_id][seance_key] * WEIGHT_RESPONSIBLE_TEACHERS)
        
        # MEDIUM PRIORITY: Availability preference
        for teacher_id in teacher_ids:
            teacher = self.enseignants.get_enseignant_by_code(teacher_id)
            if not teacher:
                continue
            
            for seance_key in seance_keys:
                day, seance = seance_key
                if teacher_id not in self.assignments[seance_key]:
                    if teacher.is_available(day, seance):
                        # Bonus for available slots
                        objective_terms.append(teacher_assigned[teacher_id][seance_key] * WEIGHT_AVAILABILITY_BONUS)
                    else:
                        # Penalty for unavailable slots (but still allow if needed)
                        objective_terms.append(teacher_assigned[teacher_id][seance_key] * WEIGHT_AVAILABILITY_PENALTY)
        
        # LOW PRIORITY: Consecutive seances bonus
        for teacher_id in teacher_ids:
            teacher = self.enseignants.get_enseignant_by_code(teacher_id)
            if not teacher:
                continue
                
            for day in range(1, len(self.seances.dates) + 1):
                # Get seances for this day in order
                day_seances = [s for d, s in seance_keys if d == day]
                day_seances.sort()
                
                # Check consecutive pairs
                for i in range(len(day_seances) - 1):
                    seance1 = day_seances[i]
                    seance2 = day_seances[i + 1]
                    seance_key1 = (day, seance1)
                    seance_key2 = (day, seance2)
                    
                    if (seance_key1 in seance_keys and seance_key2 in seance_keys and
                        teacher_id not in self.assignments[seance_key1] and 
                        teacher_id not in self.assignments[seance_key2]):
                        
                        # Create consecutive variable
                        consecutive_var = model.NewBoolVar(f'consecutive_{teacher_id}_day_{day}_seance_{seance1}_{seance2}')
                        model.Add(consecutive_var <= teacher_assigned[teacher_id][seance_key1])
                        model.Add(consecutive_var <= teacher_assigned[teacher_id][seance_key2])
                        model.Add(consecutive_var >= teacher_assigned[teacher_id][seance_key1] + teacher_assigned[teacher_id][seance_key2] - 1)
                        
                        objective_terms.append(consecutive_var * WEIGHT_CONSECUTIVE)
        
        # Set objective to maximize
        if objective_terms:
            model.Maximize(sum(objective_terms))
        
        # Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = TIMEOUT_SECONDS
        status = solver.Solve(model)
        
        # Prepare results
        results = {
            'status': 'complete_success',
            'assignments_made': 0,
            'unsatisfied_seances': [],
            'message': '',
            'solver_status': 'UNKNOWN',
            'grade_assignments': grade_assignments,
            'total_needed': N
        }
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Apply the solution
            assignments_made = 0
            for teacher_id in teacher_ids:
                for seance_key in seance_keys:
                    if (teacher_id not in self.assignments[seance_key] and 
                        solver.Value(teacher_assigned[teacher_id][seance_key]) == 1):
                        day, seance = seance_key
                        # Force assignment even if unavailable (solver already considered penalties)
                        assignment_result = self.assign_teacher_to_seance(day, seance, teacher_id, force_unavailable=True)
                        if assignment_result['success']:
                            assignments_made += 1
            
            results['assignments_made'] = assignments_made
            results['solver_status'] = 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'
        else:
            results['solver_status'] = 'INFEASIBLE'
        
        # Always analyze seance satisfaction
        unsatisfied = []
        satisfied = []
        
        for seance_key in seance_keys:
            day, seance = seance_key
            date = self.seances.dates[day - 1]
            seances_for_date = self.seances.get_seances_by_date(date)
            if seance - 1 < len(seances_for_date):
                seance_obj = seances_for_date[seance - 1]
                room_count = len(seance_obj.salles)
                min_teachers = math.ceil(room_count * F)
                current = len(self.assignments[seance_key])
                
                if current < min_teachers:
                    unsatisfied.append({
                        'day': seance_key[0],
                        'seance': seance_key[1],
                        'required': min_teachers,
                        'assigned': current,
                        'missing': min_teachers - current
                    })
                else:
                    satisfied.append({
                        'day': seance_key[0],
                        'seance': seance_key[1],
                        'required': min_teachers,
                        'assigned': current
                    })
        
        results['unsatisfied_seances'] = unsatisfied
        results['satisfied_seances'] = satisfied
        results['total_seances'] = len(self.requirements)
        
        # Set status and message based on results
        if unsatisfied:
            results['status'] = 'partial_success'
            total_satisfied = len(satisfied)
            total_seances = len(self.requirements)
            results['message'] = f'Assignment partiel: {total_satisfied}/{total_seances} séances satisfaites. {results["assignments_made"]} nouveaux assignements effectués.'
        else:
            results['status'] = 'complete_success'
            results['message'] = f'Assignment automatique terminé avec succès. {results["assignments_made"]} assignements effectués. Toutes les séances sont satisfaites.'
        
        # Add grade assignment summary to message
        grade_summary = []
        for grade, si in grade_assignments.items():
            if si > 0:
                ni = grade_info[grade]['ni']
                total_for_grade = ni * si
                grade_summary.append(f"{grade}: {si} assignements/prof ({ni} profs, {total_for_grade} total)")
        
        if grade_summary:
            results['message'] += f"\n\nRépartition par grade: {'; '.join(grade_summary)}"
        
        return results
    
    def get_assignment_summary(self) -> Dict:
        """Get a comprehensive summary of current assignments"""
        summary = {
            'total_seances': len(self.requirements),
            'total_requirements': sum(self.requirements.values()),
            'total_assignments': sum(len(assignments) for assignments in self.assignments.values()),
            'fully_satisfied_seances': 0,
            'partially_satisfied_seances': 0,
            'unsatisfied_seances': 0,
            'teacher_utilization': {},
            'seance_details': []
        }
        
        # Analyze seance satisfaction
        for seance_key, required in self.requirements.items():
            assigned = len(self.assignments[seance_key])
            
            # Check for conflicts in this seance
            has_conflicts = False
            for teacher_id in self.assignments[seance_key]:
                if self.is_assignment_conflict(seance_key[0], seance_key[1], teacher_id):
                    has_conflicts = True
                    break
            
            seance_detail = {
                'day': seance_key[0],
                'seance': seance_key[1],
                'required': required,
                'assigned': assigned,
                'teachers': self.assignments[seance_key].copy(),
                'is_complete': assigned >= required,
                'is_over_assigned': assigned > required,
                'has_conflicts': has_conflicts
            }
            summary['seance_details'].append(seance_detail)
            
            if assigned >= required:
                summary['fully_satisfied_seances'] += 1
            elif assigned > 0:
                summary['partially_satisfied_seances'] += 1
            else:
                summary['unsatisfied_seances'] += 1
        
        # Analyze teacher utilization
        for teacher in self.enseignants.get_enseignants_participating_surveillance():
            if teacher.code is None:
                continue
            
            teacher_id = teacher.code
            assigned_surveillances = self.get_teacher_total_surveillances(teacher_id)
            quota = self.get_teacher_quota(teacher_id)
            
            summary['teacher_utilization'][teacher_id] = {
                'name': f"{teacher.prenom} {teacher.nom}",
                'grade': teacher.grade,
                'assigned_surveillances': assigned_surveillances,
                'quota': quota,
                'utilization_rate': (assigned_surveillances / quota * 100) if quota > 0 else 0
            }
        
        return summary
    
    def __str__(self) -> str:
        """String representation of assignments"""
        result = "=== TEACHER ASSIGNMENTS ===\n\n"
        
        summary = self.get_assignment_summary()
        
        result += f"Overall Status:\n"
        result += f"  Total seances: {summary['total_seances']}\n"
        result += f"  Total teacher positions needed: {summary['total_requirements']}\n"
        result += f"  Total assignments made: {summary['total_assignments']}\n"
        result += f"  Fully satisfied: {summary['fully_satisfied_seances']}\n"
        result += f"  Partially satisfied: {summary['partially_satisfied_seances']}\n"
        result += f"  Unsatisfied: {summary['unsatisfied_seances']}\n\n"
        
        # Show seance assignments
        result += "Seance Assignments:\n"
        for detail in summary['seance_details']:
            if detail['assigned'] >= detail['required']:
                status = "✓"
                if detail['is_over_assigned']:
                    status += "+"  # Indicate over-assignment
            else:
                status = "✗"
            result += f"  {status} Day {detail['day']}, S{detail['seance']}: {detail['assigned']}/{detail['required']} teachers"
            if detail['teachers']:
                teacher_names = []
                for teacher_id in detail['teachers']:
                    teacher = self.enseignants.get_enseignant_by_code(teacher_id)
                    if teacher:
                        teacher_names.append(f"{teacher.prenom} {teacher.nom}")
                result += f" ({', '.join(teacher_names)})"
            result += "\n"
        
        result += "\nTeacher Utilization:\n"
        for teacher_id, util in summary['teacher_utilization'].items():
            if util['assigned_surveillances'] > 0:  # Only show assigned teachers
                result += f"  {util['name']} ({util['grade']}): {util['assigned_surveillances']}/{util['quota']} surveillances ({util['utilization_rate']:.1f}%)\n"
        
        return result