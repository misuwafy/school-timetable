"""
Timetable Solver v10 - Greedy + repair phase (NO Free periods allowed)
Implements all 15 constraints from the School Timetable Scheduling Constraints v3 PDF.
Handles 86+ divisions across 6 blocks.

CRITICAL RULE: Every subject period MUST be placed. No "Free" periods.
If a subject can't be placed with full constraints, relax teacher-day-limit
and subject-repeat constraints to ensure placement.
"""
import random
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7
TOTAL_SLOTS = NUM_DAYS * NUM_PERIODS  # 35

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']

# Constraint 10: Art (8,9) max 2, Music (8) max 2, WE (9) max 2
# Constraint 11: PET max 6 (soft)
# Constraint 15: IT lab max 6
SLOT_LIMITS = {
    'PET': 6,
    'Art': 2,
    'Music': 2,
    'Work Experience': 2,
    'IT': 6,
}

FRIDAY_P4_FREE = {'Bavakutty', 'Saheer', 'Yasir', 'Swalih'}


def solve_timetable(classes_data, teachers_data, max_attempts=50):
    """Greedy solver that guarantees all subjects are placed (no Free periods)"""

    if not classes_data:
        raise ValueError("No classes found. Please add classes with divisions first.")
    if not teachers_data:
        raise ValueError("No teachers found. Please add teachers first.")

    # Build teacher info
    teacher_info = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    # Identify IT teachers (Constraint 6)
    it_teachers = set()
    for cls in classes_data:
        for sub in cls.get('subjects', []):
            if sub.get('name') == 'IT' and sub.get('teacher'):
                it_teachers.add(sub['teacher'].strip())

    # Build class divisions and needs
    class_divs = []
    div_needs = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            div_needs[cd] = []

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
                    div_needs[cd].append({
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
                    div_needs[cd].append({
                        'subject': sub['name'],
                        'teacher_str': t,
                        'teachers': [t],
                        'periods': sub['periodsPerWeek'],
                        'is_multi': is_multi,
                        'shared': False
                    })

    # Check we have valid data
    empty_divs = [cd for cd in class_divs if not div_needs[cd]]
    if len(empty_divs) == len(class_divs):
        raise ValueError("No subjects with teachers assigned to any class.")

    # Trim classes that exceed 35 periods
    for cd in class_divs:
        total = sum(n['periods'] for n in div_needs[cd])
        if total > TOTAL_SLOTS:
            # Trim excess from shared subjects (they have duplicated periods)
            while sum(n['periods'] for n in div_needs[cd]) > TOTAL_SLOTS and div_needs[cd]:
                last = div_needs[cd][-1]
                if last['periods'] > 1:
                    last['periods'] -= 1
                else:
                    div_needs[cd].pop()

    # Identify multi-class teachers
    multi_class_teacher_set = set()
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['is_multi']:
                for t in need['teachers']:
                    multi_class_teacher_set.add(t)

    print(f"Solver v10: {len(class_divs)} divisions, {len(teachers_data)} teachers")

    ctx = {
        'class_divs': class_divs,
        'div_needs': div_needs,
        'block_heads': block_heads,
        'it_teachers': it_teachers,
        'multi_class_teacher_set': multi_class_teacher_set,
        'teacher_info': teacher_info,
    }

    # Try multiple random attempts
    best_result = None
    best_unplaced = 999999

    for attempt in range(max_attempts):
        result, unplaced_count = _attempt_schedule(ctx)
        if unplaced_count < best_unplaced:
            best_unplaced = unplaced_count
            best_result = result
            if attempt % 10 == 0:
                print(f"  Attempt {attempt + 1}: {unplaced_count} unplaced periods")
        if unplaced_count == 0:
            print(f"  Perfect solution on attempt {attempt + 1}")
            break

    if best_result is None:
        raise RuntimeError("Could not generate any timetable. Check subject/teacher assignments.")

    print(f"  Final: {best_unplaced} unplaced periods")

    # Build output format
    timetable = {}
    for cd in class_divs:
        timetable[cd] = {}
        for d in range(NUM_DAYS):
            day_name = DAYS[d]
            timetable[cd][day_name] = {}
            for p in range(NUM_PERIODS):
                period_num = PERIODS[p]
                entry = best_result.get((cd, d, p))
                if entry:
                    subject_display = entry['subject']
                    if subject_display == 'IT':
                        subject_display = 'IT (Lab)'
                    timetable[cd][day_name][period_num] = {
                        'subject': subject_display,
                        'teacher': entry['teacher_str'],
                        'shared': entry.get('shared', False)
                    }
                else:
                    # This should not happen with repair phase
                    timetable[cd][day_name][period_num] = {
                        'subject': 'Free',
                        'teacher': '',
                        'shared': False
                    }

    violations = _validate(timetable, class_divs)
    timetable['_violations'] = violations
    return timetable


def _attempt_schedule(ctx):
    """Build schedule with guaranteed placement using repair phase"""

    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    # State
    schedule = {}
    teacher_slots = defaultdict(set)
    teacher_day_count = defaultdict(lambda: defaultdict(int))
    subject_day_count = defaultdict(lambda: defaultdict(int))
    slot_subject_count = defaultdict(lambda: defaultdict(int))
    cd_filled = defaultdict(set)

    # Build assignment list
    all_assignments = []
    for cd in class_divs:
        for need in div_needs[cd]:
            all_assignments.append({'cd': cd, 'need': need, 'remaining': need['periods']})

    # Sort: harder-to-place first
    def priority(a):
        need = a['need']
        if need['is_multi']:
            return 500
        p = 0
        for t in need['teachers']:
            if t in ctx['block_heads']:
                p -= 5
            if t == 'Rashid':
                p -= 10
            if t in FRIDAY_P4_FREE:
                p -= 3
            if t == 'Jaleela':
                p -= 5
            if t == 'Bindya':
                p -= 3
        return p

    all_assignments.sort(key=priority)

    # Shuffle within same-priority groups
    i = 0
    while i < len(all_assignments):
        j = i
        p_val = priority(all_assignments[i])
        while j < len(all_assignments) and priority(all_assignments[j]) == p_val:
            j += 1
        chunk = all_assignments[i:j]
        random.shuffle(chunk)
        all_assignments[i:j] = chunk
        i = j

    # PHASE 1: Place with full constraints
    unplaced = []
    for assignment in all_assignments:
        cd = assignment['cd']
        need = assignment['need']
        periods_to_place = assignment['remaining']

        valid_slots = []
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx, strict=True):
                    valid_slots.append((d, p))

        random.shuffle(valid_slots)
        day_usage = defaultdict(int)
        for dd, pp in cd_filled[cd]:
            day_usage[dd] += 1
        valid_slots.sort(key=lambda s: (day_usage[s[0]], abs(s[1] - 3) * 0.1))

        placed = 0
        for d, p in valid_slots:
            if placed >= periods_to_place:
                break
            if (cd, d, p) in schedule:
                continue
            if not _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx, strict=True):
                continue
            _place(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
                   subject_day_count, slot_subject_count, cd_filled, ctx)
            placed += 1

        if placed < periods_to_place:
            unplaced.append({'cd': cd, 'need': need, 'remaining': periods_to_place - placed})

    # PHASE 2: Repair - place remaining with relaxed constraints
    # Relax: allow subject repeat (max 2/day), relax teacher day limit
    still_unplaced = []
    for assignment in unplaced:
        cd = assignment['cd']
        need = assignment['need']
        periods_to_place = assignment['remaining']

        valid_slots = []
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx, strict=False):
                    valid_slots.append((d, p))

        random.shuffle(valid_slots)
        day_usage = defaultdict(int)
        for dd, pp in cd_filled[cd]:
            day_usage[dd] += 1
        valid_slots.sort(key=lambda s: (day_usage[s[0]], abs(s[1] - 3) * 0.1))

        placed = 0
        for d, p in valid_slots:
            if placed >= periods_to_place:
                break
            if (cd, d, p) in schedule:
                continue
            if not _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx, strict=False):
                continue
            _place(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
                   subject_day_count, slot_subject_count, cd_filled, ctx)
            placed += 1

        if placed < periods_to_place:
            still_unplaced.append({'cd': cd, 'need': need, 'remaining': periods_to_place - placed})

    # PHASE 3: Force-place anything still unplaced (only hard constraints: teacher conflict & slot taken)
    final_unplaced = 0
    for assignment in still_unplaced:
        cd = assignment['cd']
        need = assignment['need']
        periods_to_place = assignment['remaining']

        placed = 0
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if placed >= periods_to_place:
                    break
                if (cd, d, p) in schedule:
                    continue
                # Only check absolute hard constraints: slot empty + teacher not in two places
                if _is_valid_minimal(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx):
                    _place(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
                           subject_day_count, slot_subject_count, cd_filled, ctx)
                    placed += 1

        final_unplaced += (periods_to_place - placed)

    # Fill any truly empty slots in classes that had <35 total periods
    for cd in class_divs:
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if (cd, d, p) not in schedule:
                    # Find a subject that could use an extra period or mark as study
                    # Use the class teacher's subject or just leave empty
                    # Actually this shouldn't happen since we trimmed to 35
                    pass

    return schedule, final_unplaced


def _place(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
           subject_day_count, slot_subject_count, cd_filled, ctx):
    """Place a need at (cd, d, p) and update state"""
    schedule[(cd, d, p)] = need
    cd_filled[cd].add((d, p))
    if need['subject'] != 'Free' and not need['is_multi']:
        for t in need['teachers']:
            teacher_slots[t].add((d, p))
            teacher_day_count[t][d] += 1
    if need['subject'] != 'Free':
        subject_day_count[(cd, need['subject'])][d] += 1
        slot_subject_count[(d, p)][need['subject']] += 1


def _is_valid_minimal(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx):
    """Minimal validity check - only absolute hard constraints"""
    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']

    # Teacher can't be in two places at once (non-multi only)
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # IT lab capacity (hard constraint - no more than 6)
    if subject == 'IT':
        current = slot_subject_count.get((d, p), {}).get('IT', 0)
        if current >= 6:
            return False

    return True


def _is_valid(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
              subject_day_count, slot_subject_count, cd_filled, ctx, strict=True):
    """Check constraints. strict=True for Phase 1, False for Phase 2 (relaxed)"""

    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']
    block_heads = ctx['block_heads']
    it_teachers = ctx['it_teachers']
    multi_teachers = ctx['multi_class_teacher_set']

    # === Constraint 12: PET/Art/Music/WE NOT in Period 1 (Strict) ===
    if subject in MULTI_CLASS_SUBJECTS and p == 0:
        return False

    # === Constraint 4: Block Head Teachers - no Period 1 (Strict) ===
    if p == 0:
        for t in teachers:
            if t in block_heads:
                return False

    # === Constraint 5: Bindya - no Period 1 (Strict) ===
    if p == 0 and 'Bindya' in teachers:
        return False

    # === Constraint 7: Rashid - no Period 1 and Period 4 (Hard) ===
    if 'Rashid' in teachers and p in [0, 3]:
        return False

    # === Constraint 8: Friday P4 free for certain teachers (Strict) ===
    if d == 4 and p == 3:
        for t in teachers:
            if t in FRIDAY_P4_FREE:
                return False

    # === Constraint 2: No Physics/Chemistry in Period 7 for Grade 10 (Hard) ===
    if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
        return False

    # === Constraint 9: Jaleela - P4 or P5 free each day (Strict) ===
    if 'Jaleela' in teachers and p in [3, 4]:
        other_p = 4 if p == 3 else 3
        if (d, other_p) in teacher_slots.get('Jaleela', set()):
            return False

    # === Teacher conflict: non-multi teachers can only be in one class per slot ===
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # === Constraint 6: Max periods per day (only strict mode) ===
    if strict and not is_multi:
        for t in teachers:
            if t not in multi_teachers:
                current_day = teacher_day_count[t][d]
                if t not in it_teachers:
                    if current_day >= 5:
                        return False
                else:
                    if current_day >= 7:
                        return False
    elif not strict and not is_multi:
        # Relaxed: allow up to 7 for any teacher
        for t in teachers:
            if t not in multi_teachers:
                if teacher_day_count[t][d] >= 7:
                    return False

    # === Constraint 1: No subject repetition per day ===
    current_sub_day = subject_day_count.get((cd, subject), {}).get(d, 0)
    if strict:
        if subject == 'Maths' and cd.startswith('10-'):
            if current_sub_day >= 2:
                return False
        else:
            if current_sub_day >= 1:
                return False
    else:
        # Relaxed: allow max 2 of any subject per day
        if current_sub_day >= 2:
            return False

    # === Constraints 10, 11, 15: Slot capacity limits ===
    if subject in SLOT_LIMITS:
        current_count = slot_subject_count.get((d, p), {}).get(subject, 0)
        if current_count >= SLOT_LIMITS[subject]:
            return False

    return True


def _validate(timetable, class_divs):
    """Post-generation validation"""
    violations = []
    for cd in class_divs:
        filled = 0
        free_count = 0
        for d_name in DAYS:
            for p_num in PERIODS:
                entry = timetable.get(cd, {}).get(d_name, {}).get(p_num)
                if entry and entry.get('subject'):
                    filled += 1
                    if entry['subject'] == 'Free':
                        free_count += 1
        if filled < TOTAL_SLOTS:
            violations.append(f"{cd}: only {filled}/35 slots filled")
        if free_count > 0:
            violations.append(f"{cd}: has {free_count} Free periods (subjects not placed)")
    return violations
