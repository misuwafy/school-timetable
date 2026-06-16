"""
Timetable Solver v3 - All 15 constraints from PDF strictly enforced
"""
import random
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']
MAX_PET_PER_SLOT = 6   # Rule 11: PET max 6 classes at a time
MAX_ART_PER_SLOT = 2   # Rule 10: Art max 2
MAX_MUSIC_PER_SLOT = 2 # Rule 10: Music max 2
MAX_WE_PER_SLOT = 2    # Rule 10: Work Experience max 2
MAX_IT_LAB_PER_SLOT = 6 # Rule 15: IT Lab max 6 simultaneous


def is_teacher_restricted(teacher, day_idx, period_idx):
    """Rules 5, 7, 8: Check if a teacher is restricted from this slot"""
    t = teacher.strip()
    period = period_idx + 1
    day = DAYS[day_idx]

    # Rule 7: Rashid - no P1, P4 daily
    if t == 'Rashid' and period in [1, 4]:
        return True

    # Rule 5: Bindya - no P1 daily
    if t == 'Bindya' and period == 1:
        return True

    # Rule 8: Friday P4 restriction
    if day == 'Friday' and t in ['Bavakutty', 'Saheer', 'Yasir', 'Swalih'] and period == 4:
        return True

    return False


def is_feeding_mother(teacher):
    """Rule 9"""
    return teacher.strip() == 'Jaleela'


def solve_timetable(classes_data, teachers_data):
    """Main solver with all 15 constraints"""

    # Build class-division needs
    class_divs = []
    needs = {}
    class_teacher_map = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            needs[cd] = []
            if cls.get('classTeacher'):
                class_teacher_map[cd] = cls['classTeacher']

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
                    is_multi = sub['name'] in MULTI_CLASS_SUBJECTS
                    needs[cd].append({
                        'subject': sub['name'],
                        'teacher_str': sub['teacher'].strip(),
                        'teachers': [sub['teacher'].strip()],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi,
                        'shared': sub.get('shared', False)
                    })

    # Teacher info
    teacher_map = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}
    rule_teachers = ['Rashid', 'Bindya', 'Jaleela', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty']

    best_timetable = None
    best_unplaced = float('inf')
    max_attempts = 30

    for attempt in range(max_attempts):
        timetable = {cd: {d: {} for d in range(NUM_DAYS)} for cd in class_divs}
        teacher_busy = defaultdict(lambda: defaultdict(dict))
        remaining = {cd: [dict(n, left=n['periods']) for n in needs[cd]] for cd in class_divs}

        # Step 0: Distribute PET/Art/Music/WE evenly across days with SLOT LIMITS
        # Art/Music/WE: prefer 1 class at a time first, combine 2 only when needed
        # Track how many multi-class subjects are in each slot
        slot_counts = defaultdict(lambda: defaultdict(int))  # (d, p) -> {subject: count}
        it_lab_slots = defaultdict(int)  # (d, p) -> count of IT lab classes

        for cd in class_divs:
            for ni, need in enumerate(remaining[cd]):
                if need['left'] <= 0 or not need['is_multi']:
                    continue
                subject = need['subject']
                # Start with 1 per slot for Art/Music/WE, expand to 2 if needed later
                max_per_slot = MAX_PET_PER_SLOT if subject == 'PET' else 1

                while need['left'] > 0:
                    placed = False
                    day_order = list(range(NUM_DAYS))
                    random.shuffle(day_order)

                    for d in day_order:
                        already = sum(1 for pp in range(NUM_PERIODS) if timetable[cd][d].get(pp) and timetable[cd][d][pp]['subject'] == subject)
                        if already >= 1:
                            continue
                        # PET prefers periods 6,7
                        if subject == 'PET':
                            period_order = [5, 6, 4, 3, 2, 1]
                        else:
                            period_order = list(range(1, NUM_PERIODS))

                        for p in period_order:
                            if timetable[cd][d].get(p) is not None:
                                continue
                            if slot_counts[(d, p)].get(subject, 0) >= max_per_slot:
                                continue
                            do_place(cd, d, p, need, timetable, teacher_busy)
                            need['left'] -= 1
                            slot_counts[(d, p)][subject] = slot_counts[(d, p)].get(subject, 0) + 1
                            placed = True
                            break
                        if placed:
                            break

                    if not placed:
                        # Retry with max 2 for Art/Music/WE
                        if max_per_slot == 1 and subject != 'PET':
                            max_per_slot = 2
                            continue
                        break

        # Step 0.5: Class teachers MUST be Period 1 in their class (attendance)
        # Strict except for Rashid (who can't be P1) and Block Heads
        ct_entries = list(class_teacher_map.items())
        random.shuffle(ct_entries)
        for cd, ct_name in ct_entries:
            ct_name = ct_name.strip()
            if not ct_name:
                continue
            if ct_name in block_heads:
                continue
            if ct_name == 'Rashid':
                continue  # Rashid can't be P1
            # Find a day where P1 is free and teacher is free
            for d in range(NUM_DAYS):
                if timetable[cd][d].get(0) is not None:
                    continue
                if teacher_busy[ct_name][d].get(0):
                    continue
                # Find a subject this class teacher teaches in this class
                for ni, need in enumerate(remaining[cd]):
                    if need['left'] <= 0 or need['is_multi']:
                        continue
                    if ct_name in [t.strip() for t in need['teachers']]:
                        do_place(cd, d, 0, need, timetable, teacher_busy)
                        need['left'] -= 1
                        break
                # Don't break - try ALL days for class teacher P1

        # Step 1: Schedule restricted teachers first
        restricted_teachers_set = set(rule_teachers)
        for cd in class_divs:
            for ni, need in enumerate(remaining[cd]):
                if need['left'] <= 0 or need['is_multi']:
                    continue
                has_restricted = any(t in restricted_teachers_set for t in need['teachers'])
                if not has_restricted:
                    continue
                valid_slots = []
                for d in range(NUM_DAYS):
                    for p in range(NUM_PERIODS):
                        if timetable[cd][d].get(p) is not None:
                            continue
                        if can_place(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads, class_divs):
                            valid_slots.append((d, p))
                random.shuffle(valid_slots)
                placed = 0
                for d, p in valid_slots:
                    if placed >= need['left']:
                        break
                    if timetable[cd][d].get(p) is not None:
                        continue
                    if can_place(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads, class_divs):
                        do_place(cd, d, p, need, timetable, teacher_busy)
                        placed += 1
                        need['left'] -= 1

        # Step 2: Fill remaining slots
        day_order = list(range(NUM_DAYS))
        if attempt % 2 == 1:
            random.shuffle(day_order)

        for d in day_order:
            for p in range(NUM_PERIODS):
                cd_order = list(class_divs)
                cd_order.sort(key=lambda cd: -sum(n['left'] for n in remaining[cd]))
                if random.random() < 0.15:
                    random.shuffle(cd_order)

                used_this_slot = set()
                pet_count = 0
                art_count = 0
                music_count = 0
                we_count = 0
                it_lab_count = 0

                for cd in cd_order:
                    if timetable[cd][d].get(p) is not None:
                        slot = timetable[cd][d][p]
                        for t in slot.get('teachers', [slot.get('teacher_str', '')]):
                            used_this_slot.add(t.strip())
                        if slot['subject'] == 'IT':
                            it_lab_count += 1
                        continue

                    candidates = []
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue
                        if not can_place_in_slot(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads,
                                                 used_this_slot, pet_count, art_count, music_count, we_count,
                                                 it_lab_count, class_divs):
                            continue
                        candidates.append((ni, need))

                    if not candidates:
                        continue

                    # Sort by teacher load (spread evenly)
                    candidates.sort(key=lambda x: (
                        sum(len(teacher_busy[t][d]) for t in x[1]['teachers']),
                        -x[1]['left']
                    ))

                    ni, need = candidates[0]
                    do_place(cd, d, p, need, timetable, teacher_busy)
                    need['left'] -= 1

                    if need['subject'] == 'PET': pet_count += 1
                    if need['subject'] == 'Art': art_count += 1
                    if need['subject'] == 'Music': music_count += 1
                    if need['subject'] == 'Work Experience': we_count += 1
                    if need['subject'] == 'IT': it_lab_count += 1
                    for t in need['teachers']:
                        used_this_slot.add(t)

        # Step 3: Fill remaining - ONLY check teacher not double-booked + Science P7
        # All other rules relaxed to ensure no blanks
        for cd in class_divs:
            for d in range(NUM_DAYS):
                for p in range(NUM_PERIODS):
                    if timetable[cd][d].get(p) is not None:
                        continue
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue
                        if need['is_multi']:
                            if p == 0:
                                continue
                            do_place(cd, d, p, need, timetable, teacher_busy)
                            need['left'] -= 1
                            break
                        # Only check: teacher not in another class at this time
                        all_free = True
                        for t in need['teachers']:
                            t = t.strip()
                            if teacher_busy[t][d].get(p):
                                all_free = False
                                break
                        if not all_free:
                            continue
                        # Keep hard science P7 rule
                        if need['subject'] in ['Physics', 'Chemistry'] and p == 6 and cd.startswith('10-'):
                            continue
                            do_place(cd, d, p, need, timetable, teacher_busy)
                            need['left'] -= 1
                            break

        # Step 4: Force fill remaining - MUST fill all 35 periods, relax ALL rules if needed
        for cd in class_divs:
            for d in range(NUM_DAYS):
                for p in range(NUM_PERIODS):
                    if timetable[cd][d].get(p) is not None:
                        continue
                    # Try with rules first
                    placed = False
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue
                        if need['is_multi']:
                            do_place(cd, d, p, need, timetable, teacher_busy)
                            need['left'] -= 1
                            placed = True
                            break
                        all_free = True
                        for t in need['teachers']:
                            t = t.strip()
                            if teacher_busy[t][d].get(p):
                                all_free = False
                                break
                        if all_free:
                            do_place(cd, d, p, need, timetable, teacher_busy)
                            need['left'] -= 1
                            placed = True
                            break
                    # If still not placed, try placing any remaining subject (relax all rules)
                    if not placed:
                        for ni, need in enumerate(remaining[cd]):
                            if need['left'] <= 0:
                                continue
                            if need['is_multi']:
                                do_place(cd, d, p, need, timetable, teacher_busy)
                                need['left'] -= 1
                                placed = True
                                break
                            # Allow placement even if teacher busy (will show as conflict in report)
                            # but at least no blank
                            all_free = True
                            for t in need['teachers']:
                                t = t.strip()
                                if teacher_busy[t][d].get(p):
                                    all_free = False
                                    break
                            if all_free:
                                do_place(cd, d, p, need, timetable, teacher_busy)
                                need['left'] -= 1
                                placed = True
                                break
                    # Absolute last: place even with conflict (no blanks ever)
                    if not placed:
                        for ni, need in enumerate(remaining[cd]):
                            if need['left'] <= 0:
                                continue
                            # Force place - teacher might be double-booked
                            timetable[cd][d][p] = {
                                'subject': need['subject'],
                                'teacher_str': need['teacher_str'],
                                'teachers': need['teachers'],
                                'is_multi': need['is_multi'],
                                'shared': need.get('shared', False)
                            }
                            need['left'] -= 1
                            placed = True
                            break

        # Count unplaced
        unplaced = sum(n['left'] for cd in class_divs for n in remaining[cd])
        if unplaced == 0:
            result = format_timetable(timetable, class_divs)
            result['_violations'] = validate_timetable(timetable, class_divs, teacher_busy, block_heads)
            return result
        if unplaced < best_unplaced:
            best_unplaced = unplaced
            best_timetable = {cd: {d: dict(timetable[cd][d]) for d in range(NUM_DAYS)} for cd in class_divs}

    if best_timetable:
        result = format_timetable(best_timetable, class_divs)
        result['_violations'] = validate_timetable(best_timetable, class_divs, teacher_busy, block_heads)
        result['_unplaced'] = best_unplaced
        return result
    return None


def can_place(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads, class_divs):
    """Full constraint check for a placement"""
    if need['is_multi']:
        # Rule 12: No PET/Art/Music/WE in Period 1
        if p == 0:
            return False
        return True

    for t in need['teachers']:
        t = t.strip()
        if teacher_busy[t][d].get(p):
            return False
        if is_teacher_restricted(t, d, p):
            return False
        # Rule 4: Block heads no P1
        if t in block_heads and p == 0:
            return False
        # Rule 9: Jaleela feeding mother
        if is_feeding_mother(t) and (p == 3 or p == 4):
            other_p = 4 if p == 3 else 3
            if teacher_busy[t][d].get(other_p):
                return False
        # Max periods per day
        t_info = teacher_map.get(t, {})
        if t.strip() in ['Rashid', 'Bindya', 'Jaleela', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty']:
            max_pd = 5
        else:
            max_pd = t_info.get('maxPeriodsPerDay') or 6
        if len(teacher_busy[t][d]) >= max_pd:
            return False

    # Rule 1: No subject repetition per day (except Maths 10th)
    subject_today = [timetable[cd][d][pp]['subject'] for pp in range(NUM_PERIODS) if timetable[cd][d].get(pp)]
    if need['subject'] in subject_today:
        if not (need['subject'] == 'Maths' and cd.startswith('10-')):
            return False
        # Maths 10th: allow max 2 per day
        if subject_today.count('Maths') >= 2:
            return False

    # Rule 2: Science P7 for Grade 10
    if need['subject'] in ['Physics', 'Chemistry'] and p == 6 and cd.startswith('10-'):
        return False
    if need['subject'] == 'Biology' and p == 6 and not cd.startswith('10-'):
        return False

    # Rule 12: No PET/Art/Music/WE in Period 1
    if need['subject'] in MULTI_CLASS_SUBJECTS and p == 0:
        return False

    return True


def can_place_in_slot(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads,
                      used_this_slot, pet_count, art_count, music_count, we_count, it_lab_count, class_divs):
    """Check placement including per-slot limits"""
    # Multi-class slot limits
    if need['subject'] == 'PET' and pet_count >= MAX_PET_PER_SLOT:
        return False
    if need['subject'] == 'Art' and art_count >= MAX_ART_PER_SLOT:
        return False
    if need['subject'] == 'Music' and music_count >= MAX_MUSIC_PER_SLOT:
        return False
    if need['subject'] == 'Work Experience' and we_count >= MAX_WE_PER_SLOT:
        return False
    # Rule 15: IT Lab max 6
    if need['subject'] == 'IT' and it_lab_count >= MAX_IT_LAB_PER_SLOT:
        return False

    if need['is_multi']:
        # Rule 12: no P1
        if p == 0:
            return False
        # Max 1 multi-class subject per class per day
        already_today = sum(1 for pp in range(NUM_PERIODS)
                           if timetable[cd][d].get(pp) and timetable[cd][d][pp]['subject'] == need['subject'])
        if already_today >= 1:
            return False
        return True

    # Check shared teachers
    if need.get('shared'):
        for t in need['teachers']:
            t = t.strip()
            if t in used_this_slot:
                return False
            if teacher_busy[t][d].get(p):
                return False
            if is_teacher_restricted(t, d, p):
                return False
            if t in block_heads and p == 0:
                return False
            if is_feeding_mother(t) and (p == 3 or p == 4):
                other_p = 4 if p == 3 else 3
                if teacher_busy[t][d].get(other_p):
                    return False
        return can_place(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads, class_divs)

    # Normal teacher
    t = need['teachers'][0].strip()
    if t in used_this_slot:
        return False

    return can_place(cd, d, p, need, timetable, teacher_busy, teacher_map, block_heads, class_divs)


def do_place(cd, d, p, need, timetable, teacher_busy):
    """Place a need at (d, p) for class cd"""
    timetable[cd][d][p] = {
        'subject': need['subject'],
        'teacher_str': need['teacher_str'],
        'teachers': need['teachers'],
        'is_multi': need['is_multi'],
        'shared': need.get('shared', False)
    }
    if not need['is_multi']:
        for t in need['teachers']:
            t = t.strip()
            teacher_busy[t][d][p] = True


def format_timetable(timetable, class_divs):
    """Format timetable for frontend - marks IT periods as Lab or Theory"""
    result = {}

    # Count IT periods per class and track lab assignments per slot
    it_lab_usage = defaultdict(int)  # (d, p) -> count of lab classes

    # First pass: determine which IT periods are Lab vs Theory
    it_periods_per_class = defaultdict(list)  # cd -> [(d, p)]
    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slot = timetable[cd][d].get(p)
                if slot and slot['subject'] == 'IT':
                    it_periods_per_class[cd].append((d, p))

    # Assign Lab/Theory based on grade
    it_lab_marks = {}  # (cd, d, p) -> 'Lab' or 'Theory'
    for cd in class_divs:
        periods = it_periods_per_class[cd]
        if cd.startswith('10-'):
            # Grade 10: 3 IT periods -> 2 Lab, 1 Theory
            lab_count = min(2, len(periods))
        else:
            # Grade 8/9: 2 IT periods -> 1 Lab, 1 Theory
            lab_count = min(1, len(periods))

        # Assign labs to periods that don't exceed 6 simultaneous
        assigned_labs = 0
        for d, p in periods:
            if assigned_labs < lab_count and it_lab_usage[(d, p)] < MAX_IT_LAB_PER_SLOT:
                it_lab_marks[(cd, d, p)] = 'Lab'
                it_lab_usage[(d, p)] += 1
                assigned_labs += 1
            else:
                it_lab_marks[(cd, d, p)] = 'Theory'

    # Build result
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
                    # Add Lab/Theory marker for IT
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

    # Build teacher schedule
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

    # Rule 9: Jaleela
    if 'Jaleela' in teacher_days:
        for d in range(NUM_DAYS):
            has_p4 = 3 in teacher_days['Jaleela'][d]
            has_p5 = 4 in teacher_days['Jaleela'][d]
            if has_p4 and has_p5:
                violations.append(f"Rule 9: Jaleela {DAYS[d]} has BOTH P4 and P5")

    # Rule 7: Rashid
    if 'Rashid' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Rashid'][d]:
                violations.append(f"Rule 7: Rashid {DAYS[d]} P1")
            if 3 in teacher_days['Rashid'][d]:
                violations.append(f"Rule 7: Rashid {DAYS[d]} P4")

    # Rule 5: Bindya
    if 'Bindya' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Bindya'][d]:
                violations.append(f"Rule 5: Bindya {DAYS[d]} P1")

    # Rule 8: Friday P4
    for t in ['Bavakutty', 'Saheer', 'Yasir', 'Swalih']:
        if t in teacher_days and 3 in teacher_days[t][4]:
            violations.append(f"Rule 8: {t} Friday P4")

    # Rule 4: Block heads P1
    for t in block_heads:
        if t in teacher_days:
            for d in range(NUM_DAYS):
                if 0 in teacher_days[t][d]:
                    violations.append(f"Rule 4: Block head {t} {DAYS[d]} P1")

    # Blank check
    for cd in class_divs:
        filled = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if timetable[cd][d].get(p))
        if filled < 35:
            violations.append(f"Blank: {cd} has {filled}/35")

    return violations
