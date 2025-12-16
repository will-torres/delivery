# ui/cli.py
from reporting.status import status_at

class UserInterface:
    def __init__(self, hash_table, optimizer_or_result):
        self.ht = hash_table
        # accept either optimizer with .result or a plain dict
        self.result = getattr(optimizer_or_result, "result", optimizer_or_result)

    def display_main_menu(self):
        while True:
            print("\n============================================================")
            print("WGUPS PACKAGE DELIVERY TRACKING SYSTEM")
            print("============================================================")
            print("1. View all packages")
            print("2. View package by ID")
            print("3. View packages by truck")
            print("4. View total mileage")
            print("5. View status at specific time")
            print("6. Exit")
            print("============================================================")
            choice = input("Enter your choice (1-6): ").strip()

            if choice == "5":
                when = input("Enter time (e.g., 08:55, 10:05, 12:45): ").strip()
                status_at(when, self.ht, self.result)
            elif choice == "6":
                break
            else:

                print("Feature not shown in this refactor snippet. (Use 5 or 6.)")
