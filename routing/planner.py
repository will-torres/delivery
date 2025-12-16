import re
from config import TRUCK_CAPACITY, HUB_ADDRESS

def _deadline_to_minutes_since_8(deadline: str) -> int:
    s = (deadline or "").strip().upper()
    if s in {"", "EOD"}:
        hh, mm = 17, 0
    else:
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*(AM|PM)?\s*$", s)
        if m:
            hh = int(m.group(1)); mm = int(m.group(2)); ap = m.group(3)
            if ap == "PM" and hh != 12: hh += 12
            if ap == "AM" and hh == 12: hh = 0
        else:
            try:
                hh = int(s); mm = 0
            except:
                hh, mm = 17, 0
    return max(0, (hh * 60 + mm) - (8 * 60))

def _eligible_for_truck(p, truck_id: int, depart_min: int) -> bool:
    if getattr(p, "truck_restriction", None) == 2 and truck_id != 2:
        return False
    at = getattr(p, "available_time_min", None)
    if at is not None and depart_min < at:
        return False
    ft = getattr(p, "address_fix_time_min", None)
    if ft is not None and depart_min < ft:
        return False
    return True

def _two_opt_once(route, ds):
    if len(route) < 4:
        return route
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(0, len(best) - 3):
            A = HUB_ADDRESS if i == 0 else best[i - 1].address
            B = best[i].address
            for k in range(i + 1, len(best) - 1):
                C = best[k].address
                D = best[k + 1].address
                before = ds.get_distance(A, B) + ds.get_distance(C, D)
                after  = ds.get_distance(A, C) + ds.get_distance(B, D)
                if after + 1e-9 < before:
                    best[i:k+1] = reversed(best[i:k+1])
                    improved = True
                    break
            if improved:
                break
    return best

def plan_route_for_truck(ds, packages: list, truck_id: int, depart_time_min: int):
    # 1) filter candidates
    cand = []
    for p in packages:
        if getattr(p, "status", "at_hub") != "at_hub":
            continue
        if not _eligible_for_truck(p, truck_id, depart_time_min):
            continue
        cand.append(p)
    if not cand:
        return []

    # 2) greedy NN (distance, tie-break earlier deadline)
    remaining = cand[:]
    route = []
    curr = HUB_ADDRESS
    while remaining and len(route) < TRUCK_CAPACITY:
        best_p, best_key = None, None
        for p in remaining:
            d  = ds.get_distance(curr, p.address)
            dl = _deadline_to_minutes_since_8(getattr(p, "deadline", "EOD"))
            key = (d, dl)
            if best_key is None or key < best_key:
                best_key = key; best_p = p
        route.append(best_p)
        remaining.remove(best_p)
        curr = best_p.address

    # 3) shave crossings
    return _two_opt_once(route, ds)
