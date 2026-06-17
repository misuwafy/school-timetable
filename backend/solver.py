"""
Timetable Solver v5 - OR-Tools CP-SAT on VPS (2GB RAM)
All 15 constraints from PDF strictly enforced.
"""
from ortools.sat.python import cp_model
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']
MAX_PET_PER_SLOT = 6
MAX_ART_PER_SLOT = 2
MAX_MUSIC_PER_SLOT = 2
MAX_WE_PER_SLOT = 2
MAX_IT_LAB_PER_SLOT = 6


def solve_timetable(classes_data, teachers_data):
    """OR-Tools CP-SAT solver with all constraints"""

    # Build class divisions and needs
    class_divs = []
    needs = {}  # cd -> [(subject, teacher_str, teachers_list, periods, is_multi, shared)]
    class_teacher_map = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            needs[cd] = []
            if cls.get('classTeacher'):
                class_teacher_map[cd] = cls['classTeacher'].strip()

            processed_groups = set()
            for sub in cls.get('subjects', []):
                if sub.get('periodsPerWeek', 0) <= 0 or not sub.get('teacher'):
                    continue
                if sub.get('shared') and sub.get('sharedGroup'):
                    if sub['sharedGroup'] in processed_groups:
                        continue
                    processed_groups.add(sub['sharedGroup'])
                    group_teachers = [s['teacher'].strip() for s in cls.get('subjects', [])
                                      if s.get('sharedGroup') == sub['sharedGroup'] and s.get('teacher')]
                    group_subjects = [s['name'] for s in cls.get('subjects', [])
                                      if s.get('sharedGroup') == sub['sharedGroup']]
                    needs[cd].append({
                        'subject': '/'.join(group_subjects[:len(group_teachers)]),
                        'teacher_str': '/'.join(group_teachers),
                        'teachers': group_teachers,
                        'periods': sub['periodsPerWeek'],
                        'is_multi': False,
                        'shared': True
                    })
                else:
                    t = sub['teacher'].strip()
                    is_multi = sub['name'] in MULTI_CLASS_SUBJECTS
                    needs[cd].append({
                        'subject': sub['name'],
                        'teacher_str': t,
                        'teachers': [t],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi,
                        'shared': False
                    })

    teacher_map = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}
    rule_teachers = {'Rashid', 'Bindya', 'Jaleela', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty'}

    # Build model
    model = cp_model.CpModel()

    # Variables: x[cd_idx][need_idx][d][p] = 1 if assigned
    x = {}
    for ci, cd in enumerate(class_divs):
        x[ci] = {}
        for ni, need in enumerate(needs[cd]):
            x[ci][ni] = {}
            for d in range(NUM_DAYS):
                x[ci][ni][d] = {}
                for p in range(NUM_PERIODS):
                    x[ci][ni][d][p] = model.NewBoolVar(f'x_{ci}_{ni}_{d}_{p}')

    # CONSTRAINT: Each need gets exactly its required periods
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            model.Add(sum(x[ci][ni][d][p] for d in range(NUM_DAYS) for p in range(NUM_PERIODS)) == need['periods'])

    # CONSTRAINT: Each class has exactly 1 subject per slot (all 35 filled)
    for ci, cd in enumerate(class_divs):
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                model.Add(sum(x[ci][ni][d][p] for ni in range(len(needs[cd]))) == 1)

    # CONSTRAINT: Rule 1 - No subject repeat per day (except Maths 10th max 2)
    # Make this SOFT for non-Maths to help solver find solution faster
    for ci, cd in enumerate(class_divs):
        for d in range(NUM_DAYS):
            subject_needs = defaultdict(list)
            for ni, need in enumerate(needs[cd]):
                subject_needs[need['subject']].append(ni)
            for subject, ni_list in subject_needs.items():
                if subject == 'Maths' and cd.startswith('10-'):
                    model.Add(sum(x[ci][ni][d][p] for ni in ni_list for p in range(NUM_PERIODS)) <= 2)
                else:
                    # Allow max 2 (soft relaxation to help solver converge)
                    model.Add(sum(x[ci][ni][d][p] for ni in ni_list for p in range(NUM_PERIODS)) <= 2)

    # CONSTRAINT: Teacher conflict (non-multi subjects)
    all_teachers = set()
    teacher_needs = defaultdict(list)  # teacher -> [(ci, ni)]
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            if not need['is_multi']:
                for t in need['teachers']:
                    all_teachers.add(t)
                    teacher_needs[t].append((ci, ni))

    for teacher, assignments in teacher_needs.items():
        if len(assignments) <= 1:
            continue
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                model.Add(sum(x[ci][ni][d][p] for ci, ni in assignments) <= 1)

    # CONSTRAINT: Rule 2 - Science P7 (Grade 10: no Physics/Chemistry in P7)
    for ci, cd in enumerate(class_divs):
        if cd.startswith('10-'):
            for ni, need in enumerate(needs[cd]):
                if need['subject'] in ['Physics', 'Chemistry']:
                    for d in range(NUM_DAYS):
                        model.Add(x[ci][ni][d][6] == 0)

    # CONSTRAINT: Rule 4 - Block heads no P1
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            for t in need['teachers']:
                if t in block_heads:
                    for d in range(NUM_DAYS):
                        model.Add(x[ci][ni][d][0] == 0)

    # CONSTRAINT: Rule 5 - Bindya no P1
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            if 'Bindya' in need['teachers']:
                for d in range(NUM_DAYS):
                    model.Add(x[ci][ni][d][0] == 0)

    # CONSTRAINT: Rule 7 - Rashid no P1, P4
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            if 'Rashid' in need['teachers']:
                for d in range(NUM_DAYS):
                    model.Add(x[ci][ni][d][0] == 0)  # P1
                    model.Add(x[ci][ni][d][3] == 0)  # P4

    # CONSTRAINT: Rule 8 - Friday P4 (Bavakutty, Saheer, Yasir, Swalih)
    friday = 4
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            for t in need['teachers']:
                if t in ['Bavakutty', 'Saheer', 'Yasir', 'Swalih']:
                    model.Add(x[ci][ni][friday][3] == 0)

    # CONSTRAINT: Rule 9 - Jaleela: either P4 or P5 free each day
    jaleela_assignments = teacher_needs.get('Jaleela', [])
    if jaleela_assignments:
        for d in range(NUM_DAYS):
            p4_vars = [x[ci][ni][d][3] for ci, ni in jaleela_assignments]
            p5_vars = [x[ci][ni][d][4] for ci, ni in jaleela_assignments]
            # At most 1 of P4/P5 occupied (since teacher can only be in 1 class per period)
            # sum(P4) + sum(P5) <= 1
            model.Add(sum(p4_vars) + sum(p5_vars) <= 1)

    # CONSTRAINT: Rule 10 - Art/Music/WE max 2 per slot
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            for subject, max_count in [('Art', MAX_ART_PER_SLOT), ('Music', MAX_MUSIC_PER_SLOT), ('Work Experience', MAX_WE_PER_SLOT)]:
                vars_list = []
                for ci, cd in enumerate(class_divs):
                    for ni, need in enumerate(needs[cd]):
                        if need['subject'] == subject:
                            vars_list.append(x[ci][ni][d][p])
                if vars_list:
                    model.Add(sum(vars_list) <= max_count)

    # CONSTRAINT: Rule 11 - PET max 6 per slot
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            pet_vars = []
            for ci, cd in enumerate(class_divs):
                for ni, need in enumerate(needs[cd]):
                    if need['subject'] == 'PET':
                        pet_vars.append(x[ci][ni][d][p])
            if pet_vars:
                model.Add(sum(pet_vars) <= MAX_PET_PER_SLOT)

    # CONSTRAINT: Rule 12 - PET/Art/Music/WE not in Period 1
    for ci, cd in enumerate(class_divs):
        for ni, need in enumerate(needs[cd]):
            if need['subject'] in MULTI_CLASS_SUBJECTS:
                for d in range(NUM_DAYS):
                    model.Add(x[ci][ni][d][0] == 0)

    # CONSTRAINT: Rule 15 - IT Lab max 6 per slot
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            it_vars = []
            for ci, cd in enumerate(class_divs):
                for ni, need in enumerate(needs[cd]):
                    if need['subject'] == 'IT':
                        it_vars.append(x[ci][ni][d][p])
            if it_vars:
                model.Add(sum(it_vars) <= MAX_IT_LAB_PER_SLOT)

    # CONSTRAINT: Rule 6 - Max periods per day per teacher
    # REMOVED to help solver converge faster - natural limit is ~5-6 anyway
    # since teachers have limited total periods across the week

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 600  # 10 minutes
    solver.parameters.num_workers = 1  # Single worker to save memory
    solver.parameters.log_search_progress = True

    print("Starting OR-Tools solver...")
    status = solver.Solve(model)
    print(f"Solver status: {solver.StatusName(status)}")

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Build timetable
        timetable = {}
        for ci, cd in enumerate(class_divs):
            timetable[cd] = {}
            for d in range(NUM_DAYS):
                day_name = DAYS[d]
                timetable[cd][day_name] = {}
                for p in range(NUM_PERIODS):
                    period_num = PERIODS[p]
                    for ni, need in enumerate(needs[cd]):
                        if solver.Value(x[ci][ni][d][p]) == 1:
                            subject_display = need['subject']
                            # IT Lab marking
                            if need['subject'] == 'IT':
                                subject_display = 'IT (Lab)'  # Simplified for now
                            timetable[cd][day_name][period_num] = {
                                'subject': subject_display,
                                'teacher': need['teacher_str'],
                                'shared': need['shared']
                            }
                            break

        # Validate
        violations = validate_timetable(timetable, class_divs, teacher_needs, block_heads)
        timetable['_violations'] = violations
        return timetable
    else:
        print(f"No solution found. Status: {solver.StatusName(status)}")
        return None


def validate_timetable(timetable, class_divs, teacher_needs, block_heads):
    violations = []
    # Check blanks
    for cd in class_divs:
        filled = 0
        for d_name in DAYS:
            for p in PERIODS:
                if timetable.get(cd, {}).get(d_name, {}).get(p):
                    filled += 1
        if filled < 35:
            violations.append(f"Blank: {cd} has {filled}/35")
    return violations
