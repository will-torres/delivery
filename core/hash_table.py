from core.models import Package


class HashTable:
    """
    Simple separate-chaining hash table keyed by package_id (int).
    - insert(id, address, deadline, city, zip_code, weight, status) -> stores/updates a Package
    - lookup(id) -> returns the Package (or None)
    - get_all_packages() -> iterable of all Package objects
    """
    def __init__(self, capacity: int = 64):
        # capacity should be >= number of packages; power-of-two is fine
        if capacity < 8:
            capacity = 8
        self._buckets = [[] for _ in range(capacity)]
        self._count = 0

    # ---------------- internals ----------------
    def _hash(self, key: int) -> int:
        # key is package_id (int). Simple modulo hashing.
        return int(key) % len(self._buckets)

    def _find_slot(self, bucket: list, package_id: int):
        # return (index, Package or None) within a bucket
        for i, pkg in enumerate(bucket):
            if pkg.package_id == package_id:
                return i, pkg
        return -1, None

    def insert(self, package_id: int, address: str, deadline: str, city: str,
               zip_code: str, weight: str, status: str = "at_hub",
               state: str = "UT", special_notes: str = "") -> None:
        """
        Insert or update a package by ID. Stores all required fields:
        - address, deadline, city, zip_code, weight, and delivery status (+delivery time kept if set).
        """
        idx = self._hash(package_id)
        bucket = self._buckets[idx]
        pos, existing = self._find_slot(bucket, package_id)

        if existing is None:
            pkg = Package(package_id, address, deadline, city, zip_code, weight, status, state, special_notes)
            bucket.append(pkg)
            self._count += 1
        else:
            # Update fields in-place (keep delivery_time/truck_id if already set)
            existing.address = address
            existing.deadline = deadline
            existing.city = city
            existing.state = state
            existing.zip_code = zip_code
            existing.weight = weight
            existing.status = status
            existing.special_notes = special_notes

    def lookup(self, package_id: int):
        """
        Return the Package for this ID, or None if not present.
        """
        idx = self._hash(package_id)
        bucket = self._buckets[idx]
        _, pkg = self._find_slot(bucket, package_id)
        return pkg

    def update_status(self, package_id: int, status: str, delivery_time: str | None = None, truck_id: int | None = None):
        """
        Convenience: set status and optional delivery_time/truck_id.
        """
        pkg = self.lookup(package_id)
        if not pkg:
            return False
        pkg.status = status
        if delivery_time is not None:
            pkg.delivery_time = delivery_time
        if truck_id is not None:
            pkg.truck_id = truck_id
        return True

    def get_all_packages(self):
        """
        Return a generator over all Package objects (use list(...) if you need indexing).
        """
        for bucket in self._buckets:
            for pkg in bucket:
                yield pkg

    # ---------------- optional helpers ----------------
    def __len__(self):
        return self._count

    def __iter__(self):
        return self.get_all_packages()
