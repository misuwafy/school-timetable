"""
Timetable Solver using Google OR-Tools CP-SAT
Guarantees: all classes filled (35 periods) + teacher rules enforced
"""
from ortools.sat.python import cp_model

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = len(DAYS)
NUM_PERIODS = len(PERIODS)

# Multi-class subjects (no teacher conflict)
MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']
MAX_PET_PER_SLOT = 5
MAX_ART_PER_SLOT = 2


def solve_timetable(classes_data, teachers_data):
    """
    classes_data: list of class dicts with keys: name, divisions, subjects, classTeacher, block, classType
        subjects: [{name, teacher, periodsPerWeek, shared, sharedGroup, teachers (list)}]
    teachers_data: list of teacher dicts with keys: name, maxPeriodsPerDay, isBlockHead
    
    Returns: dict of timetable {classDiv: {day: {period: {subject, teacher}}}} or None
    """
    model = cp_model.CpModel()

    # Build class-division list and their needs
    class_divs = []
    needs = {}  # classDiv -> [(subject, teacher_str, teachers_list, periods_needed, is_multi, shared)]

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            needs[cd] = []
            processed_groups = set()

            for sub in cls.get('subjects', []):
                if sub.get('periodsPerWeek', 0) <= 0:
                    continue
                if not sub.get('teacher'):
                    continue

                if sub.get('shared') and sub.get('sharedGroup'):
                    if sub['sharedGroup'] in processed_groups:
                        continue
                    processed_groups.add(sub['sharedGroup'])
                    # Find all teachers in this shared group
                    group_teachers = []
                    for s2 in cls.get('subjects', []):
                        if s2.get('sharedGroup') == sub['sharedGroup']:
                            group_teachers.append(s2['teacher'])
                    needs[cd].append({
                        'subject': '/'.join(set(t for s2 in cls['subjects'] if s2.get('sharedGroup') == sub['sharedGroup'] for t in [s2.get('name', '')])),
                        'teacher_str': '/'.join(group_teachers),
                        'teachers': group_teachers,
                        'periods': sub['periodsPerWeek'],
                        'is_multi': False,
                        'shared': True
                    })
                else:
                    is_multi = sub['name'] in MULTI_CLASS_SUBJECTS
                    needs[cd].append({
                        'subject': sub['name'],
                        'teacher_str': sub['teacher'],
                        'teachers': [sub['teacher']],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi,
                        'shared': False
                    })

    # Teacher lookup
    teacher_map = {t['name']: t for t in teachers_data}

    # Create variables: x[cd][need_idx][d][p] = 1 if subject is assigned to that slot
    x = {}
    for cd in class_divs:
        x[cd] = {}
        for ni, need in enumerate(needs[cd]):
            x[cd][ni] = {}
            for d in range(NUM_DAYS):
                x[cd][ni][d] = {}
                for p in range(NUM_PERIODS):
                    x[cd][ni][d][p] = model.NewBoolVar(f'x_{cd}_{ni}_{d}_{p}')

    # CONSTRAINT 1: Each subject gets exactly its required periods per week
    for cd in class_divs:
        for ni, need in enumerate(needs[cd]):
            model.Add(
                sum(x[cd][ni][d][p] for d in range(NUM_DAYS) for p in range(NUM_PERIODS))
                == need['periods']
            )

    # CONSTRAINT 2: Each class-division has exactly one subject per slot
    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                model.Add(
                    sum(x[cd][ni][d][p] for ni in range(len(needs[cd])))
                    == 1
                )

    # CONSTRAINT 3: No teacher conflict (except multi-class subjects)
    # For each teacher, for each time slot, they can only be in one class
    all_teachers = set()
    for cd in class_divs:
        for need in needs[cd]:
            if not need['is_multi']:
                for t in need['teachers']:
                    all_teachers.add(t)

    for teacher in all_teachers:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                # Find all (cd, ni) pairs where this teacher is involved (non-multi)
                teacher_slots = []
                for cd in class_divs:
                    for ni, need in enumerate(needs[cd]):
                        if not need['is_multi'] and teacher in need['teachers']:
                            teacher_slots.append(x[cd][ni][d][p])
                if len(teacher_slots) > 1:
                    model.Add(sum(teacher_slots) <= 1)

    # CONSTRAINT 4: PET max 5 per slot
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            pet_slots = []
            for cd in class_divs:
                for ni, need in enumerate(needs[cd]):
                    if need['subject'] == 'PET':
                        pet_slots.append(x[cd][ni][d][p])
            if pet_slots:
                model.Add(sum(pet_slots) <= MAX_PET_PER_SLOT)

    # CONSTRAINT 5: Art max 2 per slot
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            art_slots = []
            for cd in class_divs:
                for ni, need in enumerate(needs[cd]):
                    if need['subject'] == 'Art':
                        art_slots.append(x[cd][ni][d][p])
            if art_slots:
                model.Add(sum(art_slots) <= MAX_ART_PER_SLOT)

    # CONSTRAINT 6: Max same subject per day (2)
    for cd in class_divs:
        for ni, need in enumerate(needs[cd]):
            for d in range(NUM_DAYS):
                model.Add(sum(x[cd][ni][d][p] for p in range(NUM_PERIODS)) <= 2)

    # CONSTRAINT 7: Science subjects NOT in period 7 (hard), prefer not in 5,6
    for cd in class_divs:
        for ni, need in enumerate(needs[cd]):
            if need['subject'] in ['Physics', 'Chemistry', 'Biology']:
                # Hard: no period 7
                for d in range(NUM_DAYS):
                    model.Add(x[cd][ni][d][6] == 0)  # period 7 = index 6

    # CONSTRAINT 8: Teacher-specific restrictions
    for cd in class_divs:
        for ni, need in enumerate(needs[cd]):
            for teacher in need['teachers']:
                t = teacher.strip()

                # Rashid: no P1, P4 daily
                if t == 'Rashid':
                    for d in range(NUM_DAYS):
                        model.Add(x[cd][ni][d][0] == 0)  # P1
                        model.Add(x[cd][ni][d][3] == 0)  # P4

                # Bindya: no P1 daily
                if t == 'Bindya':
                    for d in range(NUM_DAYS):
                        model.Add(x[cd][ni][d][0] == 0)

                # Saheer & Yasir: no P4, P5 on Friday
                if t in ['Saheer', 'Yasir']:
                    friday_idx = 4  # Friday is index 4
                    model.Add(x[cd][ni][friday_idx][3] == 0)  # P4
                    model.Add(x[cd][ni][friday_idx][4] == 0)  # P5

                # Swalih, Fuaad, Bavakutty: no P4 on Friday
                if t in ['Swalih', 'Fuaad', 'Bavakutty']:
                    friday_idx = 4
                    model.Add(x[cd][ni][friday_idx][3] == 0)  # P4

                # Jaleela, Shafeedha: at most 1 of P4/P5 per day
                if t in ['Jaleela', 'Shafeedha']:
                    for d in range(NUM_DAYS):
                        # This teacher can have at most 1 period in P4+P5 combined across ALL their classes
                        pass  # Handled below as global constraint

    # CONSTRAINT 9: Feeding mothers - across ALL classes, max 1 of P4/P5 per day
    for fm in ['Jaleela', 'Shafeedha']:
        for d in range(NUM_DAYS):
            fm_p4_p5 = []
            for cd in class_divs:
                for ni, need in enumerate(needs[cd]):
                    if fm in need['teachers'] and not need['is_multi']:
                        fm_p4_p5.append(x[cd][ni][d][3])  # P4
                        fm_p4_p5.append(x[cd][ni][d][4])  # P5
            if fm_p4_p5:
                # At most (total_fm_classes - 1) in P4+P5, meaning at least 1 slot is free
                # Actually: among all P4 slots + all P5 slots for this teacher, 
                # either all P4 are 0 OR all P5 are 0
                # Simpler: sum of (P4 assignments) + sum of (P5 assignments) <= max possible in one period
                p4_vars = []
                p5_vars = []
                for cd in class_divs:
                    for ni, need in enumerate(needs[cd]):
                        if fm in need['teachers'] and not need['is_multi']:
                            p4_vars.append(x[cd][ni][d][3])
                            p5_vars.append(x[cd][ni][d][4])
                # Teacher can only be in 1 class per period (already constrained above)
                # So sum(p4_vars) <= 1 and sum(p5_vars) <= 1
                # We need: sum(p4_vars) + sum(p5_vars) <= 1 (either P4 or P5 free)
                if p4_vars or p5_vars:
                    model.Add(sum(p4_vars) + sum(p5_vars) <= 1)

    # CONSTRAINT 10: Max periods per day per teacher (6 default, 5 for non-IT)
    for teacher in all_teachers:
        t_info = teacher_map.get(teacher, {})
        max_per_day = t_info.get('maxPeriodsPerDay', 6)

        for d in range(NUM_DAYS):
            day_slots = []
            for cd in class_divs:
                for ni, need in enumerate(needs[cd]):
                    if teacher in need['teachers'] and not need['is_multi']:
                        day_slots.append(x[cd][ni][d][p] for p in range(NUM_PERIODS))
            flat_slots = [var for sublist in day_slots for var in (sublist if hasattr(sublist, '__iter__') else [sublist])]
            # Rebuild properly
            day_vars = []
            for cd in class_divs:
                for ni, need in enumerate(needs[cd]):
                    if teacher in need['teachers'] and not need['is_multi']:
                        for p in range(NUM_PERIODS):
                            day_vars.append(x[cd][ni][d][p])
            if day_vars:
                model.Add(sum(day_vars) <= max_per_day)

    # CONSTRAINT 11: Block heads no Period 1
    for cd in class_divs:
        for ni, need in enumerate(needs[cd]):
            for teacher in need['teachers']:
                t_info = teacher_map.get(teacher, {})
                if t_info.get('isBlockHead'):
                    for d in range(NUM_DAYS):
                        model.Add(x[cd][ni][d][0] == 0)

    # SOFT CONSTRAINT: Science prefer morning (periods 1-4)
    # Art prefer periods 6,7
    # Class teacher prefer period 1
    # (These are objectives, not hard constraints)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120  # 2 minute timeout
    solver.parameters.num_workers = 4

    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Build timetable from solution
        timetable = {}
        for cd in class_divs:
            timetable[cd] = {}
            for d in range(NUM_DAYS):
                day_name = DAYS[d]
                timetable[cd][day_name] = {}
                for p in range(NUM_PERIODS):
                    period_num = PERIODS[p]
                    for ni, need in enumerate(needs[cd]):
                        if solver.Value(x[cd][ni][d][p]) == 1:
                            timetable[cd][day_name][period_num] = {
                                'subject': need['subject'],
                                'teacher': need['teacher_str'],
                                'shared': need['shared']
                            }
                            break
        return timetable
    else:
        return None
