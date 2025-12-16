from pathlib import Path

# Files
DATA_DIR      = Path(__file__).parent
DISTANCE_CSV  = DATA_DIR / "distance_table.csv"
PACKAGE_CSV   = DATA_DIR / "package_file.csv"

# Vehicle / capacity
SPEED_MPH       = 18.0
TRUCK_CAPACITY  = 16
HUB_ADDRESS     = "Western Governors University"

# Constraint times (minutes after 08:00)
ARRIVAL_905_MIN   = 65    # 9:05 AM
ADDR_FIX_1020_MIN = 140   # 10:20 AM

# Constraint sets
ONLY_TRUCK2   = {3, 18, 36, 38}
DELAYED_905   = {6, 25, 28, 32}
ADDR_FIX_1020 = {9}

# Snapshots for rubric screenshots
SNAPSHOTS = ["08:55", "10:05", "12:45"]

# Default logging
DEBUG = False
