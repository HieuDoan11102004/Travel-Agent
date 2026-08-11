"""Seed script to load Tokyo places data into DuckDB and Qdrant."""

import json
import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.place import Place
from app.data.duckdb_client import DuckDBClient


def load_places_from_json(json_path: Path) -> list[Place]:
    with open(json_path) as f:
        data = json.load(f)
    return [Place(**item) for item in data]


def seed_duckdb(places: list[Place], db_path: str = "data/places.duckdb") -> None:
    client = DuckDBClient(db_path)
    client.insert_places(places)
    print(f"Seeded {len(places)} places into DuckDB at {db_path}")
    client.close()


def main() -> None:
    seed_file = Path(__file__).parent.parent / "seed_data" / "tokyo_places.json"
    places = load_places_from_json(seed_file)
    seed_duckdb(places)
    print("Seeding complete!")


if __name__ == "__main__":
    main()
