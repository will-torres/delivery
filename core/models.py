
from typing import List, Optional
from config import SPEED_MPH, TRUCK_CAPACITY, HUB_ADDRESS


class Package:
    """
    Minimal package record shared by the hash table, planner, simulator, and UI.

    """
    def __init__(
        self,
        package_id: int,
        address: str,
        deadline: str,
        city: str,
        zip_code: str,
        weight: str,
        status: str = "at_hub",
        state: str = "UT",
        special_notes: str = "",
    ):
        # Identity
        self.package_id: int = int(package_id)

        # Delivery metadata
        self.address: str = address
        self.city: str = city
        self.state: str = state
        self.zip_code: str = zip_code
        self.deadline: str = deadline
        self.weight: str = weight
        self.status: str = status              # "at_hub" | "en_route" | "delivered"
        self.delivery_time: Optional[str] = None  # "HH:MM" when delivered

        # Scenario helpers
        self.special_notes: str = special_notes
        self.truck_id: Optional[int] = None
        self.board_time_min: Optional[int] = None
        self.available_time_min: Optional[int] = None
        self.address_fix_time_min: Optional[int] = None
        self.truck_restriction: Optional[int] = None
        self.group_id: Optional[str] = None

    def __repr__(self) -> str:
        dt = self.delivery_time if self.delivery_time else "--:--"
        return (f"<Pkg {self.package_id} {self.address} {self.city} {self.zip_code} "
                f"ddl={self.deadline} wt={self.weight} status={self.status} t={dt}>")


class Truck:
    """
    Simple truck model.

    """
    def __init__(self, truck_id: int):
        self.truck_id: int = int(truck_id)
        self.speed: float = SPEED_MPH
        self.capacity: int = TRUCK_CAPACITY

        # State
        self.current_location: str = HUB_ADDRESS  # start at HUB (WGU)
        self.current_time: float = 8.0            # 08:00 start, in decimal hours
        self.total_miles: float = 0.0

        # Cargo tracking
        self.packages: List[int] = []            # package IDs currently on truck (if used)
        self.delivered_packages: List[int] = []  # package IDs delivered by this truck

    # ---- Optional helpers ----
    def can_load_package(self, _package: Package) -> bool:
        """Return True if there is capacity to load another package."""
        return len(self.packages) < self.capacity

    def load_package(self, package: Package) -> None:
        """Record a package as loaded"""
        if self.can_load_package(package):
            self.packages.append(package.package_id)

    def deliver_package(self, package_id: int, hash_table=None, delivered_time_decimal: Optional[float] = None) -> None:
        """
        Mark a package as delivered.

        """
        if package_id not in self.delivered_packages:
            self.delivered_packages.append(package_id)

        if hash_table is not None:
            try:
                from reporting.status import minutes_to_str
                if delivered_time_decimal is not None:
                    hhmm = self._convert_time_to_string(delivered_time_decimal)
                else:
                    hhmm = None

                if hasattr(hash_table, "update_status"):
                    hash_table.update_status(package_id, "delivered", delivery_time=hhmm, truck_id=self.truck_id)
                else:
                    # Fallback: look up and mutate directly
                    pkg = hash_table.lookup(package_id)
                    if pkg:
                        pkg.status = "delivered"
                        pkg.truck_id = self.truck_id
                        if hhmm:
                            pkg.delivery_time = hhmm
            except Exception:
                pass

    @staticmethod
    def _convert_time_to_string(time_decimal: float) -> str:
        """
        Convert decimal hours (e.g., 8.2667) to 'HH:MM' (08:16).

        """
        total_minutes = int(round(time_decimal * 60))
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"
