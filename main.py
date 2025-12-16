
# Delivery routing system using a custom hash table and greedy nearest-feasible algorithm with priority selection


from config import DISTANCE_CSV, PACKAGE_CSV, ONLY_TRUCK2, DELAYED_905, ADDR_FIX_1020, ARRIVAL_905_MIN, ADDR_FIX_1020_MIN, SNAPSHOTS
from core.hash_table import HashTable
from data.distance_service import DistanceService
from routing.scheduler import run_full_plan
from reporting.status import status_at, minutes_to_str
from ui.cli import UserInterface

class DeliveryOptimizer:
    def __init__(self, hash_table, distance_service):
        self.hash_table = hash_table
        self.distance_service = distance_service
        self.max_total_miles = 140
        self.result = {}

    def load_packages_from_file(self, filename: str):
        """
        Load package data from CSV into the custom HashTable.
        Expected header (any row containing 'Package' and 'ID' is treated as header):
          0: Package ID
          1: Address
          2: City
          3: State
          4: Zip
          5: Delivery Deadline (e.g., '10:30 AM', 'EOD')
          6: Weight
          7: Special Notes (optional)
        """
        import csv, os

        if not os.path.exists(filename):
            print(f"Package file not found: {filename}")
            return

        with open(filename, "r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        # Find header row
        header_row = -1
        for i, row in enumerate(rows):
            if not row:
                continue
            # robust match for funky headers like 'Package\nID'
            joined = " ".join(str(c) for c in row).lower()
            if "package" in joined and "id" in joined:
                header_row = i
                break

        if header_row == -1:
            print("Could not find header in package_file.csv")
            return

        loaded = 0
        for r in rows[header_row + 1:]:
            if not r or len(r) < 7:
                continue
            try:
                package_id = int(str(r[0]).strip())
            except:
                continue  # skip non-data rows

            address       = str(r[1]).strip()
            city          = str(r[2]).strip()
            state         = str(r[3]).strip() if len(r) > 3 else "UT"
            zip_code      = str(r[4]).strip() if len(r) > 4 else ""
            deadline      = str(r[5]).strip() if len(r) > 5 else "EOD"
            weight        = str(r[6]).strip() if len(r) > 6 else ""
            special_notes = str(r[7]).strip() if len(r) > 7 else ""

            # Insert into custom hash table (status starts at 'at_hub')
            self.hash_table.insert(
                package_id=package_id,
                address=address,
                deadline=deadline,
                city=city,
                zip_code=zip_code,
                weight=weight,
                status="at_hub",
                state=state,
                special_notes=special_notes,
            )
            loaded += 1

        print(f"Loaded {loaded} packages into the system")


def _apply_constraints(packages):
    for p in packages:
        if p.package_id in ONLY_TRUCK2:
            p.truck_restriction = 2
        if p.package_id in DELAYED_905:
            p.available_time_min = ARRIVAL_905_MIN
        if p.package_id in ADDR_FIX_1020:
            p.address_fix_time_min = ADDR_FIX_1020_MIN

def main():
    print("WGUPS Delivery Routing Program Starting...")
    print("Initializing system components...")

    ht = HashTable(64)
    ds = DistanceService()

    print("Loading distance data...")
    ds.load_distance_data(str(DISTANCE_CSV))

    optimizer = DeliveryOptimizer(ht, ds)
    print("Loading package data...")
    optimizer.load_packages_from_file(str(PACKAGE_CSV))

    packages = list(ht.get_all_packages())
    _apply_constraints(packages)
    print(f"Loaded {len(packages)} packages into the system")

    print("\nStarting delivery optimization...")
    result = run_full_plan(ds, packages)
    optimizer.result = result  # for UI access

    # Summary
    print("\nOptimization Results:")
    print(f"Total miles traveled: {result['total_miles']:.1f}")
    print(f"Maximum allowed: 140")
    ok = "Yes" if result["total_miles"] <= 140 else "No"
    print(f"Constraint satisfied: {ok}")
    print(f"Packages delivered: {result['delivered']}/{result['total_packages']}")

    print("\nFinal Delivery Status by Truck:")
    for t in result["trucks"]:
        print(f"Truck {t['id']}: {t['count']} packages delivered, {t['miles']:.1f} miles")

    # Timeline
    trips = result.get("trips", [])
    if trips:
        print("\nTrip timeline (max two trucks active):")
        for tr in sorted(trips, key=lambda x: x["depart"]):
            dep = minutes_to_str(tr["depart"]); ret = minutes_to_str(tr["return"])
            print(f"  Truck {tr['truck']}: {dep} → {ret} | {tr['count']} pkgs | {tr['miles']:.1f} mi")

    # Snapshots for D1–D3
    for ts in SNAPSHOTS:
        status_at(ts, ht, result)

    print("\nStarting user interface...")
    ui = UserInterface(ht, optimizer)  # UI reads optimizer.result
    ui.display_main_menu()

if __name__ == "__main__":
    main()
