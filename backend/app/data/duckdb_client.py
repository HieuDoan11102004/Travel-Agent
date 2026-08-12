from pathlib import Path

import duckdb

from app.models.place import Place


class DuckDBClient:
    """Client for local DuckDB storage of places data."""

    def __init__(self, db_path: str = "data/places.duckdb"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id VARCHAR PRIMARY KEY,
                name VARCHAR,
                category VARCHAR,
                subcategory VARCHAR,
                lat DOUBLE,
                lng DOUBLE,
                cost_estimate INTEGER,
                duration_hours DOUBLE,
                opening_hours JSON,
                popularity VARCHAR,
                rating DOUBLE,
                description VARCHAR,
                address VARCHAR
            )
        """)

    def insert_place(self, place: Place) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO places
            (id, name, category, subcategory, lat, lng, cost_estimate,
             duration_hours, opening_hours, popularity, rating, description, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                place.id,
                place.name,
                place.category,
                place.subcategory,
                place.location.lat,
                place.location.lng,
                place.cost_estimate,
                place.duration_hours,
                str(place.opening_hours) if place.opening_hours else None,
                place.popularity,
                place.rating,
                place.description,
                place.address,
            ],
        )

    def insert_places(self, places: list[Place]) -> None:
        for place in places:
            self.insert_place(place)

    def get_place(self, place_id: str) -> Place | None:
        row = self.conn.execute(
            "SELECT * FROM places WHERE id = ?", [place_id]
        ).fetchone()
        if not row:
            return None
        return self._row_to_place(row)

    def search_by_category(self, category: str, limit: int = 50) -> list[Place]:
        rows = self.conn.execute(
            "SELECT * FROM places WHERE category = ? LIMIT ?",
            [category, limit],
        ).fetchall()
        return [self._row_to_place(row) for row in rows]

    def search_by_subcategory(self, subcategory: str, limit: int = 50) -> list[Place]:
        rows = self.conn.execute(
            "SELECT * FROM places WHERE subcategory LIKE ? LIMIT ?",
            [f"%{subcategory}%", limit],
        ).fetchall()
        return [self._row_to_place(row) for row in rows]

    def get_all_places(self, limit: int = 1000) -> list[Place]:
        rows = self.conn.execute(
            "SELECT * FROM places LIMIT ?", [limit]
        ).fetchall()
        return [self._row_to_place(row) for row in rows]

    def _row_to_place(self, row: tuple) -> Place:
        return Place(
            id=row[0],
            name=row[1],
            category=row[2],
            subcategory=row[3],
            location={"lat": row[4], "lng": row[5]},
            cost_estimate=row[6],
            duration_hours=row[7],
            opening_hours=row[8],
            popularity=row[9],
            rating=row[10],
            description=row[11],
            address=row[12],
        )

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
