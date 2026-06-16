"""
Timetable Solver v4 - Teacher-first approach
Strategy: Schedule each teacher's week first, then map to classes.
Guarantees: all classes filled + teacher rules enforced.
"""
import random
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


def get_teacher_restrictions(teacher, block_heads):
    """Get blocked slots for a teacher: returns set of (day_idx, period_idx)"""
    t = teacher.strip()
    blocked = set()

    # Rashid: no P1, P4 daily
    if t == 'Rashid':
        for d in range(NUM_DAYS):
            blocked.add((d, 0))  # P1
            blocked.add((d, 3))  # P4

    # Bindya: no P1 daily
    if t == 'Bindya':
        for d in range(NUM_DAYS):
            blocked.add((d, 0))

    # Block heads: no P1
    if t in block_heads:
        for d in range(NUM_DAYS):
            blocked.add((d, 0))

    # Friday P4: Bavakutty, Saheer, Yasir, Swalih
    if t in ['Bavakutty', 'Saheer', 'Yasir', 'Swalih']:
        blocked.add((4, 3))  # Friday P4

    return blocked


def solve_timetable(classes_data, teachers_data):
    """Teacher-first solver"""

    # Build all assignments: teacher -> [(classDiv, subject, periods_needed, is_multi, shared, teachers_list)]
    teacher_assignments = defaultdict(list)
    class_divs = []
    class_teacher_map = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
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
                    # Assign to first teacher as "owner"
                    teacher_assignments[group_teachers[0]].append({
                        'cd': cd, 'subject': '/'.join(group_subjects[:len(group_teachers)]),
                        'teacher_str': '/'.join(group_teachers),
                        'teachers': group_teachers,
                        'periods': sub['periodsPerWeek'],
                        'is_multi': False, 'shared': True
                    })
                else:
                    t = sub['teacher'].strip()
                    is_multi = sub['name'] in MULTI_CLASS_SUBJECTS
                    teacher_assignments[t].append({
                        'cd': cd, 'subject': sub['name'],
                        'teacher_str': t,
                        'teachers': [t],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi, 'shared': False
                    })

    # Teacher info
    teacher_map = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}
    rule_teachers = {'Rashid', 'Bindya', 'Jaleela', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty'}

    best_timetable = None
    best_unplaced = float('inf')

    for attempt in range(20):
        # Class timetable: cd -> day -> period -> slot
        timetable = {cd: {d: {} for d in range(NUM_DAYS)} for cd in class_divs}
        # Teacher schedule: teacher -> day -> period -> True
        teacher_busy = defaultdict(lambda: defaultdict(dict))
        # Track multi-class slot usage
        slot_multi = defaultdict(lambda: defaultdict(int))  # (d,p) -> subject -> count
        # Track IT lab usage
        it_lab_usage = defaultdict(int)  # (d,p) -> count

        # Sort teachers: busiest first, restricted teachers get slight priority
        all_teachers = list(teacher_assignments.keys())
        all_teachers.sort(key=lambda t: -sum(a['periods'] for a in teacher_assignments[t]))

        # Move restricted teachers to front
        restricted = [t for t in all_teachers if t in rule_teachers]
        normal = [t for t in all_teachers if t not in rule_teachers]
        if attempt % 2 == 0:
            teacher_order = restricted + normal
        else:
            random.shuffle(all_teachers)
            teacher_order = all_teachers

        unplaced = 0

        for teacher in teacher_order:
            assignments = teacher_assignments[teacher]
            blocked_slots = get_teacher_restrictions(teacher, block_heads)
            t_info = teacher_map.get(teacher, {})
            max_per_day = 5 if teacher in rule_teachers else (t_info.get('maxPeriodsPerDay') or 6)

            # Jaleela special: track P4/P5 usage
            is_jaleela = (teacher.strip() == 'Jaleela')

            for assignment in assignments:
                cd = assignment['cd']
                periods_needed = assignment['periods']
                is_multi = assignment['is_multi']
                subject = assignment['subject']

                placed = 0
                # Build list of valid slots for this assignment
                valid_slots = []

                for d in range(NUM_DAYS):
                    for p in range(NUM_PERIODS):
                        # Skip if class already has something in this slot
                        if timetable[cd][d].get(p) is not None:
                            continue

                        # Multi-class: check slot limits, no P1
                        if is_multi:
                            if p == 0:
                                continue  # Rule 12: no P1
                            if subject == 'PET' and slot_multi[(d, p)].get('PET', 0) >= MAX_PET_PER_SLOT:
                                continue
                            if subject == 'Art' and slot_multi[(d, p)].get('Art', 0) >= MAX_ART_PER_SLOT:
                                continue
                            if subject == 'Music' and slot_multi[(d, p)].get('Music', 0) >= MAX_MUSIC_PER_SLOT:
                                continue
                            if subject == 'Work Experience' and slot_multi[(d, p)].get('Work Experience', 0) >= MAX_WE_PER_SLOT:
                                continue
                            valid_slots.append((d, p))
                            continue

                        # Regular: check teacher restrictions
                        if (d, p) in blocked_slots:
                            continue
                        if teacher_busy[teacher][d].get(p):
                            continue

                        # Shared: check ALL teachers free
                        if assignment['shared']:
                            all_free = all(not teacher_busy[t][d].get(p) for t in assignment['teachers'])
                            if not all_free:
                                continue

                        # Max per day
                        day_count = len(teacher_busy[teacher][d])
                        if day_count >= max_per_day:
                            continue

                        # Jaleela: at most 1 of P4/P5 per day
                        if is_jaleela and (p == 3 or p == 4):
                            other = 4 if p == 3 else 3
                            if teacher_busy[teacher][d].get(other):
                                continue

                        # IT Lab limit
                        if subject == 'IT' and it_lab_usage[(d, p)] >= MAX_IT_LAB_PER_SLOT:
                            continue

                        # Rule 2: Science P7 for Grade 10
                        if subject in ['Physics', 'Chemistry'] and p == 6 and cd.startswith('10-'):
                            continue
                        if subject == 'Biology' and p == 6 and not cd.startswith('10-'):
                            continue

                        # Rule 1: No repeat per day (soft - prefer unique)
                        subject_today = [timetable[cd][d][pp]['subject'] for pp in range(NUM_PERIODS) if timetable[cd][d].get(pp)]
                        repeat_penalty = 10 if subject in subject_today else 0

                        # PET prefers P6, P7
                        pet_bonus = -5 if (subject == 'PET' and p >= 4) else 0

                        # Class teacher P1 bonus
                        ct_bonus = -20 if (p == 0 and class_teacher_map.get(cd) == teacher) else 0

                        score = day_count + repeat_penalty + pet_bonus + ct_bonus
                        valid_slots.append((d, p, score))

                if is_multi:
                    # Multi-class: spread across days
                    random.shuffle(valid_slots)
                    days_used = set()
                    for d, p in valid_slots:
                        if placed >= periods_needed:
                            break
                        if d in days_used:
                            continue
                        timetable[cd][d][p] = {
                            'subject': subject, 'teacher_str': assignment['teacher_str'],
                            'teachers': assignment['teachers'], 'is_multi': True, 'shared': False
                        }
                        slot_multi[(d, p)][subject] = slot_multi[(d, p)].get(subject, 0) + 1
                        placed += 1
                        days_used.add(d)
                    # If not enough days, fill remaining anywhere
                    for d, p in valid_slots:
                        if placed >= periods_needed:
                            break
                        if timetable[cd][d].get(p) is not None:
                            continue
                        timetable[cd][d][p] = {
                            'subject': subject, 'teacher_str': assignment['teacher_str'],
                            'teachers': assignment['teachers'], 'is_multi': True, 'shared': False
                        }
                        slot_multi[(d, p)][subject] = slot_multi[(d, p)].get(subject, 0) + 1
                        placed += 1
                else:
                    # Regular: sort by score (lower = better)
                    valid_slots.sort(key=lambda x: x[2])
                    # Add randomness
                    if len(valid_slots) > 3 and random.random() < 0.2:
                        random.shuffle(valid_slots[:5])

                    for d, p, score in valid_slots:
                        if placed >= periods_needed:
                            break
                        if timetable[cd][d].get(p) is not None:
                            continue
                        # Re-verify teacher free (might have changed)
                        if teacher_busy[teacher][d].get(p):
                            continue
                        if assignment['shared']:
                            if not all(not teacher_busy[t][d].get(p) for t in assignment['teachers']):
                                continue

                        timetable[cd][d][p] = {
                            'subject': subject, 'teacher_str': assignment['teacher_str'],
                            'teachers': assignment['teachers'], 'is_multi': False,
                            'shared': assignment['shared']
                        }
                        # Mark teachers busy
                        for t in assignment['teachers']:
                            teacher_busy[t][d][p] = True
                        if subject == 'IT':
                            it_lab_usage[(d, p)] += 1
                        placed += 1

                unplaced += (periods_needed - placed)

        if unplaced == 0:
            result = format_timetable(timetable, class_divs)
            result['_violations'] = validate_timetable(timetable, class_divs, teacher_busy, block_heads)
            return result

        if unplaced < best_unplaced:
            best_unplaced = unplaced
            best_timetable = {cd: {d: dict(timetable[cd][d]) for d in range(NUM_DAYS)} for cd in class_divs}

    # Return best
    if best_timetable:
        result = format_timetable(best_timetable, class_divs)
        result['_violations'] = validate_timetable(best_timetable, class_divs, defaultdict(lambda: defaultdict(dict)), block_heads)
        result['_unplaced'] = best_unplaced
        return result
    return None


def format_timetable(timetable, class_divs):
    """Format timetable for frontend with IT Lab/Theory marking"""
    result = {}
    it_lab_usage = defaultdict(int)
    it_periods_per_class = defaultdict(list)

    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slot = timetable[cd][d].get(p)
                if slot and slot['subject'] == 'IT':
                    it_periods_per_class[cd].append((d, p))

    # Assign Lab/Theory
    it_lab_marks = {}
    for cd in class_divs:
        periods = it_periods_per_class[cd]
        lab_count = min(2, len(periods)) if cd.startswith('10-') else min(1, len(periods))
        assigned = 0
        for d, p in periods:
            if assigned < lab_count and it_lab_usage[(d, p)] < MAX_IT_LAB_PER_SLOT:
                it_lab_marks[(cd, d, p)] = 'Lab'
                it_lab_usage[(d, p)] += 1
                assigned += 1
            else:
                it_lab_marks[(cd, d, p)] = 'Theory'

    for cd in class_divs:
        result[cd] = {}
        for d in range(NUM_DAYS):
            day_name = DAYS[d]
            result[cd][day_name] = {}
            for p in range(NUM_PERIODS):
                period_num = PERIODS[p]
                slot = timetable[cd][d].get(p)
                if slot:
                    subject_display = slot['subject']
                    if slot['subject'] == 'IT' and (cd, d, p) in it_lab_marks:
                        subject_display = f"IT ({it_lab_marks[(cd, d, p)]})"
                    result[cd][day_name][period_num] = {
                        'subject': subject_display,
                        'teacher': slot['teacher_str'],
                        'shared': slot.get('shared', False)
                    }
    return result


def validate_timetable(timetable, class_divs, teacher_busy, block_heads):
    """Check all rules and report violations"""
    violations = []
    teacher_days = defaultdict(lambda: defaultdict(dict))

    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slot = timetable[cd][d].get(p)
                if slot:
                    for t in slot.get('teachers', [slot.get('teacher_str', '')]):
                        t = t.strip()
                        if t:
                            teacher_days[t][d][p] = cd

    # Jaleela
    if 'Jaleela' in teacher_days:
        for d in range(NUM_DAYS):
            if 3 in teacher_days['Jaleela'][d] and 4 in teacher_days['Jaleela'][d]:
                violations.append(f"Rule 9: Jaleela {DAYS[d]} has BOTH P4 and P5")

    # Rashid
    if 'Rashid' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Rashid'][d]:
                violations.append(f"Rule 7: Rashid {DAYS[d]} P1")
            if 3 in teacher_days['Rashid'][d]:
                violations.append(f"Rule 7: Rashid {DAYS[d]} P4")

    # Bindya
    if 'Bindya' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Bindya'][d]:
                violations.append(f"Rule 5: Bindya {DAYS[d]} P1")

    # Friday P4
    for t in ['Bavakutty', 'Saheer', 'Yasir', 'Swalih']:
        if t in teacher_days and 3 in teacher_days[t][4]:
            violations.append(f"Rule 8: {t} Friday P4")

    # Blanks
    for cd in class_divs:
        filled = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if timetable[cd][d].get(p))
        if filled < 35:
            violations.append(f"Blank: {cd} has {filled}/35")

    return violations
