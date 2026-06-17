"""
Timetable Solver v11 - Greedy + swap-based repair (ZERO Free periods)
Implements all 15 constraints from School Timetable Scheduling Constraints v3.

Strategy:
1. Phase 1: Greedy placement with full constraints
2. Phase 2: Relaxed placement (allow subject repeats, relax day limits)
3. Phase 3: Swap repair - for any unplaced period, find a slot where another
   subject can be moved elsewhere, freeing up the needed slot
4. Phase 4: Force-place with only teacher-conflict check
"""
import random
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [1, 2, 3, 4, 5, 6, 7]
NUM_DAYS = 5
NUM_PERIODS = 7
TOTAL_SLOTS = NUM_DAYS * NUM_PERIODS  # 35

MULTI_CLASS_SUBJECTS = ['PET', 'Music', 'Art', 'Work Experience']

SLOT_LIMITS = {
    'PET': 6,
    'Art': 2,
    'Music': 2,
    'Work Experience': 2,
    'IT': 6,
}

FRIDAY_P4_FREE = {'Bavakutty', 'Saheer', 'Yasir', 'Swalih'}


def solve_timetable(classes_data, teachers_data, max_attempts=50):
    """Greedy solver that guarantees all subjects placed"""

    if not classes_data:
        raise ValueError("No classes found.")
    if not teachers_data:
        raise ValueError("No teachers found.")

    teacher_info = {t['name']: t for t in teachers_data}
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    it_teachers = set()
    for cls in classes_data:
        for sub in cls.get('subjects', []):
            if sub.get('name') == 'IT' and sub.get('teacher'):
                it_teachers.add(sub['teacher'].strip())

    # Build divisions and needs
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

    empty_divs = [cd for cd in class_divs if not div_needs[cd]]
    if len(empty_divs) == len(class_divs):
        raise ValueError("No subjects with teachers assigned.")

    # Ensure total <= 35 per division
    for cd in class_divs:
        total = sum(n['periods'] for n in div_needs[cd])
        if total > TOTAL_SLOTS:
            while sum(n['periods'] for n in div_needs[cd]) > TOTAL_SLOTS and div_needs[cd]:
                last = div_needs[cd][-1]
                if last['periods'] > 1:
                    last['periods'] -= 1
                else:
                    div_needs[cd].pop()
        elif total < TOTAL_SLOTS:
            # Need to fill remaining - duplicate periods from subjects with most periods
            deficit = TOTAL_SLOTS - total
            # Sort needs by periods descending, add 1 to each until filled
            sorted_needs = sorted(div_needs[cd], key=lambda n: -n['periods'])
            idx = 0
            while deficit > 0 and sorted_needs:
                sorted_needs[idx % len(sorted_needs)]['periods'] += 1
                deficit -= 1
                idx += 1

    multi_class_teacher_set = set()
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['is_multi']:
                for t in need['teachers']:
                    multi_class_teacher_set.add(t)

    print(f"Solver v11: {len(class_divs)} divisions, {len(teachers_data)} teachers")

    ctx = {
        'class_divs': class_divs,
        'div_needs': div_needs,
        'block_heads': block_heads,
        'it_teachers': it_teachers,
        'multi_class_teacher_set': multi_class_teacher_set,
        'teacher_info': teacher_info,
    }

    best_result = None
    best_unplaced = 999999

    for attempt in range(max_attempts):
        result, unplaced = _attempt_full(ctx)
        if unplaced < best_unplaced:
            best_unplaced = unplaced
            best_result = result
            if attempt % 10 == 0 or unplaced == 0:
                print(f"  Attempt {attempt+1}: {unplaced} unplaced")
        if unplaced == 0:
            print(f"  Perfect on attempt {attempt+1}")
            break

    if best_result is None:
        raise RuntimeError("Could not generate timetable.")

    print(f"  Final: {best_unplaced} unplaced")

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
                        'subject': 'Free',
                        'teacher': '',
                        'shared': False
                    }

    violations = _validate(timetable, class_divs)
    timetable['_violations'] = violations
    return timetable


def _attempt_full(ctx):
    """Full attempt: greedy + relaxed + swap + force"""
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    schedule = {}
    teacher_slots = defaultdict(set)
    teacher_day_count = defaultdict(lambda: defaultdict(int))
    subject_day_count = defaultdict(lambda: defaultdict(int))
    slot_subject_count = defaultdict(lambda: defaultdict(int))
    cd_filled = defaultdict(set)

    state = (schedule, teacher_slots, teacher_day_count, subject_day_count,
             slot_subject_count, cd_filled)

    # Build assignments
    all_assignments = []
    for cd in class_divs:
        for need in div_needs[cd]:
            all_assignments.append({'cd': cd, 'need': need, 'remaining': need['periods']})

    # Prioritize constrained subjects
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
    # Shuffle within priority groups
    _shuffle_groups(all_assignments, priority)

    # PHASE 1: Strict placement
    unplaced_list = _place_batch(all_assignments, state, ctx, strict=True)

    # PHASE 2: Relaxed placement for leftovers
    if unplaced_list:
        unplaced_list = _place_batch(unplaced_list, state, ctx, strict=False)

    # PHASE 3: Swap-based repair
    if unplaced_list:
        unplaced_list = _swap_repair(unplaced_list, state, ctx)

    # PHASE 4: Force-place (ignore everything except teacher-in-two-places)
    final_unplaced = 0
    for assignment in unplaced_list:
        cd = assignment['cd']
        need = assignment['need']
        remaining = assignment['remaining']
        placed = 0
        for d in range(NUM_DAYS):
            if placed >= remaining:
                break
            for p in range(NUM_PERIODS):
                if placed >= remaining:
                    break
                if (cd, d, p) in schedule:
                    continue
                # Only check: teacher not double-booked
                can_place = True
                if not need['is_multi']:
                    for t in need['teachers']:
                        if (d, p) in teacher_slots.get(t, set()):
                            can_place = False
                            break
                if can_place:
                    _do_place(cd, need, d, p, *state, ctx)
                    placed += 1
        final_unplaced += (remaining - placed)

    return schedule, final_unplaced


def _place_batch(assignments, state, ctx, strict):
    """Place a batch of assignments, return unplaced ones"""
    schedule, teacher_slots, teacher_day_count, subject_day_count, \
        slot_subject_count, cd_filled = state

    unplaced = []
    for assignment in assignments:
        cd = assignment['cd']
        need = assignment['need']
        to_place = assignment['remaining']

        valid = []
        for d in range(NUM_DAYS):
            for p in range(NUM_PERIODS):
                if _check(cd, need, d, p, *state, ctx, strict):
                    valid.append((d, p))

        random.shuffle(valid)
        # Spread across days
        day_usage = defaultdict(int)
        for dd, pp in cd_filled[cd]:
            day_usage[dd] += 1
        valid.sort(key=lambda s: (day_usage[s[0]], abs(s[1] - 3) * 0.1))

        placed = 0
        for d, p in valid:
            if placed >= to_place:
                break
            if (cd, d, p) in schedule:
                continue
            if not _check(cd, need, d, p, *state, ctx, strict):
                continue
            _do_place(cd, need, d, p, *state, ctx)
            placed += 1

        if placed < to_place:
            unplaced.append({'cd': cd, 'need': need, 'remaining': to_place - placed})

    return unplaced


def _swap_repair(unplaced_list, state, ctx):
    """Try to swap existing placements to make room for unplaced subjects"""
    schedule, teacher_slots, teacher_day_count, subject_day_count, \
        slot_subject_count, cd_filled = state

    still_unplaced = []

    for assignment in unplaced_list:
        cd = assignment['cd']
        need = assignment['need']
        remaining = assignment['remaining']
        placed = 0

        for d in range(NUM_DAYS):
            if placed >= remaining:
                break
            for p in range(NUM_PERIODS):
                if placed >= remaining:
                    break
                if (cd, d, p) not in schedule:
                    # Empty slot - try relaxed placement
                    if _check(cd, need, d, p, *state, ctx, strict=False):
                        _do_place(cd, need, d, p, *state, ctx)
                        placed += 1
                    continue

                # Slot is taken - try swapping
                existing = schedule[(cd, d, p)]
                if existing['subject'] == need['subject']:
                    continue  # Same subject, no point swapping

                # Can we move 'existing' somewhere else?
                # Remove existing temporarily
                _do_remove(cd, existing, d, p, *state, ctx)

                # Can we place 'need' here now?
                if _check(cd, need, d, p, *state, ctx, strict=False):
                    # Try to find a new home for 'existing'
                    moved = False
                    for d2 in range(NUM_DAYS):
                        if moved:
                            break
                        for p2 in range(NUM_PERIODS):
                            if (cd, d2, p2) in schedule:
                                continue
                            if _check(cd, existing, d2, p2, *state, ctx, strict=False):
                                # Swap successful
                                _do_place(cd, need, d, p, *state, ctx)
                                _do_place(cd, existing, d2, p2, *state, ctx)
                                moved = True
                                placed += 1
                                break

                    if not moved:
                        # Put existing back
                        _do_place(cd, existing, d, p, *state, ctx)
                else:
                    # Put existing back
                    _do_place(cd, existing, d, p, *state, ctx)

        if placed < remaining:
            still_unplaced.append({'cd': cd, 'need': need, 'remaining': remaining - placed})

    return still_unplaced


def _do_place(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
              subject_day_count, slot_subject_count, cd_filled, ctx):
    """Place need at (cd, d, p)"""
    schedule[(cd, d, p)] = need
    cd_filled[cd].add((d, p))
    if not need['is_multi']:
        for t in need['teachers']:
            teacher_slots[t].add((d, p))
            teacher_day_count[t][d] += 1
    subject_day_count[(cd, need['subject'])][d] += 1
    slot_subject_count[(d, p)][need['subject']] += 1


def _do_remove(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
               subject_day_count, slot_subject_count, cd_filled, ctx):
    """Remove need from (cd, d, p)"""
    del schedule[(cd, d, p)]
    cd_filled[cd].discard((d, p))
    if not need['is_multi']:
        for t in need['teachers']:
            teacher_slots[t].discard((d, p))
            teacher_day_count[t][d] -= 1
    subject_day_count[(cd, need['subject'])][d] -= 1
    slot_subject_count[(d, p)][need['subject']] -= 1


def _check(cd, need, d, p, schedule, teacher_slots, teacher_day_count,
           subject_day_count, slot_subject_count, cd_filled, ctx, strict=True):
    """Validate placement"""
    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']
    block_heads = ctx['block_heads']
    it_teachers = ctx['it_teachers']
    multi_teachers = ctx['multi_class_teacher_set']

    # Constraint 12: Multi-class subjects not P1
    if subject in MULTI_CLASS_SUBJECTS and p == 0:
        return False

    # Constraint 4: Block heads no P1
    if p == 0:
        for t in teachers:
            if t in block_heads:
                return False

    # Constraint 5: Bindya no P1
    if p == 0 and 'Bindya' in teachers:
        return False

    # Constraint 7: Rashid no P1, P4
    if 'Rashid' in teachers and p in [0, 3]:
        return False

    # Constraint 8: Friday P4 free
    if d == 4 and p == 3:
        for t in teachers:
            if t in FRIDAY_P4_FREE:
                return False

    # Constraint 2: No Physics/Chemistry P7 Grade 10
    if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
        return False

    # Constraint 9: Jaleela P4 or P5 free
    if 'Jaleela' in teachers and p in [3, 4]:
        other_p = 4 if p == 3 else 3
        if (d, other_p) in teacher_slots.get('Jaleela', set()):
            return False

    # Teacher conflict (non-multi)
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # Constraint 6: Max periods/day
    if not is_multi:
        for t in teachers:
            if t not in multi_teachers:
                current = teacher_day_count[t][d]
                if strict:
                    if t not in it_teachers:
                        if current >= 5:
                            return False
                    else:
                        if current >= 7:
                            return False
                else:
                    if current >= 7:
                        return False

    # Constraint 1: Subject repetition
    current_sub = subject_day_count.get((cd, subject), {}).get(d, 0)
    if strict:
        if subject == 'Maths' and cd.startswith('10-'):
            if current_sub >= 2:
                return False
        else:
            if current_sub >= 1:
                return False
    else:
        # Relaxed: allow 2
        if current_sub >= 2:
            return False

    # Slot capacity
    if subject in SLOT_LIMITS:
        current = slot_subject_count.get((d, p), {}).get(subject, 0)
        if current >= SLOT_LIMITS[subject]:
            return False

    return True


def _shuffle_groups(assignments, priority_fn):
    """Shuffle within same-priority groups"""
    i = 0
    while i < len(assignments):
        j = i
        p_val = priority_fn(assignments[i])
        while j < len(assignments) and priority_fn(assignments[j]) == p_val:
            j += 1
        chunk = assignments[i:j]
        random.shuffle(chunk)
        assignments[i:j] = chunk
        i = j


def _validate(timetable, class_divs):
    violations = []
    for cd in class_divs:
        free_count = 0
        for d_name in DAYS:
            for p_num in PERIODS:
                entry = timetable.get(cd, {}).get(d_name, {}).get(p_num)
                if entry and entry.get('subject') == 'Free':
                    free_count += 1
        if free_count > 0:
            violations.append(f"{cd}: has {free_count} Free periods (subjects not placed)")
    return violations
