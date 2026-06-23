"""
Local Timetable Generator - Run on your laptop with full CPU power.
Connects to your Supabase database, generates timetable, saves it back.

Usage: python generate_local.py
"""
import json
import requests
import sys
import os

# Your live server
SERVER_URL = "https://timetable.synaptalogic.com"

def main():
    print("=" * 60)
    print("  SCHOOL TIMETABLE GENERATOR (Local)")
    print("  Running on your laptop with full CPU power")
    print("=" * 60)
    print()

    # Step 1: Fetch data from server
    print("[1/3] Fetching data from server...")
    try:
        teachers = requests.get(f"{SERVER_URL}/api/teachers").json()
        classes = requests.get(f"{SERVER_URL}/api/classes").json()
        print(f"  ✓ {len(teachers)} teachers, {len(classes)} classes loaded")
    except Exception as e:
        print(f"  ✗ Failed to fetch data: {e}")
        sys.exit(1)

    classes_data = [
        {
            "name": c["name"],
            "divisions": c["divisions"],
            "block": c.get("block", ""),
            "classType": c.get("classType", ""),
            "classTeacher": c.get("classTeacher", ""),
            "subjects": c.get("subjects", [])
        }
        for c in classes
    ]
    teachers_data = [
        {
            "name": t["name"],
            "maxPeriodsPerDay": t.get("maxPeriodsPerDay", 5),
            "isBlockHead": t.get("isBlockHead", False),
            "headOfBlock": t.get("headOfBlock", "")
        }
        for t in teachers
    ]

    # Step 2: Run solver locally
    print()
    print("[2/3] Running OR-Tools solver locally (this may take 10-30 minutes)...")
    print("  Using all CPU cores. Do NOT close this window.")
    print()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    from solver import solve_timetable

    try:
        timetable = solve_timetable(classes_data, teachers_data)
    except Exception as e:
        print(f"\n  ✗ Solver failed: {e}")
        sys.exit(1)

    violations = timetable.pop('_violations', [])
    print(f"\n  ✓ Timetable generated!")
    print(f"  Violations: {len(violations)}")
    if violations:
        for v in violations[:10]:
            print(f"    ⚠️ {v}")

    # Step 3: Upload to server
    print()
    print("[3/3] Uploading timetable to server...")
    try:
        # Save as current timetable
        res = requests.post(f"{SERVER_URL}/api/timetable", json=timetable)
        if res.ok:
            print("  ✓ Timetable saved to server!")
        else:
            print(f"  ⚠️ Server save returned: {res.status_code}")
            # Save locally as backup
            with open("timetable_result.json", "w") as f:
                json.dump(timetable, f)
            print("  ✓ Saved locally as timetable_result.json")
    except Exception as e:
        print(f"  ⚠️ Upload failed: {e}")
        with open("timetable_result.json", "w") as f:
            json.dump(timetable, f)
        print("  ✓ Saved locally as timetable_result.json")

    print()
    print("=" * 60)
    print("  DONE! Refresh your browser to see the timetable.")
    print("=" * 60)


if __name__ == "__main__":
    main()
