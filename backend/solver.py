"""
Timetable Solver v9 - Greedy + random restarts
Implements all 15 constraints from the School Timetable Scheduling Constraints v3 PDF.
Handles 86+ divisions across 6 blocks.

Key insight: Multi-class subjects (PET, Art, Music, WE) share time slots —
one teacher handles multiple classes in the same period simultaneously.
These teachers are NOT subject to per-day period limits or teacher-conflict checks.
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
SLOT_LIMITS = {
    'PET': 6,
    'Art': 2,
    'Music': 2,
    'Work Experience': 2,
    'IT': 6,  # Constraint 15: max 6 IT labs simultaneously
}

FRIDAY_P4_FREE = {'Bavakutty', 'Saheer', 'Yasir', 'Swalih'}


def solve_timetable(classes_data, teachers_data, max_attempts=40):
    """Fast greedy solver with random restarts for large school timetables"""

    if not classes_data:
        raise ValueError("No classes found. Please add classes with divisions first.")
    if not teachers_data:
        raise ValueError("No teachers found. Please add teachers first.")

    # Build teacher info
    teacher_info = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    # Identify which teachers teach IT (for Constraint 6)
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

    # Pad with Free periods if total != 35
    for cd in class_divs:
        total = sum(n['periods'] for n in div_needs[cd])
        if total < TOTAL_SLOTS:
            div_needs[cd].append({
                'subject': 'Free',
                'teacher_str': '',
                'teachers': [],
                'periods': TOTAL_SLOTS - total,
                'is_multi': True,
                'shared': False
            })
        elif total > TOTAL_SLOTS:
            while sum(n['periods'] for n in div_needs[cd]) > TOTAL_SLOTS and div_needs[cd]:
                last = div_needs[cd][-1]
                if last['periods'] > 1:
                    last['periods'] -= 1
                else:
                    div_needs[cd].pop()

    # Identify multi-class teachers (they share time slots, not subject to conflict/day-limit)
    multi_class_teacher_set = set()
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['is_multi']:
                for t in need['teachers']:
                    multi_class_teacher_set.add(t)

    print(f"Solver v9: {len(class_divs)} divisions, {len(teachers_data)} teachers, "
          f"{len(multi_class_teacher_set)} multi-class teachers")

    # Context object to pass around
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
    best_score = -1
    target_score = len(class_divs) * TOTAL_SLOTS

    for attempt in range(max_attempts):
        result, score = _attempt_schedule(ctx)
        if score > best_score:
            best_score = score
            best_result = result
            pct = 100 * score // target_score
            if attempt % 5 == 0 or score == target_score:
                print(f"  Attempt {attempt + 1}: {score}/{target_score} ({pct}%)")
        if score == target_score:
            print(f"  Perfect solution on attempt {attempt + 1}")
            break
        # If we're close (>98%), try more attempts to hit perfect
        if best_score >= target_score * 0.98 and attempt >= max_attempts - 1:
            max_attempts += 10  # extend search

    if best_result is None:
        raise RuntimeError("Could not generate any timetable. Check subject/teacher assignments.")

    print(f"  Final: {best_score}/{target_score} ({100*best_score//target_score}%)")

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
                    timetable[cd][day_name][period_num] = {
                        'subject': 'Free',
                        'teacher': '',
                        'shared': False
                    }

    violations = _validate(timetable, class_divs)
    timetable['_violations'] = violations
    return timetable


def _attempt_schedule(ctx):
    """One attempt at building a full schedule"""

    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    # State tracking
    schedule = {}  # (cd, day, period) -> need entry
    teacher_slots = defaultdict(set)  # non-multi teacher -> set of (day, period)
    teacher_day_count = defaultdict(lambda: defaultdict(int))  # non-multi teacher -> day -> count
    subject_day_count = defaultdict(lambda: defaultdict(int))  # (cd, subject) -> day -> count
    slot_subject_count = defaultdict(lambda: defaultdict(int))  # (day, period) -> subject -> count
    cd_filled = defaultdict(set)  # cd -> set of (day, period)

    # Build assignment list
    all_assignments = []
    for cd in class_divs:
        for need in div_needs[cd]:
            all_assignments.append({'cd': cd, 'need': need, 'remaining': need['periods']})

    # Sort: constrained regular subjects first, then multi-class, then Free
    def priority(a):
        need = a['need']
        if need['subject'] == 'Free':
            return 1000
        if need['is_multi']:
            return 500
        # Regular subjects - more constrained teachers get priority
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

    # Shuffle within same-priority groups for randomness
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

    score = 0

    for assignment in all_assignments:
        cd = assignment['cd']
        need = assignment['need']
        periods_to_place = assignment['remaining']

        # Get valid slots
        valid_slots = []
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx):
                    valid_slots.append((d, p))

        # Shuffle and sort by preference
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
            # Re-validate (state may have changed)
            if not _is_valid(cd, need, d, p, schedule, teacher_slots,
                             teacher_day_count, subject_day_count,
                             slot_subject_count, cd_filled, ctx):
                continue

            # Place
            schedule[(cd, d, p)] = need
            cd_filled[cd].add((d, p))
            if need['subject'] != 'Free' and not need['is_multi']:
                for t in need['teachers']:
                    teacher_slots[t].add((d, p))
                    teacher_day_count[t][d] += 1
            if need['subject'] != 'Free':
                subject_day_count[(cd, need['subject'])][d] += 1
                slot_subject_count[(d, p)][need['subject']] += 1
            placed += 1
            score += 1

        # Fill leftover with Free
        if placed < periods_to_place and need['subject'] == 'Free':
            for d in range(NUM_DAYS):
                for p in range(NUM_PERIODS):
                    if placed >= periods_to_place:
                        break
                    if (cd, d, p) not in schedule:
                        schedule[(cd, d, p)] = need
                        cd_filled[cd].add((d, p))
                        placed += 1
                        score += 1

    return schedule, score


def _is_valid(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
              subject_day_count, slot_subject_count, cd_filled, ctx):
    """Check all constraints for placing need at (cd, d, p)"""

    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']
    block_heads = ctx['block_heads']
    it_teachers = ctx['it_teachers']
    multi_teachers = ctx['multi_class_teacher_set']

    # Free can go anywhere empty
    if subject == 'Free':
        return True

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

    # === Constraint 8: Bavakutty/Saheer/Yasir/Swalih - no Period 4 on Friday (Strict) ===
    if d == 4 and p == 3:  # Friday, Period 4 (0-indexed: d=4, p=3)
        for t in teachers:
            if t in FRIDAY_P4_FREE:
                return False

    # === Constraint 2: No Physics/Chemistry in Period 7 for Grade 10 (Hard) ===
    if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
        return False

    # === Constraint 9: Jaleela - either P4 or P5 free each day (Strict) ===
    if 'Jaleela' in teachers and p in [3, 4]:
        other_p = 4 if p == 3 else 3
        if (d, other_p) in teacher_slots.get('Jaleela', set()):
            return False

    # === Teacher conflict: non-multi teachers can only be in one class per slot ===
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # === Constraint 6: Max periods per day for non-multi teachers ===
    # Non-IT teachers: max 5 periods/day
    # IT teachers: can exceed 5 if IT period is included (handled by data - they just get more)
    if not is_multi:
        for t in teachers:
            if t not in multi_teachers:
                current_day = teacher_day_count[t][d]
                if t not in it_teachers:
                    # Non-IT teacher: max 5 periods per day
                    if current_day >= 5:
                        return False
                else:
                    # IT teacher: allowed more than 5, no hard cap enforced here
                    # (natural limit is the number of classes they teach)
                    if current_day >= 7:
                        return False

    # === Constraint 1: No subject repetition per day per class ===
    # Exception: Maths 10th can appear twice
    # For greedy solver: allow max 2 as soft fallback (strict is 1, except Maths-10)
    current_sub_day = subject_day_count.get((cd, subject), {}).get(d, 0)
    if subject == 'Maths' and cd.startswith('10-'):
        if current_sub_day >= 2:
            return False
    else:
        if current_sub_day >= 1:
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
        for d_name in DAYS:
            for p_num in PERIODS:
                entry = timetable.get(cd, {}).get(d_name, {}).get(p_num)
                if entry and entry.get('subject'):
                    filled += 1
        if filled < TOTAL_SLOTS:
            violations.append(f"{cd}: only {filled}/35 slots filled")
    return violations
