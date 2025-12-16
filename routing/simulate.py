from config import SPEED_MPH, HUB_ADDRESS
from reporting.status import minutes_to_str

def simulate_route(ds, ordered_pkgs: list, depart_time_min: int, truck_id: int):
    miles = 0.0
    time_min = int(depart_time_min)
    curr = HUB_ADDRESS
    legs = []

    # record board time once per trip (optional, useful for snapshots)
    for p in ordered_pkgs:
        if getattr(p, "board_time_min", None) is None:
            p.board_time_min = depart_time_min

    for p in ordered_pkgs:
        fix = getattr(p, "address_fix_time_min", None)
        if fix is not None and time_min < fix:
            time_min = fix
        d = ds.get_distance(curr, p.address)
        travel_min = int(round(60.0 * d / SPEED_MPH))
        time_min += travel_min
        miles += d
        curr = p.address

        p.status = "delivered"
        p.delivery_time = minutes_to_str(time_min)
        p.truck_id = truck_id

        legs.append((curr, d, time_min))

    return miles, time_min, legs
