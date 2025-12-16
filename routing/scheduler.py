from routing.planner import plan_route_for_truck
from routing.simulate import simulate_route

def run_full_plan(ds, packages: list):
    """
    Two-driver scheduler: start Truck 1 & 2 at t=0 (08:00), then reuse the earlier-free slot.
    """
    def remaining():
        return [p for p in packages if p.status == "at_hub"]

    miles_by_truck = {1: 0.0, 2: 0.0, 3: 0.0}
    counts_by_truck = {1: 0, 2: 0, 3: 0}
    trips = []

    def dispatch(truck_id: int, depart_min: int):
        pkgs = plan_route_for_truck(ds, remaining(), truck_id=truck_id, depart_time_min=depart_min)
        if not pkgs:
            return 0.0, depart_min, 0
        for p in pkgs:
            p.status = "en_route"
        miles, end_time, _legs = simulate_route(ds, pkgs, depart_min, truck_id=truck_id)
        trips.append({"truck": truck_id, "depart": depart_min, "return": end_time, "miles": miles, "count": len(pkgs)})
        miles_by_truck[truck_id] += miles
        counts_by_truck[truck_id] += len(pkgs)
        return miles, end_time, len(pkgs)

    # Wave 1
    slotA = {"truck": 1, "free": 0}
    slotB = {"truck": 2, "free": 0}
    used = {1, 2}

    _, endA, _ = dispatch(1, 0); slotA["free"] = endA
    _, endB, _ = dispatch(2, 0); slotB["free"] = endB

    # Subsequent waves
    safety = 0
    while remaining() and safety < 100:
        safety += 1
        slot = slotA if slotA["free"] <= slotB["free"] else slotB
        depart = slot["free"]
        rem = remaining()

        needs_t2 = any(getattr(p, "truck_restriction", None) == 2 for p in rem)
        if needs_t2:
            next_truck = 2
        else:
            next_truck = 3 if 3 not in used else slot["truck"]
            used.add(next_truck)

        _, end_time, count = dispatch(next_truck, depart)
        if count == 0:
            unlocks = []
            for p in rem:
                at = getattr(p, "available_time_min", 0)
                ft = getattr(p, "address_fix_time_min", 0)
                if at and at > depart: unlocks.append(at)
                if ft and ft > depart: unlocks.append(ft)
            if unlocks:
                depart2 = min(unlocks)
                _, end_time, count = dispatch(next_truck, depart2)
            if count == 0:
                break

        slot["truck"] = next_truck
        slot["free"] = end_time

    total_miles = sum(miles_by_truck.values())
    delivered = sum(1 for p in packages if p.status == "delivered")
    return {
        "trucks": [
            {"id": 1, "miles": miles_by_truck[1], "end": max([t["return"] for t in trips if t["truck"] == 1], default=0), "count": counts_by_truck[1]},
            {"id": 2, "miles": miles_by_truck[2], "end": max([t["return"] for t in trips if t["truck"] == 2], default=0), "count": counts_by_truck[2]},
            {"id": 3, "miles": miles_by_truck[3], "end": max([t["return"] for t in trips if t["truck"] == 3], default=0), "count": counts_by_truck[3]},
        ],
        "total_miles": total_miles,
        "delivered": delivered,
        "total_packages": len(packages),
        "trips": trips,
    }
