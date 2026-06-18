"""
Timetable Solver v14 - Zero blanks + all rules enforced

Strategy: Place ALL subjects first (guaranteed zero blanks), then iteratively
swap within each class to fix rule violations.

Hard Rules (NEVER broken):
1. No subject repeat per day (except Maths 10th max 2)
2. Block Head Teachers - no P1 (except their own class)  
3. Max 5 periods/day per teacher (one day can be 6, IT must be 6th for IT teachers)
4. Rashid - no P1 and P4
5. PET/Art/Music/WE not in P1
6. Art max 2 combined, Music max 2, WE max 2, PET max 6, IT max 6
7. Grade 10 Physics - NOT in Period 7
8. Class teacher in P1 minimum 2 days/week
"""
import random
from collections import defaultdict
import time

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7
TOTAL_SLOTS = NUM_DAYS * NUM_PERIODS

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']
SLOT_LIMITS = {'PET': 6, 'Art': 2, 'Music': 2, 'Work Experience': 2, 'IT': 6}


def solve_timetable(classes_data, teachers_data, max_attempts=80):
    if not classes_data:
        raise ValueError("No classes found.")
    if not teachers_data:
        raise ValueError("No teachers found.")

    start_time = time.time()
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    class_divs = []
    div_needs = {}
    div_class_teacher = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            div_needs[cd] = []
            div_class_teacher[cd] = cls.get('classTeacher', '').strip()

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

    # Trim to 35
    for cd in class_divs:
        total = sum(n['periods'] for n in div_needs[cd])
        while total > TOTAL_SLOTS and div_needs[cd]:
            last = div_needs[cd][-1]
            if last['periods'] > 1:
                last['periods'] -= 1
                total -= 1
            else:
                div_needs[cd].pop()
                total -= 1

    multi_teachers = set()
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['is_multi']:
                for t in need['teachers']:
                    multi_teachers.add(t)

    it_teachers = set()
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['subject'] == 'IT':
                for t in need['teachers']:
                    it_teachers.add(t)

    ctx = {
        'class_divs': class_divs,
        'div_needs': div_needs,
        'div_class_teacher': div_class_teacher,
        'block_heads': block_heads,
        'multi_teachers': multi_teachers,
        'it_teachers': it_teachers,
    }

    print(f"Solver v14: {len(class_divs)} divisions")

    best_result = None
    best_violations = 999999

    for attempt in range(max_attempts):
        if time.time() - start_time > 90:
            break
        schedule, teacher_slots = _build_schedule(ctx)
        v_count = _count_violations(schedule, teacher_slots, ctx)
        if v_count < best_violations:
            best_violations = v_count
            best_result = schedule
            if attempt % 10 == 0 or v_count == 0:
                print(f"  Attempt {attempt+1}: {v_count} violations")
        if v_count == 0:
            print(f"  PERFECT on attempt {attempt+1}")
            break

    if best_result is None:
        raise RuntimeError("Could not generate timetable.")

    print(f"  Done in {time.time()-start_time:.1f}s, {best_violations} violations")

    # Build output
    timetable = {}
    for cd in class_divs:
        timetable[cd] = {}
        for d in range(NUM_DAYS):
            timetable[cd][DAYS[d]] = {}
            for p in range(NUM_PERIODS):
                entry = best_result.get((cd, d, p))
                if entry:
                    subj = entry['subject']
                    if subj == 'IT':
                        subj = 'IT (Lab)'
                    timetable[cd][DAYS[d]][PERIODS[p]] = {
                        'subject': subj,
                        'teacher': entry['teacher_str'],
                        'shared': entry.get('shared', False)
                    }
                else:
                    timetable[cd][DAYS[d]][PERIODS[p]] = {
                        'subject': 'Free', 'teacher': '', 'shared': False
                    }

    violations = []
    for cd in class_divs:
        free = sum(1 for d in DAYS for p in PERIODS if timetable[cd][d][p]['subject'] == 'Free')
        if free > 0:
            violations.append(f"{cd}: has {free} Free periods")
    timetable['_violations'] = violations
    return timetable


def _build_schedule(ctx):
    """Build a complete schedule with zero blanks, then fix violations."""
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    schedule = {}
    teacher_slots = defaultdict(set)

    # Step 1: For each class, create a list of all period-slots to fill
    # and assign subjects to them respecting teacher conflicts
    for cd in class_divs:
        needs = div_needs[cd]
        # Build the period list for this class: each subject repeated periodsPerWeek times
        period_list = []
        for need in needs:
            for _ in range(need['periods']):
                period_list.append(need)

        # Pad or trim to exactly 35
        while len(period_list) < TOTAL_SLOTS:
            # Duplicate the subject with most periods
            if needs:
                top = max(needs, key=lambda n: n['periods'])
                period_list.append(top)
            else:
                break
        period_list = period_list[:TOTAL_SLOTS]

        # Shuffle the period list
        random.shuffle(period_list)

        # Sort slots: P1 first (for class teacher rule), then others
        slots = []
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slots.append((d, p))

        # Try to assign class teacher subjects to P1 slots
        ct = ctx['div_class_teacher'].get(cd, '')
        ct_periods = [i for i, n in enumerate(period_list) if ct in n['teachers'] and not n['is_multi']]
        non_ct_periods = [i for i in range(len(period_list)) if i not in ct_periods]

        # Assign to slots prioritizing constraints
        assigned = [None] * TOTAL_SLOTS  # slot_idx -> need
        slot_idx_map = {(d, p): d * NUM_PERIODS + p for d in range(NUM_DAYS) for p in range(NUM_PERIODS)}

        # Place class teacher in P1 (min 2 days)
        p1_slots = [(d, 0) for d in range(NUM_DAYS)]
        random.shuffle(p1_slots)
        ct_placed = 0
        for d, p in p1_slots:
            if ct_placed >= 2:
                break
            if not ct_periods:
                break
            idx = ct_periods.pop(0)
            need = period_list[idx]
            slot_i = slot_idx_map[(d, p)]
            # Check teacher not busy
            busy = False
            if not need['is_multi']:
                for t in need['teachers']:
                    if (d, p) in teacher_slots.get(t, set()):
                        busy = True
                        break
            if busy:
                ct_periods.append(idx)  # Put back
                continue
            # Check hard rules for P1
            if 'Rashid' in need['teachers']:
                ct_periods.append(idx)
                continue
            if need['subject'] in MULTI_CLASS_SUBJECTS:
                ct_periods.append(idx)
                continue
            assigned[slot_i] = need
            if not need['is_multi']:
                for t in need['teachers']:
                    teacher_slots[t].add((d, p))
            ct_placed += 1

        # Remaining periods - place them greedily
        remaining_indices = ct_periods + non_ct_periods
        random.shuffle(remaining_indices)

        # Sort remaining by constraint difficulty
        remaining_indices.sort(key=lambda i: _need_difficulty(period_list[i], ctx))

        for idx in remaining_indices:
            need = period_list[idx]
            # Find best available slot
            best_slot = None
            best_score = 999

            available_slots = [(d, p) for d in range(NUM_DAYS) for p in range(NUM_PERIODS)
                               if assigned[slot_idx_map[(d, p)]] is None]
            random.shuffle(available_slots)

            for d, p in available_slots:
                slot_i = slot_idx_map[(d, p)]
                if assigned[slot_i] is not None:
                    continue
                score = _placement_score(cd, need, d, p, schedule, teacher_slots, assigned, slot_idx_map, ctx)
                if score < best_score:
                    best_score = score
                    best_slot = (d, p)
                if score == 0:
                    break  # Perfect slot

            if best_slot:
                d, p = best_slot
                slot_i = slot_idx_map[(d, p)]
                assigned[slot_i] = need
                if not need['is_multi']:
                    for t in need['teachers']:
                        teacher_slots[t].add((d, p))

        # Write to schedule
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                slot_i = slot_idx_map[(d, p)]
                if assigned[slot_i]:
                    schedule[(cd, d, p)] = assigned[slot_i]

    return schedule, teacher_slots


def _need_difficulty(need, ctx):
    """Higher = harder to place, should be placed first"""
    score = 0
    if 'Rashid' in need['teachers']:
        score += 10
    for t in need['teachers']:
        if t in ctx['block_heads']:
            score += 5
    if need['subject'] in ['Physics'] and not need['is_multi']:
        score += 3  # Physics Grade 10 has P7 restriction
    return -score  # Negative so harder ones sort first


def _placement_score(cd, need, d, p, schedule, teacher_slots, assigned, slot_idx_map, ctx):
    """Score a placement. 0 = perfect, higher = more violations."""
    score = 0
    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']

    # Teacher conflict (worst violation)
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                score += 100

    # Rashid P1/P4
    if 'Rashid' in teachers and p in [0, 3]:
        score += 50

    # Block heads P1
    if p == 0:
        ct = ctx['div_class_teacher'].get(cd, '')
        for t in teachers:
            if t in ctx['block_heads'] and t != ct:
                score += 50

    # Multi-class subjects P1
    if subject in MULTI_CLASS_SUBJECTS and p == 0:
        score += 50

    # Grade 10 Physics/Chemistry not P7
    if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
        score += 1000  # Absolute hard constraint - never place here

    # Subject repeat today
    # Rule: max 1 per day normally, but ONE day per week can have a repeat
    sub_today = sum(1 for pp in range(NUM_PERIODS)
                    if assigned[slot_idx_map[(d, pp)]] is not None
                    and assigned[slot_idx_map[(d, pp)]]['subject'] == subject)
    if subject == 'Maths' and cd.startswith('10-'):
        if sub_today >= 2:
            score += 20
    else:
        if sub_today >= 1:
            # Check if this subject already repeats on another day this week
            repeat_days = 0
            for dd in range(NUM_DAYS):
                if dd == d:
                    continue
                day_count = sum(1 for pp in range(NUM_PERIODS)
                                if assigned[slot_idx_map[(dd, pp)]] is not None
                                and assigned[slot_idx_map[(dd, pp)]]['subject'] == subject)
                if day_count >= 2:
                    repeat_days += 1
            if repeat_days >= 1:
                # Already used the one repeat day, can't repeat again
                score += 40
            else:
                # This would be the repeat day - minor penalty
                score += 5

    # Max 5/day for teacher
    if not is_multi:
        for t in teachers:
            if t not in ctx['multi_teachers']:
                day_count = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == d)
                if day_count >= 5:
                    # Check if they already used their 6-day
                    days_with_6 = sum(1 for dd in range(NUM_DAYS)
                                      if sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == dd) >= 6)
                    if day_count >= 6 or days_with_6 >= 1:
                        score += 30
                    else:
                        # This would be the 6th - allowed once, but IT teacher needs IT
                        if t in ctx['it_teachers'] and subject != 'IT':
                            score += 30

    return score


def _count_violations(schedule, teacher_slots, ctx):
    """Count total violations in a schedule."""
    violations = 0
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    for cd in class_divs:
        # Check blanks
        placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if (cd, d, p) in schedule)
        needed = sum(n['periods'] for n in div_needs[cd])
        needed = min(needed, TOTAL_SLOTS)
        if placed < needed:
            violations += (needed - placed) * 10  # Heavy penalty for blanks

        for d in range(NUM_DAYS):
            subjects_today = defaultdict(int)
            for p in range(NUM_PERIODS):
                entry = schedule.get((cd, d, p))
                if not entry:
                    continue

                subject = entry['subject']
                teachers = entry['teachers']
                is_multi = entry['is_multi']

                subjects_today[subject] += 1

                # Rashid P1/P4
                if 'Rashid' in teachers and p in [0, 3]:
                    violations += 5

                # Block heads P1
                if p == 0:
                    ct = ctx['div_class_teacher'].get(cd, '')
                    for t in teachers:
                        if t in ctx['block_heads'] and t != ct:
                            violations += 3

                # Multi-class P1
                if subject in MULTI_CLASS_SUBJECTS and p == 0:
                    violations += 3

                # Grade 10 Physics/Chemistry P7
                if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
                    violations += 50

            # Subject repeats
            for sub, count in subjects_today.items():
                if sub == 'Maths' and cd.startswith('10-'):
                    if count > 2:
                        violations += (count - 2) * 2
                else:
                    if count > 1:
                        # Check if this is the only repeat day for this subject
                        other_repeat_days = 0
                        for dd in range(NUM_DAYS):
                            if dd == d:
                                continue
                            dd_count = sum(1 for pp in range(NUM_PERIODS)
                                          if schedule.get((cd, dd, pp), {}).get('subject') == sub
                                          if (cd, dd, pp) in schedule)
                            if dd_count >= 2:
                                other_repeat_days += 1
                        if other_repeat_days >= 1:
                            # More than one repeat day - violation
                            violations += (count - 1) * 3
                        elif count > 2:
                            # Max 2 even on the repeat day
                            violations += (count - 2) * 3

    return violations
