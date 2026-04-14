"""Admin API routes — dashboard, appointments, customers, stylists, services."""

import logging
from datetime import datetime, timedelta, timezone, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, case, extract, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.appointment import Appointment
from models.customer import Customer
from models.service import Service
from models.stylist import Stylist
from models.admin_device import AdminDevice
from config import settings
from middleware.admin_auth import create_admin_token, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

IST = timezone(timedelta(hours=5, minutes=30))


# ─── AUTH ────────────────────────────────────────────────

@router.post("/login")
async def admin_login(body: dict):
    """Login with admin PIN → returns JWT token."""
    pin = str(body.get("pin", ""))
    if pin == settings.ADMIN_PIN:
        token = create_admin_token()
        return {"success": True, "token": token}
    raise HTTPException(status_code=401, detail="Invalid PIN")


@router.post("/register-device", dependencies=[Depends(require_admin)])
async def register_device(body: dict, db: AsyncSession = Depends(get_db)):
    """Register an Expo push token for admin notifications."""
    token = body.get("expo_push_token")
    device_name = body.get("device_name", "Admin Device")
    if not token:
        raise HTTPException(status_code=400, detail="expo_push_token is required")

    # Check if already registered
    existing = await db.execute(
        select(AdminDevice).where(AdminDevice.expo_push_token == token)
    )
    if existing.scalar_one_or_none():
        return {"success": True, "message": "Device already registered"}

    device = AdminDevice(expo_push_token=token, device_name=device_name)
    db.add(device)
    await db.flush()
    return {"success": True, "message": "Device registered for notifications"}


# ─── DASHBOARD ───────────────────────────────────────────

@router.get("/dashboard", dependencies=[Depends(require_admin)])
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Dashboard stats — today's bookings, revenue, weekly trends."""
    now = datetime.now(IST)
    today = now.date()
    week_ago = today - timedelta(days=6)

    # Today's stats
    today_result = await db.execute(
        select(
            func.count(Appointment.id).label("total"),
            func.count(case((Appointment.status == "booked", 1))).label("booked"),
            func.count(case((Appointment.status == "completed", 1))).label("completed"),
            func.count(case((Appointment.status == "cancelled", 1))).label("cancelled"),
        ).where(func.date(Appointment.start_time) == today)
    )
    today_stats = today_result.one()

    # Today's revenue (from booked + completed)
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Service.price), 0)).select_from(
            Appointment.__table__.join(Service.__table__, Appointment.service_id == Service.id)
        ).where(
            and_(
                func.date(Appointment.start_time) == today,
                Appointment.status.in_(["booked", "completed"]),
            )
        )
    )
    today_revenue = float(revenue_result.scalar())

    # Total customers
    customer_count = await db.execute(select(func.count(Customer.id)))
    total_customers = customer_count.scalar()

    # Weekly bookings (last 7 days) — for the bar chart
    weekly_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    func.date(Appointment.start_time) == d,
                    Appointment.status.in_(["booked", "completed"]),
                )
            )
        )
        weekly_data.append({
            "date": d.isoformat(),
            "day": d.strftime("%a"),
            "count": day_result.scalar(),
        })

    # Weekly revenue (last 7 days) — for the line chart
    weekly_revenue = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev_result = await db.execute(
            select(func.coalesce(func.sum(Service.price), 0)).select_from(
                Appointment.__table__.join(Service.__table__, Appointment.service_id == Service.id)
            ).where(
                and_(
                    func.date(Appointment.start_time) == d,
                    Appointment.status.in_(["booked", "completed"]),
                )
            )
        )
        weekly_revenue.append({
            "date": d.isoformat(),
            "day": d.strftime("%a"),
            "revenue": float(rev_result.scalar()),
        })

    # Service popularity — for the pie chart
    popularity_result = await db.execute(
        select(Service.name, func.count(Appointment.id).label("count")).select_from(
            Appointment.__table__.join(Service.__table__, Appointment.service_id == Service.id)
        ).where(
            Appointment.status.in_(["booked", "completed"])
        ).group_by(Service.name).order_by(func.count(Appointment.id).desc())
    )
    service_popularity = [{"service": row.name, "count": row.count} for row in popularity_result.all()]

    # Upcoming appointments (next 5)
    upcoming_result = await db.execute(
        select(Appointment, Service.name.label("service_name"), Stylist.name.label("stylist_name")).join(
            Service, Appointment.service_id == Service.id
        ).join(
            Stylist, Appointment.stylist_id == Stylist.id
        ).where(
            and_(
                Appointment.status == "booked",
                Appointment.start_time > now,
            )
        ).order_by(Appointment.start_time.asc()).limit(5)
    )
    upcoming = []
    for row in upcoming_result.all():
        appt = row[0]
        upcoming.append({
            "id": appt.id,
            "customer_name": appt.customer_name,
            "customer_phone": appt.customer_phone,
            "service": row.service_name,
            "stylist": row.stylist_name,
            "start_time": appt.start_time.isoformat(),
            "status": appt.status,
        })

    return {
        "today": {
            "total_bookings": today_stats.total,
            "booked": today_stats.booked,
            "completed": today_stats.completed,
            "cancelled": today_stats.cancelled,
            "revenue": today_revenue,
        },
        "total_customers": total_customers,
        "weekly_bookings": weekly_data,
        "weekly_revenue": weekly_revenue,
        "service_popularity": service_popularity,
        "upcoming_appointments": upcoming,
    }


# ─── APPOINTMENTS ────────────────────────────────────────

@router.get("/appointments", dependencies=[Depends(require_admin)])
async def get_appointments(
    date: str = Query(None, description="Filter by date (YYYY-MM-DD)"),
    status: str = Query(None, description="Filter by status"),
    stylist_id: int = Query(None, description="Filter by stylist"),
    db: AsyncSession = Depends(get_db),
):
    """Get all appointments with optional filters."""
    query = (
        select(Appointment, Service.name.label("service_name"), Service.price.label("service_price"),
               Stylist.name.label("stylist_name"))
        .join(Service, Appointment.service_id == Service.id)
        .join(Stylist, Appointment.stylist_id == Stylist.id)
    )

    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(func.date(Appointment.start_time) == filter_date)
        except ValueError:
            pass

    if status:
        query = query.where(Appointment.status == status)

    if stylist_id:
        query = query.where(Appointment.stylist_id == stylist_id)

    query = query.order_by(Appointment.start_time.desc())
    result = await db.execute(query)

    appointments = []
    for row in result.all():
        appt = row[0]
        appointments.append({
            "id": appt.id,
            "customer_name": appt.customer_name,
            "customer_phone": appt.customer_phone,
            "service": row.service_name,
            "service_price": row.service_price,
            "stylist": row.stylist_name,
            "stylist_id": appt.stylist_id,
            "start_time": appt.start_time.isoformat(),
            "end_time": appt.end_time.isoformat(),
            "status": appt.status,
            "created_at": appt.created_at.isoformat() if appt.created_at else None,
        })

    return {"appointments": appointments, "total": len(appointments)}


@router.get("/appointments/{appointment_id}", dependencies=[Depends(require_admin)])
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single appointment by ID."""
    result = await db.execute(
        select(Appointment, Service.name.label("service_name"), Service.price.label("service_price"),
               Stylist.name.label("stylist_name"))
        .join(Service, Appointment.service_id == Service.id)
        .join(Stylist, Appointment.stylist_id == Stylist.id)
        .where(Appointment.id == appointment_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt = row[0]
    return {
        "id": appt.id,
        "customer_name": appt.customer_name,
        "customer_phone": appt.customer_phone,
        "service": row.service_name,
        "service_price": row.service_price,
        "stylist": row.stylist_name,
        "stylist_id": appt.stylist_id,
        "start_time": appt.start_time.isoformat(),
        "end_time": appt.end_time.isoformat(),
        "status": appt.status,
        "created_at": appt.created_at.isoformat() if appt.created_at else None,
    }


@router.patch("/appointments/{appointment_id}", dependencies=[Depends(require_admin)])
async def update_appointment(appointment_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """Update appointment status (complete, cancel)."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    new_status = body.get("status")
    if new_status and new_status in ("booked", "completed", "cancelled", "rescheduled"):
        appt.status = new_status

    await db.flush()
    return {"success": True, "id": appt.id, "status": appt.status}


# ─── CUSTOMERS ───────────────────────────────────────────

@router.get("/customers", dependencies=[Depends(require_admin)])
async def get_customers(
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all customers, optionally search by name or phone."""
    query = select(Customer).order_by(Customer.total_visits.desc())

    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%") | Customer.phone.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    customers = result.scalars().all()

    return {
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "preferred_language": c.preferred_language,
                "total_visits": c.total_visits,
            }
            for c in customers
        ],
        "total": len(customers),
    }


@router.get("/customers/{customer_id}", dependencies=[Depends(require_admin)])
async def get_customer_detail(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get customer detail with appointment history."""
    cust_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get their appointments
    appts_result = await db.execute(
        select(Appointment, Service.name.label("service_name"), Stylist.name.label("stylist_name"))
        .join(Service, Appointment.service_id == Service.id)
        .join(Stylist, Appointment.stylist_id == Stylist.id)
        .where(Appointment.customer_phone == customer.phone)
        .order_by(Appointment.start_time.desc())
    )

    appointments = []
    for row in appts_result.all():
        appt = row[0]
        appointments.append({
            "id": appt.id,
            "service": row.service_name,
            "stylist": row.stylist_name,
            "start_time": appt.start_time.isoformat(),
            "status": appt.status,
        })

    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "preferred_language": customer.preferred_language,
        "total_visits": customer.total_visits,
        "appointments": appointments,
    }


# ─── STYLISTS ────────────────────────────────────────────

@router.get("/stylists", dependencies=[Depends(require_admin)])
async def get_stylists(db: AsyncSession = Depends(get_db)):
    """Get all stylists with today's booking count."""
    today = datetime.now(IST).date()

    result = await db.execute(select(Stylist).order_by(Stylist.id))
    stylists = result.scalars().all()

    stylist_data = []
    for s in stylists:
        # Count today's bookings
        count_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.stylist_id == s.id,
                    Appointment.status.in_(["booked", "completed"]),
                    func.date(Appointment.start_time) == today,
                )
            )
        )
        today_count = count_result.scalar()

        stylist_data.append({
            "id": s.id,
            "name": s.name,
            "phone": s.phone,
            "specializations": s.specializations,
            "work_start": s.work_start,
            "work_end": s.work_end,
            "days_off": s.days_off,
            "is_active": s.is_active,
            "today_bookings": today_count,
        })

    return {"stylists": stylist_data}


@router.patch("/stylists/{stylist_id}", dependencies=[Depends(require_admin)])
async def update_stylist(stylist_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """Toggle stylist active/inactive."""
    result = await db.execute(select(Stylist).where(Stylist.id == stylist_id))
    stylist = result.scalar_one_or_none()
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist not found")

    if "is_active" in body:
        stylist.is_active = body["is_active"]
    if "name" in body:
        stylist.name = body["name"]
    if "phone" in body:
        stylist.phone = body["phone"]
    if "specializations" in body:
        stylist.specializations = body["specializations"]

    await db.flush()
    return {"success": True, "id": stylist.id, "is_active": stylist.is_active}


# ─── SERVICES ────────────────────────────────────────────

@router.get("/services", dependencies=[Depends(require_admin)])
async def get_services(db: AsyncSession = Depends(get_db)):
    """Get all salon services."""
    result = await db.execute(select(Service).order_by(Service.id))
    services = result.scalars().all()

    return {
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "duration": s.duration,
                "price": s.price,
                "category": s.category,
                "is_active": s.is_active,
            }
            for s in services
        ]
    }


@router.patch("/services/{service_id}", dependencies=[Depends(require_admin)])
async def update_service(service_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """Update service price, duration, or active status."""
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if "price" in body:
        service.price = body["price"]
    if "duration" in body:
        service.duration = body["duration"]
    if "is_active" in body:
        service.is_active = body["is_active"]
    if "name" in body:
        service.name = body["name"]
    if "category" in body:
        service.category = body["category"]

    await db.flush()
    return {"success": True, "id": service.id, "name": service.name}


@router.delete("/wipe-database", dependencies=[Depends(require_admin)])
async def wipe_database(db: AsyncSession = Depends(get_db)):
    """Wipe all customer and appointment data."""
    await db.execute(delete(Appointment))
    await db.execute(delete(Customer))
    await db.flush()
    return {"success": True, "message": "Database wiped successfully"}
