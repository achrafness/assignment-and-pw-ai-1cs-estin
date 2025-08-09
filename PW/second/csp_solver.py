class Course:
    def __init__(self, name, teacher, has_lecture=True, has_td=True, has_tp=False, 
                 tp_teachers=None, td_teacher=None):
        self.name = name
        self.teacher = teacher
        self.has_lecture = has_lecture
        self.has_td = has_td
        self.has_tp = has_tp
        self.tp_teachers = tp_teachers if tp_teachers else [self.teacher]
        self.td_teacher = td_teacher if td_teacher else self.teacher
        self.groups = ["Group 01", "Group 02", "Group 03", "Group 04", "Group 05"]

class TimeSlot:
    def __init__(self, day, slot):
        self.day = day
        self.slot = slot

    # Overrides the equality operator 
    def __eq__(self, other):
        return self.day == other.day and self.slot == other.slot

    # use hash based on day and slot
    def __hash__(self):
        return hash((self.day, self.slot))

    # Overrides the string representation of the object
    def __str__(self):
        return f"{self.day} - Slot {self.slot}"

class Session:
    def __init__(self, course, session_type, teacher, group=None):
        self.course = course
        self.session_type = session_type  
        self.teacher = teacher
        self.group = group  
        self.assigned_slot = None

    # String representation 
    def __str__(self):
        group_str = f" ({self.group})" if self.group else ""
        return f"{self.course.name} ({self.session_type}{group_str}) - {self.teacher}"

class CSPSolver:
    def __init__(self):
        # C1: Only 5 working days defined
        self.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        # C2: Tuesday has only 3 slots, others have 5
        self.slots_per_day = {"Sunday": 5, "Monday": 5, "Tuesday": 3, "Wednesday": 5, "Thursday": 5}
        self.sessions = []
        self.domains = {}
        self.courses = self.initialize_courses()

    def initialize_courses(self):
        courses = [
            Course("Sécurité", "Teacher 1"),
            Course("Méthodes formelles", "Teacher 2"),
            Course("Analyse numérique", "Teacher 3"),
            Course("Entrepreneuriat", "Teacher 4", has_td=False),
            Course("Recherche opérationnelle 2", "Teacher 5"),
            Course("Distributed Architecture & Intensive Computing", "Teacher 6"),
            Course("Réseaux 2", "Teacher 7", has_tp=True, td_teacher="Teacher 7A"),
            Course("Artificial Intelligence", "Teacher 11", has_tp=True, tp_teachers=["Teacher 12", "Teacher 13", "Teacher 14"])
        ]
        return courses

    def initialize_sessions(self):
        self.sessions = []
        for course in self.courses:
            if course.has_lecture:
                self.sessions.append(Session(course, "lecture", course.teacher))
            
            if course.has_td:
                for group in course.groups:
                    self.sessions.append(Session(course, "td", course.td_teacher, group))
            
            if course.has_tp:
                for i, group in enumerate(course.groups):
                    teacher_index = i % len(course.tp_teachers)
                    tp_teacher = course.tp_teachers[teacher_index]
                    self.sessions.append(Session(course, "tp", tp_teacher, group))
        return self.sessions
    
    def initialize_domains(self):
        # For each session, initialize its domain (possible timeslots)
        self.domains = {}
        for session in self.sessions:
            domain = []
            for day in self.days:
                for slot in range(1, self.slots_per_day[day] + 1):
                    domain.append(TimeSlot(day, slot))
            self.domains[session] = domain
        print("Initial domains:")
        for session, domain in self.domains.items():
            print(f"{session}: {[str(slot) for slot in domain]}")
        return self.domains

    def ac3(self):
        queue = [(xi, xj) for xi in self.sessions for xj in self.sessions if xi != xj]
        while queue:
            (xi, xj) = queue.pop(0)
            if self.revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False
                for xk in [x for x in self.sessions if x != xi and x != xj]:
                    queue.append((xk, xi))  
                    

        return True

    def revise(self, xi, xj):
        revised = False
        to_remove = []
        
        for time_slot_i in self.domains[xi]:
            if not any(self.is_consistent(xi, time_slot_i, xj, time_slot_j) 
                        for time_slot_j in self.domains[xj]):
                to_remove.append(time_slot_i)
                revised = True
        
        for time_slot in to_remove:
            self.domains[xi].remove(time_slot)
        
        return revised

    def is_consistent(self, session_i, time_slot_i, session_j, time_slot_j):
        if time_slot_i == time_slot_j:
            # C5: Prevent same group having two courses at same time
            if session_i.group and session_j.group and session_i.group == session_j.group:
                return False
            # Prevent same teacher teaching two sessions at same time
            if session_i.teacher == session_j.teacher:
                return False
            # Prevent lectures overlapping with any other session
            if session_i.session_type == "lecture" or session_j.session_type == "lecture":
                return False

        # C4: Prevent same course having multiple sessions in same slot
        if (session_i.course == session_j.course and 
            session_i.session_type == session_j.session_type and 
            session_i.group == session_j.group and
            time_slot_i.slot == time_slot_j.slot):
            return False

        return True

    def backtracking_search(self):
        # Implement backtracking search
        return self.backtrack({})

    def backtrack(self, assignment):
        if len(assignment) == len(self.sessions):
            return assignment
        
        unassigned = [var for var in self.sessions if var not in assignment]
        var = min(unassigned, key=lambda var: len(self.domains[var]))
        
        for value in self.order_domain_values(var, assignment):
            if self.is_value_consistent(var, value, assignment):
                assignment[var] = value
                var.assigned_slot = value

                # C3: Check for 4+ consecutive slots
                if not self.check_consecutive_sessions(assignment):
                    del assignment[var]
                    var.assigned_slot = None
                    continue
                
                result = self.backtrack(assignment)
                if result:
                    return result
                
                del assignment[var]
                var.assigned_slot = None
        
        return False

    def order_domain_values(self, var, assignment):
        # LCV heuristic: order domain values by how constraining they are
        def count_conflicts(value):
            conflicts = 0
            for other_var in self.sessions:
                if other_var != var and other_var not in assignment:
                    for other_value in self.domains[other_var]:
                        if not self.is_consistent(var, value, other_var, other_value):
                            conflicts += 1
            return conflicts
        
        return sorted(self.domains[var], key=count_conflicts)

    def is_value_consistent(self, var, value, assignment):
        for other_var, other_value in assignment.items():
            if not self.is_consistent(var, value, other_var, other_value):
                return False
        return True

    # C3
    def check_consecutive_sessions(self, assignment):
        # Track slots by teacher
        teacher_slots = {}
        # Track slots by group
        group_slots = {}
        
        for session, time_slot in assignment.items():
            # Track by teacher
            teacher = session.teacher
            if teacher not in teacher_slots:
                teacher_slots[teacher] = {}
            
            day = time_slot.day
            if day not in teacher_slots[teacher]:
                teacher_slots[teacher][day] = []
            
            teacher_slots[teacher][day].append(time_slot.slot)
            
            # Track by group
            if session.group:
                group = session.group
                if group not in group_slots:
                    group_slots[group] = {}
                
                if day not in group_slots[group]:
                    group_slots[group][day] = []
                
                group_slots[group][day].append(time_slot.slot)
        
        # Check teacher consecutive slots
        for teacher, days in teacher_slots.items():
            for day, slots in days.items():
                slots.sort()
                consecutive = 1
                for i in range(1, len(slots)):
                    if slots[i] == slots[i-1] + 1:
                        consecutive += 1
                        if consecutive > 3:
                            return False
                    else:
                        consecutive = 1
        
        # Check group consecutive slots
        for group, days in group_slots.items():
            for day, slots in days.items():
                slots.sort()
                consecutive = 1
                for i in range(1, len(slots)):
                    if slots[i] == slots[i-1] + 1:
                        consecutive += 1
                        if consecutive > 3:
                            return False
                    else:
                        consecutive = 1
        
        # Also check for global consecutive slots (students in general)
        all_slots_by_day = {}
        for session, time_slot in assignment.items():
            if session.session_type == "lecture":  # Lectures affect all students
                day = time_slot.day
                if day not in all_slots_by_day:
                    all_slots_by_day[day] = set()
                all_slots_by_day[day].add(time_slot.slot)
        
        # For each group, add their specific sessions
        for group in group_slots:
            for day, slots in group_slots[group].items():
                if day not in all_slots_by_day:
                    all_slots_by_day[day] = set()
                for slot in slots:
                    all_slots_by_day[day].add(slot)
        
        # Check for consecutive global slots
        for day, slots_set in all_slots_by_day.items():
            slots = sorted(list(slots_set))
            consecutive = 1
            for i in range(1, len(slots)):
                if slots[i] == slots[i-1] + 1:
                    consecutive += 1
                    if consecutive > 3:
                        return False
                else:
                    consecutive = 1
        
        return True

    def solve(self):
        self.initialize_sessions()
        self.initialize_domains()
        self.ac3()
        solution = self.backtracking_search()
        
        if solution:
            # Convert solution to a readable timetable
            timetable = {day: {slot: [] for slot in range(1, self.slots_per_day[day] + 1)} for day in self.days}
            
            # Process lectures first (common to all groups)
            for session, time_slot in solution.items():
                if session.session_type == "lecture":
                    timetable[time_slot.day][time_slot.slot].append({
                        'course': session.course.name,
                        'type': "lecture",
                        'teacher': session.teacher
                    })
            
            # Then process group-specific sessions (TD and TP)
            for session, time_slot in solution.items():
                if session.session_type != "lecture":
                    group_str = f" ({session.group})" if session.group else ""
                    timetable[time_slot.day][time_slot.slot].append({
                        'course': session.course.name,
                        'type': f"{session.session_type}{group_str}",
                        'teacher': session.teacher
                    })
            
            return timetable
        
        return None