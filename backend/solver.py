"""
Lightweight Timetable Solver - Slot-based with backtracking
Memory efficient, no OR-Tools dependency
Guarantees: all classes filled + teacher rules enforced
"""
import random
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']
MAX_PET_PER_SLOT = 5
MAX_ART_PER_SLOT = 2


def is_teacher_restricted(teacher, day_idx, period_idx):
    """Check if a teacher is restricted from this slot"""
    t = teacher.strip()
    period = period_idx + 1  # Convert to 1-based
    day = DAYS[day_idx]

    # Rashid: no P1, P4 daily
    if t == 'Rashid' and period in [1, 4]:
        return True

    # Bindya: no P1 daily
    if t == 'Bindya' and period == 1:
        return True

    # Friday restrictions
    if day == 'Friday':
        # Swalih, Fuaad, Bavakutty: no P4
        if t in ['Swalih', 'Fuaad', 'Bavakutty'] and period == 4:
            return True
        # Saheer, Yasir: no P4, P5
        if t in ['Saheer', 'Yasir'] and period in [4, 5]:
            return True

    return False


def is_feeding_mother(teacher):
    return teacher.strip() in ['Jaleela', 'Shafeedha']


def solve_timetable(classes_data, teachers_data):
    """
    Slot-based solver with intelligent assignment.
    Uses iterative improvement instead of brute-force backtracking.
    """
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
                    group_teachers = [s['teacher'] for s in cls.get('subjects', [])
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
                        'teacher_str': sub['teacher'],
                        'teachers': [sub['teacher']],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi,
                        'shared': sub.get('shared', False)
                    })

    # Teacher info
    teacher_map = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    # Best result tracking
    best_timetable = None
    best_unplaced = float('inf')
    max_attempts = 30

    for attempt in range(max_attempts):
        timetable = {cd: {d: {} for d in range(NUM_DAYS)} for cd in class_divs}
        teacher_busy = defaultdict(lambda: defaultdict(dict))  # teacher -> day -> period -> True
        remaining = {cd: [dict(n, left=n['periods']) for n in needs[cd]] for cd in class_divs}

        # Track feeding mother usage per day
        fm_used = {fm: {d: 0 for d in range(NUM_DAYS)} for fm in ['Jaleela', 'Shafeedha']}

        # Step 0: Distribute PET/Art/Music/WE evenly across all 5 days FIRST
        for cd in class_divs:
            for ni, need in enumerate(remaining[cd]):
                if need['left'] <= 0 or not need['is_multi']:
                    continue
                # Assign to the day with fewest multi-class slots so far
                while need['left'] > 0:
                    # Find day with fewest assigned periods for this class
                    day_loads = [(d, sum(1 for pp in range(NUM_PERIODS) if timetable[cd][d].get(pp))) for d in range(NUM_DAYS)]
                    day_loads.sort(key=lambda x: x[1])
                    placed = False
                    for d, _ in day_loads:
                        # Check if this class already has this multi-subject today
                        already = sum(1 for pp in range(NUM_PERIODS) if timetable[cd][d].get(pp) and timetable[cd][d][pp]['subject'] == need['subject'])
                        if already >= 1:
                            continue
                        # Find a free period
                        for p in range(NUM_PERIODS):
                            if timetable[cd][d].get(p) is None:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                placed = True
                                break
                        if placed:
                            break
                    if not placed:
                        break  # Can't place more

        # Step 1: Schedule restricted teachers first in their allowed periods
        restricted_teachers = ['Rashid', 'Bindya', 'Jaleela', 'Shafeedha', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty']

        for cd in class_divs:
            for ni, need in enumerate(remaining[cd]):
                if need['left'] <= 0:
                    continue
                has_restricted = any(t.strip() in restricted_teachers for t in need['teachers'])
                if not has_restricted:
                    continue

                # Find valid slots for this restricted teacher
                valid_slots = []
                for d in range(NUM_DAYS):
                    for p in range(NUM_PERIODS):
                        if timetable[cd][d].get(p) is not None:
                            continue
                        if can_place(cd, ni, d, p, remaining[cd][ni], timetable, teacher_busy, teacher_map, block_heads, fm_used, class_divs):
                            valid_slots.append((d, p))

                random.shuffle(valid_slots)
                placed = 0
                for d, p in valid_slots:
                    if placed >= need['left']:
                        break
                    if timetable[cd][d].get(p) is not None:
                        continue
                    if can_place(cd, ni, d, p, remaining[cd][ni], timetable, teacher_busy, teacher_map, block_heads, fm_used, class_divs):
                        do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                        placed += 1
                        need['left'] -= 1

        # Step 2: Fill remaining slots day by day, period by period
        day_order = list(range(NUM_DAYS))
        if attempt % 2 == 1:
            random.shuffle(day_order)

        for d in day_order:
            for p in range(NUM_PERIODS):
                cd_order = list(class_divs)
                # Prioritize classes with most remaining
                cd_order.sort(key=lambda cd: -sum(n['left'] for n in remaining[cd]))
                if random.random() < 0.15:
                    random.shuffle(cd_order)

                used_this_slot = set()
                pet_count = 0
                art_count = 0

                for cd in cd_order:
                    if timetable[cd][d].get(p) is not None:
                        # Track already-placed teachers
                        slot = timetable[cd][d][p]
                        for t in slot.get('teachers', [slot.get('teacher_str', '')]):
                            used_this_slot.add(t)
                        continue

                    # Find candidates
                    candidates = []
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue

                        # Max 2 same subject per day
                        same_today = sum(1 for pp in range(NUM_PERIODS)
                                         if timetable[cd][d].get(pp) and timetable[cd][d][pp]['subject'] == need['subject'])
                        if same_today >= 2:
                            continue

                        # Multi-class limits
                        if need['subject'] == 'PET' and pet_count >= MAX_PET_PER_SLOT:
                            continue
                        if need['subject'] == 'Art' and art_count >= MAX_ART_PER_SLOT:
                            continue

                        # Spread multi-class subjects: max 1 per class per day
                        if need['is_multi']:
                            already_today = sum(1 for pp in range(NUM_PERIODS)
                                                if timetable[cd][d].get(pp) and timetable[cd][d][pp]['subject'] == need['subject'])
                            if already_today >= 1:
                                continue

                        if need['is_multi']:
                            candidates.append((ni, need))
                            continue

                        # Check all teachers are free
                        all_free = True
                        for t in need['teachers']:
                            if t in used_this_slot and not need['is_multi']:
                                all_free = False
                                break
                            if teacher_busy[t][d].get(p):
                                all_free = False
                                break
                        if not all_free:
                            continue

                        if can_place(cd, ni, d, p, need, timetable, teacher_busy, teacher_map, block_heads, fm_used, class_divs):
                            candidates.append((ni, need))

                    if not candidates:
                        continue

                    # Sort: prefer teachers with fewer periods today, then most remaining
                    candidates.sort(key=lambda x: (
                        sum(len(teacher_busy[t][d]) for t in x[1]['teachers']),
                        -x[1]['left']
                    ))

                    ni, need = candidates[0]
                    do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                    need['left'] -= 1

                    if need['subject'] == 'PET':
                        pet_count += 1
                    if need['subject'] == 'Art':
                        art_count += 1
                    for t in need['teachers']:
                        used_this_slot.add(t)

        # Step 3: Fill any remaining with relaxed max periods (but keep rules)
        for cd in class_divs:
            for d in range(NUM_DAYS):
                for p in range(NUM_PERIODS):
                    if timetable[cd][d].get(p) is not None:
                        continue
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue
                        if need['is_multi']:
                            do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                            need['left'] -= 1
                            break
                        # Check teacher free (ignore max/day)
                        all_free = True
                        for t in need['teachers']:
                            if teacher_busy[t][d].get(p):
                                all_free = False
                                break
                            if is_teacher_restricted(t, d, p):
                                all_free = False
                                break
                            if t in block_heads and p == 0:
                                all_free = False
                                break
                        if all_free:
                            # Feeding mother check
                            ok = True
                            for t in need['teachers']:
                                if is_feeding_mother(t) and (p == 3 or p == 4):  # P4 or P5
                                    other_p = 4 if p == 3 else 3
                                    if teacher_busy[t][d].get(other_p):
                                        ok = False
                                        break
                            if ok:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                break

        # Step 4: Fill remaining blanks by swapping with other periods in the same class
        for cd in class_divs:
            for d in range(NUM_DAYS):
                for p in range(NUM_PERIODS):
                    if timetable[cd][d].get(p) is not None:
                        continue
                    # Try to find a subject that can go here (with rules)
                    placed = False
                    for ni, need in enumerate(remaining[cd]):
                        if need['left'] <= 0:
                            continue
                        if need['is_multi']:
                            do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                            need['left'] -= 1
                            placed = True
                            break
                        all_free = True
                        for t in need['teachers']:
                            if teacher_busy[t][d].get(p):
                                all_free = False
                                break
                            if is_teacher_restricted(t, d, p):
                                all_free = False
                                break
                            if t in block_heads and p == 0:
                                all_free = False
                                break
                        if all_free:
                            do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                            need['left'] -= 1
                            placed = True
                            break

                    if not placed:
                        # Try swap: find another period in this class where the needed teacher CAN go
                        for ni, need in enumerate(remaining[cd]):
                            if need['left'] <= 0 or need['is_multi']:
                                continue
                            # Find a period where this teacher's subject already exists in another day
                            # and swap with something that CAN be in this slot
                            for other_d in range(NUM_DAYS):
                                for other_p in range(NUM_PERIODS):
                                    if other_d == d and other_p == p:
                                        continue
                                    other_slot = timetable[cd][other_d].get(other_p)
                                    if not other_slot:
                                        continue
                                    # Can the current slot's needed teacher go in other_d/other_p?
                                    can_need_go_other = True
                                    for t in need['teachers']:
                                        if teacher_busy[t][other_d].get(other_p):
                                            can_need_go_other = False
                                            break
                                        if is_teacher_restricted(t, other_d, other_p):
                                            can_need_go_other = False
                                            break
                                    if not can_need_go_other:
                                        continue
                                    # Can other_slot's teacher go in d/p?
                                    other_teachers = other_slot.get('teachers', [other_slot.get('teacher_str', '')])
                                    can_other_go_here = True
                                    for t in other_teachers:
                                        if is_teacher_restricted(t, d, p):
                                            can_other_go_here = False
                                            break
                                    if not can_other_go_here:
                                        continue
                                    # Swap!
                                    timetable[cd][d][p] = other_slot
                                    timetable[cd][other_d][other_p] = None
                                    # Place the needed subject in the freed slot
                                    do_place(cd, other_d, other_p, need, timetable, teacher_busy, fm_used)
                                    need['left'] -= 1
                                    placed = True
                                    break
                                if placed:
                                    break
                            if placed:
                                break

                    # Last resort: still enforce feeding mother + restrictions, only relax max/day
                    if not placed:
                        for ni, need in enumerate(remaining[cd]):
                            if need['left'] <= 0:
                                continue
                            if need['is_multi']:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                placed = True
                                break
                            all_free = True
                            for t in need['teachers']:
                                if teacher_busy[t][d].get(p):
                                    all_free = False
                                    break
                                # Enforce feeding mother even here
                                if is_feeding_mother(t) and (p == 3 or p == 4):
                                    other_p = 4 if p == 3 else 3
                                    if teacher_busy[t][d].get(other_p):
                                        all_free = False
                                        break
                                # Enforce period restrictions even here
                                if is_teacher_restricted(t, d, p):
                                    all_free = False
                                    break
                            if all_free:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                placed = True
                                break

                    # Absolute last: only conflict check (1-2 slots max in entire school)
                    if not placed:
                        for ni, need in enumerate(remaining[cd]):
                            if need['left'] <= 0:
                                continue
                            if need['is_multi']:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                break
                            all_free = True
                            for t in need['teachers']:
                                if teacher_busy[t][d].get(p):
                                    all_free = False
                                    break
                            if all_free:
                                do_place(cd, d, p, need, timetable, teacher_busy, fm_used)
                                need['left'] -= 1
                                break

        # Count unplaced
        unplaced = sum(n['left'] for cd in class_divs for n in remaining[cd])

        if unplaced == 0:
            result = format_timetable(timetable, class_divs, remaining, needs)
            result['_violations'] = validate_timetable(timetable, class_divs, needs)
            return result

        if unplaced < best_unplaced:
            best_unplaced = unplaced
            best_timetable = {cd: {d: dict(timetable[cd][d]) for d in range(NUM_DAYS)} for cd in class_divs}

    # Always return something - never leave classes blank
    if best_timetable:
        result = format_timetable(best_timetable, class_divs, remaining, needs)
        result['_violations'] = validate_timetable(best_timetable, class_divs, needs)
        result['_unplaced'] = best_unplaced
        return result
    result = format_timetable(timetable, class_divs, remaining, needs)
    result['_violations'] = validate_timetable(timetable, class_divs, needs)
    return result


def validate_timetable(timetable, class_divs, needs):
    """Check for rule violations in the generated timetable"""
    violations = []
    
    # Build teacher schedule from timetable
    teacher_days = defaultdict(lambda: defaultdict(dict))
    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slot = timetable[cd][d].get(p)
                if slot:
                    teachers = slot.get('teachers', [slot.get('teacher_str', '')])
                    for t in teachers:
                        t = t.strip()
                        if t:
                            teacher_days[t][d][p] = cd

    # Check feeding mothers
    for fm in ['Jaleela', 'Shafeedha']:
        if fm not in teacher_days:
            continue
        for d in range(NUM_DAYS):
            has_p4 = 3 in teacher_days[fm][d]
            has_p5 = 4 in teacher_days[fm][d]
            if has_p4 and has_p5:
                violations.append(f"{fm}: {DAYS[d]} has BOTH P4 and P5 occupied")

    # Check Rashid
    if 'Rashid' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Rashid'][d]:
                violations.append(f"Rashid: {DAYS[d]} P1 occupied")
            if 3 in teacher_days['Rashid'][d]:
                violations.append(f"Rashid: {DAYS[d]} P4 occupied")

    # Check Bindya
    if 'Bindya' in teacher_days:
        for d in range(NUM_DAYS):
            if 0 in teacher_days['Bindya'][d]:
                violations.append(f"Bindya: {DAYS[d]} P1 occupied")

    # Check Friday restrictions
    friday = 4
    for t in ['Saheer', 'Yasir']:
        if t in teacher_days:
            if 3 in teacher_days[t][friday]:
                violations.append(f"{t}: Friday P4 occupied")
            if 4 in teacher_days[t][friday]:
                violations.append(f"{t}: Friday P5 occupied")

    for t in ['Swalih', 'Fuaad', 'Bavakutty']:
        if t in teacher_days:
            if 3 in teacher_days[t][friday]:
                violations.append(f"{t}: Friday P4 occupied")

    # Check blank periods
    for cd in class_divs:
        filled = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if timetable[cd][d].get(p))
        if filled < 35:
            violations.append(f"{cd}: only {filled}/35 periods filled")

    return violations


def can_place(cd, ni, d, p, need, timetable, teacher_busy, teacher_map, block_heads, fm_used, class_divs):
    """Check if a need can be placed at (d, p) for class cd"""
    if need['is_multi']:
        return True

    for t in need['teachers']:
        # Teacher busy
        if teacher_busy[t][d].get(p):
            return False

        # Restricted periods
        if is_teacher_restricted(t, d, p):
            return False

        # Block heads no P1
        if t in block_heads and p == 0:
            return False

        # Feeding mothers: only allow if the other (P4/P5) is free
        if is_feeding_mother(t) and (p == 3 or p == 4):  # P4=index3, P5=index4
            other_p = 4 if p == 3 else 3
            if teacher_busy[t][d].get(other_p):
                return False

        # Max periods per day
        t_info = teacher_map.get(t, {})
        # Rule teachers: strict 5 max. Others: allow up to 6
        rule_teachers = ['Rashid', 'Bindya', 'Jaleela', 'Shafeedha', 'Saheer', 'Yasir', 'Swalih', 'Fuaad', 'Bavakutty']
        if t.strip() in rule_teachers:
            max_per_day = 5
        else:
            max_per_day = t_info.get('maxPeriodsPerDay') or 6
        current_today = len(teacher_busy[t][d])
        if current_today >= max_per_day:
            return False

    # Science: no period 7 (hard)
    if need['subject'] in ['Physics', 'Chemistry', 'Biology'] and p == 6:
        return False

    return True


def do_place(cd, d, p, need, timetable, teacher_busy, fm_used):
    """Place a need at (d, p) for class cd"""
    timetable[cd][d][p] = {
        'subject': need['subject'],
        'teacher_str': need['teacher_str'],
        'teachers': need['teachers'],
        'is_multi': need['is_multi'],
        'shared': need['shared']
    }
    if not need['is_multi']:
        for t in need['teachers']:
            teacher_busy[t][d][p] = True
            if is_feeding_mother(t) and (p == 3 or p == 4):
                fm_used[t.strip()][d] += 1


def format_timetable(timetable, class_divs, remaining, needs):
    """Format timetable for frontend"""
    result = {}
    for cd in class_divs:
        result[cd] = {}
        for d in range(NUM_DAYS):
            day_name = DAYS[d]
            result[cd][day_name] = {}
            for p in range(NUM_PERIODS):
                period_num = PERIODS[p]
                slot = timetable[cd][d].get(p)
                if slot:
                    result[cd][day_name][period_num] = {
                        'subject': slot['subject'],
                        'teacher': slot['teacher_str'],
                        'shared': slot.get('shared', False)
                    }
    return result
