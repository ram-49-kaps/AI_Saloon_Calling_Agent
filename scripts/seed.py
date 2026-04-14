"""Seed script — populates the database with initial services and stylists."""

import asyncio
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database import async_session, create_tables
from models.service import Service
from models.stylist import Stylist


SERVICES = [
    {
        "name": "Haircut",
        "aliases": ["बाल कटवाना", "વાળ કાપવા", "baal katna", "baal katvana", "hair cut", "cutting"],
        "duration": 30,
        "price": 500,
        "category": "Hair",
    },
    {
        "name": "Hair Color",
        "aliases": ["बाल रंगना", "વાળ રંગવા", "baal rangna", "hair colour", "coloring", "colour"],
        "duration": 90,
        "price": 2000,
        "category": "Hair",
    },
    {
        "name": "Facial",
        "aliases": ["फेशियल", "ફેશિયલ", "face treatment", "facial treatment"],
        "duration": 45,
        "price": 800,
        "category": "Facial",
    },
    {
        "name": "Manicure",
        "aliases": ["मैनीक्योर", "મેનિક્યોર", "nail art", "hand treatment"],
        "duration": 30,
        "price": 400,
        "category": "Nails",
    },
    {
        "name": "Pedicure",
        "aliases": ["पेडीक्योर", "પેડિક્યોર", "foot treatment", "pedi"],
        "duration": 45,
        "price": 500,
        "category": "Nails",
    },
    {
        "name": "Hair Spa",
        "aliases": ["हेयर स्पा", "હેર સ્પા", "hair treatment", "spa", "hair spa treatment"],
        "duration": 60,
        "price": 1200,
        "category": "Hair",
    },
    {
        "name": "Beard Trim",
        "aliases": ["दाढ़ी ट्रिम", "દાઢી ટ્રિમ", "daadhi trim", "beard", "shaving", "trim"],
        "duration": 15,
        "price": 200,
        "category": "Hair",
    },
    {
        "name": "Threading",
        "aliases": ["थ्रेडिंग", "થ્રેડિંગ", "eyebrow", "eyebrow threading"],
        "duration": 15,
        "price": 100,
        "category": "Facial",
    },
]

STYLISTS = [
    {
        "name": "Rahul",
        "phone": "9876543001",
        "specializations": ["Hair", "Facial"],
        "work_start": "09:00",
        "work_end": "20:00",
        "days_off": [0],  # Sunday off
    },
    {
        "name": "Priya",
        "phone": "9876543002",
        "specializations": ["Facial", "Nails"],
        "work_start": "10:00",
        "work_end": "19:00",
        "days_off": [0],  # Sunday off
    },
    {
        "name": "Amit",
        "phone": "9876543003",
        "specializations": ["Hair"],
        "work_start": "09:00",
        "work_end": "20:00",
        "days_off": [1],  # Monday off
    },
]


async def seed():
    """Seed the database with services and stylists."""
    print("🌱 Seeding database...")

    await create_tables()

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(select(Service).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Database already has data. Skipping seed.")
            print("   To re-seed, clear the tables first.")
            return

        # Insert services
        for svc_data in SERVICES:
            service = Service(**svc_data)
            session.add(service)
        print(f"✅ Added {len(SERVICES)} services")

        # Insert stylists
        for sty_data in STYLISTS:
            stylist = Stylist(**sty_data)
            session.add(stylist)
        print(f"✅ Added {len(STYLISTS)} stylists")

        await session.commit()

    print("🎉 Seed complete!")
    print("\nServices:")
    for s in SERVICES:
        print(f"  • {s['name']} — {s['duration']}min — ₹{s['price']}")
    print("\nStylists:")
    for s in STYLISTS:
        print(f"  • {s['name']} — {', '.join(s['specializations'])}")


if __name__ == "__main__":
    asyncio.run(seed())
