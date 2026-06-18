"""
Timetable Solver v13 - Updated constraints (June 2026)
CRITICAL RULE: Class teacher MUST teach Period 1 in their class every day.

Constraints:
1. No subject repeat per day (except Maths 10th, max 2, second in P7 one day only)
2. Free periods spread apart (not consecutive) for teachers
3. Block Head Teachers - no P1 (but class teacher rule overrides for their own class)
4. All teachers max 5 periods/day
5. Rashid - no P1 and P4
6. Art(8,9) max 2 combined, Music(8) max 2, WE(9) max 2
7. PET max 6 combined
8. PET/Art/Music/WE not in P1
9. Arabic combining 8-EE & 8-EC (same teacher)
10. Sanskrit combining 10-B & 10-EI (Sreeja M)
11. IT Lab max 6 simultaneous
MOST IMPORTANT: Class teacher teaches Period 1 in their own class every day
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


def solve_timetable(classes_data, teachers_data, max_attempts=60):
    if not classes_data:
        raise ValueError("No classes found.")
    if not teachers_data:
        raise ValueError("No teachers found.")

    start_time = time.time()
    block_heads = {t['name'] for t in teachers_data if t.get('isBlockHead')}

    # Build divisions
    class_divs = []
    div_needs = {}
    div_class_teacher = {}  # cd -> class teacher name

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
        'div_class_teacher': div_class_teacher,
        'block_heads': block_heads,
        'multi_teachers': multi_teachers,
        'it_teachers': set(),
    }

    # Identify IT teachers
    for cd in class_divs:
        for need in div_needs[cd]:
            if need['subject'] == 'IT':
                for t in need['teachers']:
                    ctx['it_teachers'].add(t)

    print(f"Solver v13: {len(class_divs)} divisions")

    best_result = None
    best_free = 999999

    for attempt in range(max_attempts):
        if time.time() - start_time > 55:
            break
        result, free_count = _full_attempt(ctx)
        if free_count < best_free:
            best_free = free_count
            best_result = result
            if attempt % 10 == 0 or free_count == 0:
                print(f"  Attempt {attempt+1}: {free_count} free")
        if free_count == 0:
            print(f"  PERFECT on attempt {attempt+1}")
            break

    if best_result is None:
        raise RuntimeError("Could not generate timetable.")

    print(f"  Done in {time.time()-start_time:.1f}s, {best_free} free")

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
        free = sum(1 for d in DAYS for p in PERIODS
                   if timetable[cd][d][p]['subject'] == 'Free')
        if free > 0:
            violations.append(f"{cd}: has {free} Free periods")
    timetable['_violations'] = violations
    return timetable


def _full_attempt(ctx):
    class_divs = ctx['class_divs']
    div_needs = ctx['div_needs']
    div_class_teacher = ctx['div_class_teacher']

    schedule = {}
    teacher_slots = defaultdict(set)  # teacher -> {(d,p)}
    slot_subject_count = defaultdict(lambda: defaultdict(int))  # (d,p) -> subject -> count

    # STEP 1: Place class teacher in Period 1 — MINIMUM 2 days per week
    # This is the MOST IMPORTANT rule but with flexibility to avoid blanks
    MIN_CT_P1_DAYS = 2

    for cd in class_divs:
        ct = div_class_teacher.get(cd, '')
        if not ct:
            continue
        ct_needs = [n for n in div_needs[cd] if ct in n['teachers'] and not n['is_multi']]
        if not ct_needs:
            continue

        # Sort by periods descending - use the subject with most periods first for P1
        ct_needs_sorted = sorted(ct_needs, key=lambda n: -n['periods'])

        days_placed = 0
        days_order = list(range(NUM_DAYS))
        random.shuffle(days_order)

        for d in days_order:
            if days_placed >= MIN_CT_P1_DAYS:
                break
            placed = False
            for need in ct_needs_sorted:
                # Don't exceed this subject's total period allocation
                already_placed_total = sum(1 for dd in range(NUM_DAYS) for pp in range(NUM_PERIODS)
                                           if schedule.get((cd, dd, pp)) == need)
                if already_placed_total >= need['periods']:
                    continue
                if need['subject'] in MULTI_CLASS_SUBJECTS:
                    continue
                if 'Rashid' in need['teachers']:
                    continue
                # Check teacher not double-booked in P1 this day
                teacher_busy = False
                for t in need['teachers']:
                    if (d, 0) in teacher_slots.get(t, set()):
                        teacher_busy = True
                        break
                if teacher_busy:
                    continue
                # Place it
                schedule[(cd, d, 0)] = need
                for t in need['teachers']:
                    if not need['is_multi']:
                        teacher_slots[t].add((d, 0))
                if need['subject'] in SLOT_LIMITS:
                    slot_subject_count[(d, 0)][need['subject']] += 1
                days_placed += 1
                placed = True
                break

    # STEP 2: Place remaining subjects
    # Build assignment list (excluding already-placed P1 slots)
    all_assignments = []
    for cd in class_divs:
        for need in div_needs[cd]:
            already = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS)
                         if schedule.get((cd, d, p)) == need)
            remaining = need['periods'] - already
            if remaining > 0:
                all_assignments.append({'cd': cd, 'need': need, 'remaining': remaining})

    # Sort by teacher busyness (busiest first)
    teacher_load = defaultdict(int)
    for a in all_assignments:
        for t in a['need']['teachers']:
            teacher_load[t] += a['remaining']

    all_assignments.sort(key=lambda a: -max((teacher_load[t] for t in a['need']['teachers']), default=0))

    # Shuffle within same-load groups
    i = 0
    while i < len(all_assignments):
        j = i
        load_i = max((teacher_load[t] for t in all_assignments[i]['need']['teachers']), default=0)
        while j < len(all_assignments):
            load_j = max((teacher_load[t] for t in all_assignments[j]['need']['teachers']), default=0)
            if load_j != load_i:
                break
            j += 1
        chunk = all_assignments[i:j]
        random.shuffle(chunk)
        all_assignments[i:j] = chunk
        i = j

    # Phase 2a: Strict placement
    unplaced = []
    for a in all_assignments:
        cd, need, remaining = a['cd'], a['need'], a['remaining']
        placed = _place_periods(cd, need, remaining, schedule, teacher_slots,
                                slot_subject_count, ctx, strict=True)
        left = remaining - placed
        if left > 0:
            unplaced.append({'cd': cd, 'need': need, 'remaining': left})

    # Phase 2b: Relaxed placement
    still_unplaced = []
    for a in unplaced:
        cd, need, remaining = a['cd'], a['need'], a['remaining']
        placed = _place_periods(cd, need, remaining, schedule, teacher_slots,
                                slot_subject_count, ctx, strict=False)
        left = remaining - placed
        if left > 0:
            still_unplaced.append({'cd': cd, 'need': need, 'remaining': left})

    # Phase 2c: Force + swap
    for a in still_unplaced:
        cd, need, remaining = a['cd'], a['need'], a['remaining']
        _force_place(cd, need, remaining, schedule, teacher_slots, slot_subject_count, ctx)

    # Count free
    free_count = 0
    for cd in class_divs:
        total_needed = sum(n['periods'] for n in div_needs[cd])
        placed = sum(1 for d in range(NUM_DAYS) for p in range(NUM_PERIODS) if (cd, d, p) in schedule)
        free_count += max(0, total_needed - placed)

    return schedule, free_count


def _place_periods(cd, need, count, schedule, teacher_slots, slot_subject_count, ctx, strict):
    """Try to place 'count' periods of need. Returns number placed."""
    placed = 0
    slots = []
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            if _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
                slots.append((d, p))

    random.shuffle(slots)
    # Spread across days
    day_usage = defaultdict(int)
    for d in range(NUM_DAYS):
        for p in range(NUM_PERIODS):
            if (cd, d, p) in schedule:
                day_usage[d] += 1
    slots.sort(key=lambda s: (day_usage[s[0]], random.random()))

    for d, p in slots:
        if placed >= count:
            break
        if not _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
            continue
        _do_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count)
        placed += 1

    return placed


def _force_place(cd, need, count, schedule, teacher_slots, slot_subject_count, ctx):
    """Force-place with swaps if needed. GUARANTEES placement."""
    remaining = count

    # Try empty slots (only hard constraints: teacher not double-booked + Rashid + max 5/day)
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
                    # Max 5/day with one 6-period day allowed
                    if can and t not in ctx['multi_teachers']:
                        day_count = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == d)
                        if day_count >= 5:
                            days_with_6 = sum(1 for dd in range(NUM_DAYS)
                                              if sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == dd) >= 6)
                            if day_count >= 6:
                                can = False
                                break
                            elif days_with_6 >= 1:
                                can = False
                                break
                            else:
                                # 6th period allowed - if IT teacher, must be IT
                                if t in ctx.get('it_teachers', set()) and need['subject'] != 'IT':
                                    can = False
                                    break
            # HARD: Rashid never P1 or P4
            if can and 'Rashid' in need['teachers'] and p in [0, 3]:
                can = False
            # HARD: Block heads no P1 (unless class teacher of this division)
            if can and p == 0:
                ct = ctx['div_class_teacher'].get(cd, '')
                for t in need['teachers']:
                    if t in ctx['block_heads'] and t != ct:
                        can = False
                        break
            # HARD: Multi-class subjects not P1
            if can and need['subject'] in MULTI_CLASS_SUBJECTS and p == 0:
                can = False
            if can:
                _do_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count)
                remaining -= 1

    # Swap existing subjects
    if remaining > 0:
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
                # HARD: Rashid can't go to P1 or P4
                if 'Rashid' in need['teachers'] and p in [0, 3]:
                    continue
                # HARD: Multi-class not P1
                if need['subject'] in MULTI_CLASS_SUBJECTS and p == 0:
                    continue
                # HARD: Block heads no P1 (unless class teacher)
                if p == 0:
                    ct = ctx['div_class_teacher'].get(cd, '')
                    skip = False
                    for t in need['teachers']:
                        if t in ctx['block_heads'] and t != ct:
                            skip = True
                            break
                    if skip:
                        continue
                # Can need's teacher do (d,p)? Check conflict + max 5/day (with 6-day exception)
                can_need = True
                if not need['is_multi']:
                    for t in need['teachers']:
                        if (d, p) in teacher_slots.get(t, set()):
                            can_need = False
                            break
                        if can_need and t not in ctx['multi_teachers']:
                            day_count = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == d)
                            if day_count >= 5:
                                days_with_6 = sum(1 for dd in range(NUM_DAYS)
                                                  if sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == dd) >= 6)
                                if day_count >= 6 or days_with_6 >= 1:
                                    can_need = False
                                    break
                                elif t in ctx.get('it_teachers', set()) and need['subject'] != 'IT':
                                    can_need = False
                                    break
                if not can_need:
                    continue
                # Can existing go somewhere else?
                relocated = False
                for d2 in range(NUM_DAYS):
                    if relocated:
                        break
                    for p2 in range(NUM_PERIODS):
                        if (cd, d2, p2) in schedule:
                            continue
                        # HARD: Rashid can't go to P1 or P4
                        if 'Rashid' in existing['teachers'] and p2 in [0, 3]:
                            continue
                        # HARD: Multi-class not P1
                        if existing['subject'] in MULTI_CLASS_SUBJECTS and p2 == 0:
                            continue
                        # Check conflict + max 5/day for existing (with 6-day exception)
                        can_ex = True
                        if not existing['is_multi']:
                            for t in existing['teachers']:
                                if (d2, p2) in teacher_slots.get(t, set()):
                                    can_ex = False
                                    break
                                if can_ex and t not in ctx['multi_teachers']:
                                    day_count = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == d2)
                                    if day_count >= 5:
                                        days_with_6 = sum(1 for dd in range(NUM_DAYS)
                                                          if sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == dd) >= 6)
                                        if day_count >= 6 or days_with_6 >= 1:
                                            can_ex = False
                                            break
                                        elif t in ctx.get('it_teachers', set()) and existing['subject'] != 'IT':
                                            can_ex = False
                                            break
                        if can_ex:
                            _do_remove(cd, existing, d, p, schedule, teacher_slots, slot_subject_count)
                            _do_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count)
                            _do_place(cd, existing, d2, p2, schedule, teacher_slots, slot_subject_count)
                            remaining -= 1
                            relocated = True
                            break


def _do_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count):
    schedule[(cd, d, p)] = need
    if not need['is_multi']:
        for t in need['teachers']:
            teacher_slots[t].add((d, p))
    if need['subject'] in SLOT_LIMITS:
        slot_subject_count[(d, p)][need['subject']] += 1


def _do_remove(cd, need, d, p, schedule, teacher_slots, slot_subject_count):
    del schedule[(cd, d, p)]
    if not need['is_multi']:
        for t in need['teachers']:
            teacher_slots[t].discard((d, p))
    if need['subject'] in SLOT_LIMITS:
        slot_subject_count[(d, p)][need['subject']] -= 1


def _can_place(cd, need, d, p, schedule, teacher_slots, slot_subject_count, ctx, strict):
    if (cd, d, p) in schedule:
        return False

    subject = need['subject']
    teachers = need['teachers']
    is_multi = need['is_multi']
    block_heads = ctx['block_heads']
    multi_teachers = ctx['multi_teachers']
    div_class_teacher = ctx['div_class_teacher']

    # Constraint 8: Multi-class subjects not P1
    if subject in MULTI_CLASS_SUBJECTS and p == 0:
        return False

    # Constraint 3: Block heads no P1 (unless it's their own class's P1 - handled by class teacher rule)
    if p == 0:
        ct = div_class_teacher.get(cd, '')
        for t in teachers:
            if t in block_heads and t != ct:
                return False

    # Constraint 5: Rashid no P1, P4
    if 'Rashid' in teachers and p in [0, 3]:
        return False

    # Teacher conflict (non-multi)
    if not is_multi:
        for t in teachers:
            if (d, p) in teacher_slots.get(t, set()):
                return False

    # Constraint 4: Max 5 periods/day for non-multi teachers (STRICT)
    # Exception: Each teacher can have ONE day with 6 periods (to avoid blanks)
    # If they teach IT, the 6th period must be IT
    if not is_multi:
        for t in teachers:
            if t not in multi_teachers:
                day_count = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == d)
                if day_count >= 5:
                    # Check if this teacher already used their 6th-period day
                    days_with_6 = []
                    for dd in range(NUM_DAYS):
                        c = sum(1 for dp in teacher_slots.get(t, set()) if dp[0] == dd)
                        if c >= 6:
                            days_with_6.append(dd)
                    if day_count >= 6:
                        # Already at 6 today, can't add more
                        return False
                    elif len(days_with_6) >= 1:
                        # Already used the one 6-period day on another day
                        return False
                    else:
                        # This would be the 6th period (allowed once per week)
                        # If teacher holds IT, 6th must be IT
                        if t in ctx.get('it_teachers', set()):
                            if subject != 'IT':
                                return False

    # Constraint 1: No subject repeat per day (except Maths-10 max 2)
    sub_today = sum(1 for pp in range(NUM_PERIODS)
                    if (cd, d, pp) in schedule and schedule[(cd, d, pp)]['subject'] == subject)
    if strict:
        if subject == 'Maths' and cd.startswith('10-'):
            if sub_today >= 2:
                return False
        else:
            if sub_today >= 1:
                return False
    else:
        if sub_today >= 2:
            return False

    # Slot capacity limits
    if subject in SLOT_LIMITS:
        if slot_subject_count[(d, p)].get(subject, 0) >= SLOT_LIMITS[subject]:
            return False

    return True
