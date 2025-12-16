import re

def minutes_to_str(m: int) -> str:
    total = 8 * 60 + int(m)
    h = total // 60; mi = total % 60
    return f"{h:02d}:{mi:02d}"

def _clock_to_min_since_8(s: str) -> int:
    s = (s or "").strip().upper()
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*(AM|PM)?\s*$", s)
    if not m:
        raise ValueError(f"Bad time format: {s!r}")
    h = int(m.group(1)); mi = int(m.group(2)); ap = m.group(3)
    if ap == "PM" and h != 12: h += 12
    if ap == "AM" and h == 12: h = 0
    return max(0, (h * 60 + mi) - (8 * 60))

def status_at(time_str: str, hash_table, result: dict | None = None) -> None:
    t = _clock_to_min_since_8(time_str)
    pkgs = list(hash_table.get_all_packages())
    pkgs.sort(key=lambda p: getattr(p, "package_id", 0))

    print("\n============================================================")
    print(f"Status Snapshot @ {time_str}")
    print("============================================================")

    def _deliv_min(p) -> int | None:
        dt = getattr(p, "delivery_time", None)
        if not dt: return None
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", dt)
        if not m: return None
        h = int(m.group(1)); mi = int(m.group(2))
        return (h * 60 + mi) - (8 * 60)

    trips = result.get("trips", []) if isinstance(result, dict) else []
    trips_by_truck = {}
    for tr in trips:
        trips_by_truck.setdefault(tr["truck"], []).append(tr)
    for arr in trips_by_truck.values():
        arr.sort(key=lambda x: x["depart"])

    for p in pkgs:
        dmin = _deliv_min(p)
        board = getattr(p, "board_time_min", None)
        if board is None and dmin is not None and getattr(p, "truck_id", None) in trips_by_truck:
            for tr in trips_by_truck[p.truck_id]:
                if tr["depart"] <= dmin <= tr["return"]:
                    board = tr["depart"]; break

        if dmin is not None and t >= dmin:
            print(f"Pkg {p.package_id:2d}: DELIVERED at {p.delivery_time:>5}  | {p.address}")
        elif board is not None and board <= t < (dmin if dmin is not None else 10**9):
            from_dep = minutes_to_str(board)
            print(f"Pkg {p.package_id:2d}: EN ROUTE  since {from_dep}  on Truck {getattr(p, 'truck_id', '?')} | {p.address}")
        else:
            print(f"Pkg {p.package_id:2d}: AT HUB                        | {p.address}")
