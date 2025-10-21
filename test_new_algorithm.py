#!/usr/bin/env python3
"""
Test script to verify the new teacher assignment algorithm
"""

def test_greedy_assignment_algorithm():
    """Test the greedy assignment algorithm with a simple example"""
    
    # Example from your description:
    # Grade 1: n₁ = 10 teachers, Q₁ = 20 quota
    # Grade 2: n₂ = 8 teachers, Q₂ = 18 quota  
    # Grade 3: n₃ = 6 teachers, Q₃ = 15 quota
    # N = 150 total assignments needed
    
    grade_info = {
        'Grade 1': {'ni': 10, 'Qi': 20, 'current_total': 0},
        'Grade 2': {'ni': 8, 'Qi': 18, 'current_total': 0},
        'Grade 3': {'ni': 6, 'Qi': 15, 'current_total': 0}
    }
    
    N = 150
    
    # Initialize all grades to 0 assignments
    grade_assignments = {}
    for grade in grade_info.keys():
        grade_assignments[grade] = 0
    
    remaining = N
    
    print(f"Starting with N = {N} assignments to distribute")
    print(f"Grade info: {grade_info}")
    print()
    
    iteration = 0
    # Greedy assignment: repeatedly assign to grade with lowest utilization ratio
    while remaining > 0 and iteration < 50:  # Safety limit
        iteration += 1
        
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
            print(f"No grade can accept more assignments at iteration {iteration}")
            break
        
        # Assign one more assignment to each teacher in the best grade
        grade_assignments[best_grade] += 1
        remaining -= grade_info[best_grade]['ni']
        
        print(f"Iteration {iteration}: Assigned to {best_grade}, ratio = {best_ratio:.3f}, remaining = {remaining}")
    
    print()
    print("Final Results:")
    total_assigned = 0
    for grade, si in grade_assignments.items():
        ni = grade_info[grade]['ni']
        Qi = grade_info[grade]['Qi']
        total_for_grade = ni * si
        ratio = si / Qi if Qi > 0 else 0
        total_assigned += total_for_grade
        print(f"  {grade}: S_i = {si}, total = {ni} × {si} = {total_for_grade}, ratio = {ratio:.3f}")
    
    print(f"\nTotal assignments: {total_assigned} (needed: {N})")
    print(f"Success: {'✓' if total_assigned >= N else '✗'}")
    
    # Check balance
    ratios = []
    for grade, si in grade_assignments.items():
        Qi = grade_info[grade]['Qi']
        if Qi > 0:
            ratios.append(si / Qi)
    
    if ratios:
        max_ratio = max(ratios)
        min_ratio = min(ratios)
        print(f"Balance: max ratio = {max_ratio:.3f}, min ratio = {min_ratio:.3f}, diff = {max_ratio - min_ratio:.3f}")

if __name__ == "__main__":
    test_greedy_assignment_algorithm()
