import csv
import re

class DistanceService:
    """
    Service class to load and query the WGUPS distance matrix.

    """

    def __init__(self):
        # Matrix in display order (0..N-1). Index 0 is HUB (WGU).
        self.addresses: list[str] = []
        self.distance_matrix: list[list[float]] = []

        # Lookup maps
        self._raw_to_idx: dict[str, int] = {}   # exact raw string -> index
        self._norm_to_idx: dict[str, int] = {}  # normalized string -> index

        self.address_indices: dict[str, int] = {}

        # flip to True when you actually want verbose logs
        self.debug = False

    def _dbg(self, *a):
            if self.debug:
                print(*a)

    #  Normalization
    def _normalize(self, s: str) -> str:
        """Uppercase, strip punctuation/suites, standardize tokens, collapse spaces."""
        if not s:
            return ""
        s = s.upper().strip()
        s = re.sub(r"[.,#]", " ", s)  # drop punctuation/suite markers
        out = []
        for t in s.split():
            if t in {"STREET", "ST."}:
                t = "ST"
            elif t in {"AVENUE", "AV"}:
                t = "AVE"
            elif t == "BOULEVARD":
                t = "BLVD"
            elif t == "STATION":
                t = "STA"
            elif t == "SOUTH":
                t = "S"
            elif t == "NORTH":
                t = "N"
            elif t == "EAST":
                t = "E"
            elif t == "WEST":
                t = "W"
            out.append(t)
        return re.sub(r"\s+", " ", " ".join(out)).strip()

    def _add_mapping(self, text: str, idx: int) -> None:
        """Register raw and normalized forms for lookup."""
        if not text:
            return
        self._raw_to_idx[text] = idx
        self._norm_to_idx[self._normalize(text)] = idx

    #  Loading
    def load_distance_data(self, filename: str):
        with open(filename, "r", encoding="utf-8", errors="ignore") as file:
            rows = list(csv.reader(file))

        # Find header row (the one that has "Western Governors" among its cells)
        header_row = -1
        for i, row in enumerate(rows):
            if len(row) > 5 and any("Western Governors" in str(cell) for cell in row):
                header_row = i
                break
        if header_row == -1:
            raise RuntimeError("Distance table header row not found.")

        header = rows[header_row]

        # Reset structures
        self.addresses = []
        self.distance_matrix = []
        self._raw_to_idx.clear()
        self._norm_to_idx.clear()
        self.address_indices.clear()

        # Build addresses list (0..N-1) and map BOTH the name and street to SAME index
        for col in range(2, len(header)):  # columns >= 2 hold locations
            cell = (header[col] or "").strip()
            if not cell:
                continue
            lines = [l.strip() for l in cell.splitlines() if l.strip()]
            if not lines:
                continue

            name = lines[0]  # location name for display
            # street is first line containing a number; fallback to name
            street = next((l for l in lines[1:] if re.search(r"\d", l)), name)

            idx = len(self.addresses)
            self.addresses.append(name)

            # Map raw and normalized forms for BOTH name and street
            self._add_mapping(name, idx)
            self._add_mapping(street, idx)

        # Helpful aliases
        if self.addresses:
            # HUB aliases (index 0 is Western Governors University)
            self._add_mapping("HUB", 0)
            self._add_mapping("Western Governors University", 0)

        # Known tricky alias from the dataset/logs
        alias_from = "3575 W Valley Central Station bus Loop"
        alias_to   = "3575 W Valley Central Sta bus Loop"
        to_key = self._normalize(alias_to)
        if to_key in self._norm_to_idx:
            self._add_mapping(alias_from, self._norm_to_idx[to_key])

        for raw, idx in self._raw_to_idx.items():
            self.address_indices[raw] = idx

        # Build symmetric matrix (read lower triangle under the header)
        size = len(self.addresses)
        if size == 0:
            raise RuntimeError("No addresses parsed from the distance table header.")

        self.distance_matrix = [[0.0 for _ in range(size)] for _ in range(size)]

        # Rows immediately after header correspond to matrix rows
        for r in range(1, size + 1):                 # r = 1..size
            if header_row + r >= len(rows):
                break
            row = rows[header_row + r]
            i = r - 1                                 # matrix row index
            # lower triangle including diagonal for this row
            for c in range(2, 2 + r):
                if c >= len(row):
                    continue
                val = str(row[c]).strip()
                if not val:
                    continue
                try:
                    d = float(val)
                except ValueError:
                    continue
                j = c - 2
                self.distance_matrix[i][j] = d
                self.distance_matrix[j][i] = d       # mirror

        # Final symmetry/diagonal pass (no made-up defaults)
        for i in range(size):
            self.distance_matrix[i][i] = 0.0
            for j in range(size):
                a = self.distance_matrix[i][j]
                b = self.distance_matrix[j][i]
                if a == 0.0 and b != 0.0:
                    self.distance_matrix[i][j] = b
                elif b == 0.0 and a != 0.0:
                    self.distance_matrix[j][i] = a

        self._dbg(f"DEBUG: Created {size}x{size} matrix with addresses: {self.addresses[:5]}")

    #  Lookup & distance
    def _find_address_index(self, address: str) -> int:
        """Resolve an arbitrary address string to its matrix index."""
        if not address:
            return -1
        n = self._normalize(address)

        # 1) normalized direct hit
        idx = self._norm_to_idx.get(n)
        if idx is not None:
            return idx

        # 2) raw exact fallback
        addr_lc = address.strip().lower()
        for raw, i in self._raw_to_idx.items():
            if addr_lc == raw.strip().lower():
                return i

        # 3) tiny fuzzy: match by house number + first token (kept minimal to avoid false hits)
        parts = re.findall(r"\d+|[A-Z]+", n)
        for raw, i in self._raw_to_idx.items():
            rparts = re.findall(r"\d+|[A-Z]+", self._normalize(raw))
            if len(parts) >= 2 and len(rparts) >= 2 and parts[0] == rparts[0] and parts[1] == rparts[1]:
                self._dbg(f"DEBUG: Fuzzy match: {address} -> {raw}")
                return i

        return -1

    def get_distance(self, from_addr: str, to_addr: str) -> float:
        """
        Return miles between two addresses using the distance matrix.
        Fail-fast if either endpoint is unknown (no silent defaults).
        """
        i = self._find_address_index(from_addr)
        j = self._find_address_index(to_addr)

        if i == -1 or j == -1:
            examples = [a[:30] for a in self.addresses[:5]]
            raise ValueError(
                f"Address not in distance matrix: FROM='{from_addr}' TO='{to_addr}'. "
                f"Examples: {examples}"
            )

        d = self.distance_matrix[i][j]
        self._dbg(f"DEBUG: Distance from {from_addr[:20]}... to {to_addr[:20]}... = {d:.1f} miles")
        return d

