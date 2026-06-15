"""Structured data access over SQLite (built from the committed CSVs).

A thin repository layer on stdlib sqlite3 (no ORM). Most tables are read-only;
the logbook and feedback tables are appendable.
"""
