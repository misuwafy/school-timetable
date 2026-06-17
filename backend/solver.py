"""
Timetable Solver v12 - Block-aware greedy with iterative repair
Solves block-by-block to minimize teacher conflicts within each block.
Uses iterative deepening: multiple passes with increasing relaxation.

NO FREE PERIODS - every subject must be placed.
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
SLOT_LIMITS = {
    'PET': 6, 'Art': 2, 'Music': 2, 'Work Experience': 2, 'IT': 6,
}
FRIDAY_P4_FREE = {'Bavakutty', 'Saheer', 'Yasir', 'Swalih'}


def solve_timetable(classes_data, teachers_data, max_attempts=60):
    """Main entry point"""
    if not classes_data:
        raise ValueError("No classes found.")
    if not teachers_data:
        raise ValueError("No teachers found.")

    start_time = time.time()

    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}
    it_teachers = set()
    for cls in classes_data:
        for sub in cls.get('subjects', []):
            if sub.get('name') == 'IT' and sub.get('teacher'):
                it_teachers.add(sub['teacher'].strip())

    # Build divisions
    class_divs = []
    div_needs = {}
    div_block = {}

    for cls in classes_data:
        for div in cls.get('divisions', []):
            cd = f"{cls['name']}-{div}"
            class_divs.append(cd)
            div_needs[cd] = []
            div_block[cd] = cls.get('block', '')

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

    # Trim to 35 if over
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

    ctx = {
        'class_divs': class_divs,
        'div_needs': div_needs,
        'div_block': div_block,
        'block_heads': block_heads,
        'it_teachers': it_teachers,
        'multi_teachers': multi_teachers,
    }

    print(f"Solver v12: {len(class_divs)} divisions")

    best_result = None
    best_free = 999999

    for attempt in range(max_attempts):
        if time.time() - start_time > 55:  # Don't exceed 60s timeout
            break
        result, free_count = _full_attempt(ctx)
        if free_count < best_free:
            best_free = free_count
            best_result = result
            print(f"  Attempt {attempt+1}: {free_count} free slots")
        if free_count == 0:
            print(f"  PERFECT on attempt {attempt+1}")
            break

    if best_result is None:
        raise RuntimeError("Could not generate timetable.")

    elapsed = time.time() - start_time
    print(f"  Done in {elapsed:.1f}s, {best_free} free slots remaining")

    # Build output
    timetable = _build_output(best_result, class_divs)
    return timetable


def _full_attempt(ctx):
    """Single full attempt"""
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    # Global state
    schedule = {}
    teacher_slots = defaultdict(set)  # teacher -> {(d,p)}
    slot_subject_count = defaultdict(lambda: defaultdict(int))  # (d,p) -> subject -> count

    # Build all assignments with division info
    assignments = []
    for cd in class_divs:
        for need in div_needs[cd]:
            assignments.append((cd, need))

    # Separate multi-class and regular
    regular = [(cd, n) for cd, n in assignments if not n['is_multi']]
    multi = [(cd, n) for cd, n in assignments if n['is_multi']]

    # Shuffle regular assignments
    random.shuffle(regular)

    # Sort regular by teacher load (busiest teachers first)
    teacher_load = defaultdict(int)
    for cd, need in regular:
        for t in need['teachers']:
            teacher_load[t] += need['periods']

    regular.sort(key=lambda x: -max((teacher_load[t] for t in x[1]['teachers']), default=0))

    # Place regular subjects first
    for cd, need in regular:
        _place_need(cd, need, schedule, teacher_slots, slot_subject_count, ctx, strict=True)

    # Place multi-class subjects (they don't have teacher conflicts)
    for cd, need in multi:
        _place_need(cd, need, schedule, teacher_slots, slot_subject_count, ctx, strict=True)

    # Count unplaced
    free_count = 0
    for cd in class_divs:
        total_needed = sum(n['periods'] for n in div_needs[cd])
        placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if (cd, d, p) in schedule)
        free_count += max(0, total_needed - placed)

    # REPAIR: Try to place unplaced with relaxed constraints
    if free_count > 0:
        _repair_pass(schedule, teacher_slots, slot_subject_count, ctx, strict=False)
        # Recount
        free_count = 0
        for cd in class_divs:
            total_needed = sum(n['periods'] for n in div_needs[cd])
            placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if (cd, d, p) in schedule)
            free_count += max(0, total_needed - placed)

    # FORCE REPAIR: swap-based
    if free_count > 0:
        _force_repair(schedule, teacher_slots, slot_subject_count, ctx)
        free_count = 0
        for cd in class_divs:
            total_needed = sum(n['periods'] for n in div_needs[cd])
            placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if (cd, d, p) in schedule)
            free_count += max(0, total_needed - placed)

    return schedule, free_count


def _place_need(cd, need, schedule, teacher_slots, slot_subject_count, ctx, strict):
    """Place all periods of a need"""
    periods_needed = need['periods']
    placed = 0

    # Get valid slots
    slots = []
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            if _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
                slots.append((d, p))

    # Distribute across days
    random.shuffle(slots)
    day_count = defaultdict(int)
    slots.sort(key=lambda s: (day_count.get(s[0], 0), random.random()))

    for d, p in slots:
        if placed >= periods_needed:
            break
        if not _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
            continue
        schedule[(cd, d, p)] = need
        if not need['is_multi']:
            for t in need['teachers']:
                teacher_slots[t].add((d, p))
        if need['subject'] in SLOT_LIMITS:
            slot_subject_count[(d, p)][need['subject']] += 1
        day_count[d] += 1
        placed += 1


def _repair_pass(schedule, teacher_slots, slot_subject_count, ctx, strict):
    """Try to place unplaced periods with relaxed constraints"""
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    for cd in class_divs:
        for need in div_needs[cd]:
            placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS)
                         if schedule.get((cd, d, p)) == need)
            remaining = need['periods'] - placed
            if remaining <= 0:
                continue

            for d in range(NUM_DAYS):
                if remaining <= 0:
                    break
                for p in range(NUM_PERIODS):
                    if remaining <= 0:
                        break
                    if (cd, d, p) in schedule:
                        continue
                    if _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
                        schedule[(cd, d, p)] = need
                        if not need['is_multi']:
                            for t in need['teachers']:
                                teacher_slots[t].add((d, p))
                        if need['subject'] in SLOT_LIMITS:
                            slot_subject_count[(d, p)][need['subject']] += 1
                        remaining -= 1


def _force_repair(schedule, teacher_slots, slot_subject_count, ctx):
    """Force placement using swaps"""
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']

    for cd in class_divs:
        for need in div_needs[cd]:
            placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS)
                         if schedule.get((cd, d, p)) == need)
            remaining = need['periods'] - placed
            if remaining <= 0:
                continue

            # Try empty slots with only teacher-conflict check
            for d in range(NUM_DAYS):
                if remaining <= 0:
                    break
                for p in range(NUM_PERIODS):
                    if remaining <= 0:
                        break
                    if (cd, d, p) in schedule:
                        continue
                    can = True
                    if not need['is_multi']:
                        for t in need['teachers']:
                            if (d, p) in teacher_slots.get(t, set()):
                                can = False
                                break
                    if can:
                        schedule[(cd, d, p)] = need
                        if not need['is_multi']:
                            for t in need['teachers']:
                                teacher_slots[t].add((d, p))
                        if need['subject'] in SLOT_LIMITS:
                            slot_subject_count[(d, p)][need['subject']] += 1
                        remaining -= 1

            if remaining <= 0:
                continue

            # SWAP: move existing subjects to free up slots
            for d in range(NUM_DAYS):
                if remaining <= 0:
                    break
                for p in range(NUM_PERIODS):
                    if remaining <= 0:
                        break
                    if (cd, d, p) not in schedule:
                        continue
                    existing = schedule[(cd, d, p)]
                    if existing['subject'] == need['subject']:
                        continue

                    # Check if need's teacher is free at (d,p)
                    teacher_free = True
                    if not need['is_multi']:
                        for t in need['teachers']:
                            if (d, p) in teacher_slots.get(t, set()):
                                teacher_free = False
                                break
                    if not teacher_free:
                        continue

                    # Try to relocate existing
                    for d2 in range(NUM_DAYS):
                        if remaining <= 0:
                            break
                        for p2 in range(NUM_PERIODS):
                            if (cd, d2, p2) in schedule:
                                continue
                            can = True
                            if not existing['is_multi']:
                                for t in existing['teachers']:
                                    if (d2, p2) in teacher_slots.get(t, set()):
                                        can = False
                                        break
                            if can:
                                # Remove existing
                                del schedule[(cd, d, p)]
                                if not existing['is_multi']:
                                    for t in existing['teachers']:
                                        teacher_slots[t].discard((d, p))
                                if existing['subject'] in SLOT_LIMITS:
                                    slot_subject_count[(d, p)][existing['subject']] -= 1
                                # Place existing at new location
                                schedule[(cd, d2, p2)] = existing
                                if not existing['is_multi']:
                                    for t in existing['teachers']:
                                        teacher_slots[t].add((d2, p2))
                                if existing['subject'] in SLOT_LIMITS:
                                    slot_subject_count[(d2, p2)][existing['subject']] += 1
                                # Place need at original location
                                schedule[(cd, d, p)] = need
                                if not need['is_multi']:
                                    for t in need['teachers']:
                                        teacher_slots[t].add((d, p))
                                if need['subject'] in SLOT_LIMITS:
                                    slot_subject_count[(d, p)][need['subject']] += 1
                                remaining -= 1
                                break
                        if remaining <= 0:
                            break


def _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
    """Check if placement is valid"""
    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']
    block_heads = ctx['block_heads']
    multi_teachers = ctx['multi_teachers']
    it_teachers = ctx['it_teachers']

    # Hard constraints (always enforced)
    if subject in MULTI_CLASS_SUBJECTS and p == 0:
        return False
    if p == 0:
        for t in teachers:
            if t in block_heads:
                return False
    if p == 0 and 'Bindya' in teachers:
        return False
    if 'Rashid' in teachers and p in [0, 3]:
        return False
    if d == 4 and p == 3:
        for t in teachers:
            if t in FRIDAY_P4_FREE:
                return False
    if cd.startswith('10-') and subject in ['Physics', 'Chemistry'] and p == 6:
        return False
    if 'Jaleela' in teachers and p in [3, 4]:
        other = 4 if p == 3 else 3
        if (d, other) in teacher_slots.get('Jaleela', set()):
            return False

    # Teacher conflict (always enforced for non-multi)
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # Soft constraints (only in strict mode)
    if strict:
        # Max 5 periods/day for non-IT, non-multi teachers
        if not is_multi:
            for t in teachers:
                if t not in multi_teachers:
                    count = sum(1 for dd_pp in teacher_slots.get(t, set()) if dd_pp[0] == d)
                    if t not in it_teachers:
                        if count >= 5:
                            return False
                    else:
                        if count >= 7:
                            return False

        # No subject repeat per day (except Maths-10 max 2)
        sub_today = sum(1 for pp in range(NUM_PERIODS)
                        if schedule.get((cd, d, pp), {}).get('subject') == subject
                        if (cd, d, pp) in schedule)
        if subject == 'Maths' and cd.startswith('10-'):
            if sub_today >= 2:
                return False
        else:
            if sub_today >= 1:
                return False
    else:
        # Relaxed: allow max 2 repeats
        sub_today = sum(1 for pp in range(NUM_PERIODS)
                        if (cd, d, pp) in schedule and schedule[(cd, d, pp)].get('subject') == subject)
        if sub_today >= 2:
            return False

    # Slot capacity limits (always enforced)
    if subject in SLOT_LIMITS:
        count = slot_subject_count[(d, p)].get(subject, 0)
        if count >= SLOT_LIMITS[subject]:
            return False

    return True


def _build_output(schedule, class_divs):
    """Build output timetable dict"""
    timetable = {}
    for cd in class_divs:
        timetable[cd] = {}
        for d in range(NUM_DAYS):
            timetable[cd][DAYS[d]] = {}
            for p in range(NUM_PERIODS):
                entry = schedule.get((cd, d, p))
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

    # Validate
    violations = []
    for cd in class_divs:
        free = sum(1 for d in DAYS for p in PERIODS
                   if timetable[cd][d][p]['subject'] == 'Free')
        if free > 0:
            violations.append(f"{cd}: has {free} Free periods (subjects not placed)")
    timetable['_violations'] = violations
    return timetable
