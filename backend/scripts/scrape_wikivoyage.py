#!/usr/bin/env python3
"""Scrape Wikivoyage data for travel destinations."""

import argparse
import asyncio
import json
import re
from pathlib import Path
import httpx

JAPAN_DESTINATIONS = {
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "kyoto": "Kyoto",
    "nara": "Nara",
    "yokohama": "Yokohama",
    "hiroshima": "Hiroshima",
    "sapporo": "Sapporo",
    "nagoya": "Nagoya",
    "kobe": "Kobe",
    "fukuoka": "Fukuoka",
}

COST_ESTIMATES = {"attraction": 1500, "restaurant": 2000, "shopping": 5000, "entertainment": 3000, "nature": 0, "cultural": 500}
DURATION_ESTIMATES = {"attraction": 1.5, "restaurant": 1.5, "shopping": 2.0, "entertainment": 2.5, "nature": 3.0, "cultural": 2.0}

# Words that indicate non-place entries
SKIP_WORDS = {"get around", "get in", "get out", "stay safe", "stay healthy", "stay connect", "cope", 
              "static map", "image:", "file:", "category:", "talk", "edit", "pagebanner"}


def classify(name, section=""):
    text = f"{name} {section}".lower()
    if any(k in text for k in ["temple", "shrine", "castle", "palace", "museum", "gallery"]):
        return "cultural"
    if any(k in text for k in ["park", "garden", "tower", "landmark", "observation"]):
        return "attraction"
    if any(k in text for k in ["market", "mall", "district", "shopping", "street"]):
        return "shopping"
    if any(k in text for k in ["restaurant", "cafe", "coffee", "ramen", "sushi", "izakaya", "food"]):
        return "restaurant"
    if any(k in text for k in ["mountain", "beach", "lake", "forest", "trail", "hiking"]):
        return "nature"
    return "attraction"


def extract_places(title, wikitext):
    places = []
    seen = set()
    sections = re.split(r"\n==+([^=]+)==+\n", wikitext)
    
    for i, part in enumerate(sections):
        if i % 2 == 1:
            current_section = part.strip()
        else:
            current_section = "See"
        
        for match in re.finditer(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", part):
            name = (match.group(2) or match.group(1)).strip()
            name_lower = name.lower()
            
            # Skip duplicates and invalid names
            if name_lower in seen:
                continue
            if len(name) < 3 or len(name) > 50:
                continue
            if name_lower in [title.lower(), "japan"]:
                continue
            if any(skip in name_lower for skip in SKIP_WORDS):
                continue
            if name.lower() in ["see", "do", "buy", "eat", "drink", "sleep", "connect"]:
                continue
            
            seen.add(name_lower)
            
            # Extract description
            start = max(0, match.start() - 30)
            end = min(len(part), match.end() + 80)
            context = re.sub(r'\[\[[^\]]*\|', '', part[start:end])
            context = re.sub(r'\[\[|\]\]', '', context)
            context = re.sub(r"'''?|'", '', context)
            context = re.sub(r'\s+', ' ', context).strip()[:150]
            
            category = classify(name, current_section)
            
            places.append({
                "id": f"wiki-{title.lower()}-{re.sub(r'[^a-z0-9]+', '-', name_lower)[:25]}",
                "name": name,
                "category": category,
                "subcategory": "other",
                "location": {"lat": 0, "lng": 0},
                "cost_estimate": COST_ESTIMATES.get(category, 1000),
                "duration_hours": DURATION_ESTIMATES.get(category, 1.5),
                "opening_hours": {"monday": "10:00-20:00", "tuesday": "10:00-20:00", "wednesday": "10:00-20:00",
                                 "thursday": "10:00-20:00", "friday": "10:00-20:00", "saturday": "10:00-21:00", "sunday": "10:00-20:00"},
                "popularity": "medium",
                "rating": round(3.5 + (hash(name) % 15) / 10, 1),
                "description": context or f"Popular destination in {title}",
                "address": f"{name}, {title}",
                "wikivoyage_source": f"https://en.wikivoyage.org/wiki/{title.replace(' ', '_')}",
            })
    return places


async def fetch_wikivoyage(destinations):
    all_places = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for dest in destinations:
            article = JAPAN_DESTINATIONS.get(dest.lower(), dest.title())
            print(f"Fetching: {article}...")
            try:
                r = await client.get(
                    "https://en.wikivoyage.org/w/api.php",
                    params={"action": "query", "titles": article, "prop": "revisions",
                            "rvprop": "content", "rvslots": "main", "format": "json"},
                    headers={"User-Agent": "TravelPlannerBot/1.0 (Educational Project)"}
                )
                data = r.json()
                pages = data.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    wikitext = pdata.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", "")
                    if wikitext:
                        places = extract_places(article, wikitext)
                        print(f"  Found {len(places)} places")
                        all_places.extend(places)
            except Exception as e:
                print(f"  Error: {e}")
    return all_places


async def main():
    parser = argparse.ArgumentParser(description="Scrape Wikivoyage for travel places")
    parser.add_argument("--dest", nargs="+", default=["tokyo"], help="Destinations to scrape")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--merge", action="store_true", help="Merge with existing seed data")
    args = parser.parse_args()

    places = await fetch_wikivoyage(args.dest)
    print(f"\nTotal: {len(places)} places scraped")

    if not places:
        print("No places found.")
        return

    # Merge if requested
    if args.merge:
        existing_path = Path(__file__).parent.parent / "seed_data" / "tokyo_places.json"
        if existing_path.exists():
            with open(existing_path) as f:
                existing = json.load(f)
            existing_ids = {p["id"] for p in existing if isinstance(p, dict)}
            merged = existing.copy()
            for place in places:
                if place["id"] not in existing_ids:
                    merged.append(place)
            places = merged
            print(f"After merge: {len(places)} places")

    output = Path(args.output) if args.output else Path(__file__).parent.parent / "seed_data" / "wikivoyage_places.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output}")
    print("\n" + "="*60)
    print("ATTRIBUTION REQUIRED:")
    print("Content sourced from Wikivoyage (https://www.wikivoyage.org/)")
    print("Licensed under Creative Commons Attribution-ShareAlike 3.0")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
