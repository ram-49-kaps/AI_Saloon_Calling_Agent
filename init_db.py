"""Startup script — creates tables and seeds data on first deploy."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, async_session
from sqlalchemy import select, text
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
        "days_off": [0],
    },
    {
        "name": "Priya",
        "phone": "9876543002",
        "specializations": ["Facial", "Nails"],
        "work_start": "10:00",
        "work_end": "19:00",
        "days_off": [0],
    },
    {
        "name": "Amit",
        "phone": "9876543003",
        "specializations": ["Hair"],
        "work_start": "09:00",
        "work_end": "20:00",
        "days_off": [1],
    },
]


async def init_db():
    """Create tables and seed if empty."""
    print("📦 Creating database tables...")
    await create_tables()
    print("✅ Tables created")

    async with async_session() as session:
        result = await session.execute(select(Service).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Database already seeded. Skipping.")
            return

        for svc_data in SERVICES:
            session.add(Service(**svc_data))
        for sty_data in STYLISTS:
            session.add(Stylist(**sty_data))
        await session.commit()
        print(f"🌱 Seeded {len(SERVICES)} services + {len(STYLISTS)} stylists")


if __name__ == "__main__":
    asyncio.run(init_db())
