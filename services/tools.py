"""Tool handlers — core business logic for Vapi tool calls."""

from datetime import datetime, timedelta, date, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from thefuzz import fuzz

from models.service import Service
from models.stylist import Stylist
from models.appointment import Appointment
from models.customer import Customer
from utils.service_match import find_service, get_service_list_for_speech
from utils.slot_generator import generate_available_slots, format_slots_for_speech
from services.sms_service import send_booking_confirmation_sms
from services.push_service import send_admin_push_notification


def find_stylist_by_name(name: str, stylists: list) -> Stylist | None:
    """Fuzzy match a stylist name."""
    name = name.strip().lower()
    best, best_score = None, 0
    for s in stylists:
        score = fuzz.ratio(name, s.name.lower())
        if score > best_score:
            best_score = score
            best = s
    return best if best_score >= 60 else None


async def check_availability(args: dict, db: AsyncSession) -> str:
    """
    Check available time slots for a service on a given date, optionally for a specific stylist.

    Args expected: { service: str, date: "YYYY-MM-DD", stylist_name?: str }
    """
    service_name = args.get("service", "")
    date_str = args.get("date", "")
    preferred_stylist = args.get("stylist_name", "")

    # Validate date
    try:
        target_date = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return "I need a valid date. Could you tell me which date you'd like?"

    # Don't allow past dates
    today = date.today()
    if target_date < today:
        return "That date has already passed. Could you give me a future date?"

    # Find the service
    services_result = await db.execute(select(Service).where(Service.is_active == True))
    all_services = services_result.scalars().all()

    matched_service = find_service(service_name, all_services)
    if not matched_service:
        service_list = get_service_list_for_speech(all_services)
        return f"I couldn't find that service. We offer: {service_list}. Which one would you like?"

    # Get active stylists who can do this service
    stylists_result = await db.execute(
        select(Stylist).where(
            and_(
                Stylist.is_active == True,
                Stylist.specializations.contains([matched_service.category])
            )
        )
    )
    stylists = stylists_result.scalars().all()

    if not stylists:
        return f"Sorry, no stylist is available for {matched_service.name} on that date."

    # Filter by preferred stylist if specified
    if preferred_stylist:
        matched_stylist = find_stylist_by_name(preferred_stylist, stylists)
        if matched_stylist:
            stylists = [matched_stylist]
        else:
            stylist_names = ", ".join(s.name for s in stylists)
            return f"I couldn't find stylist '{preferred_stylist}'. Available stylists for {matched_service.name} are: {stylist_names}. Who would you prefer?"

    # Check day of week
    day_of_week = target_date.isoweekday() % 7  # 0=Sun

    # Collect slots per stylist
    stylist_slots = {}  # {stylist_name: [slots]}
    for stylist in stylists:
        if day_of_week in (stylist.days_off or []):
            continue

        appts_result = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status == "booked",
                    func.date(Appointment.start_time) == target_date,
                )
            )
        )
        existing = appts_result.scalars().all()

        slots = generate_available_slots(
            target_date, matched_service.duration, stylist, existing
        )
        if slots:
            stylist_slots[stylist.name] = slots

    if not stylist_slots:
        return f"Sorry, no slots available for {matched_service.name} on {target_date.strftime('%B %d')}. Would you like to try another date?"

    # If specific stylist was requested, show their slots
    if preferred_stylist and len(stylist_slots) == 1:
        name = list(stylist_slots.keys())[0]
        slots_text = format_slots_for_speech(stylist_slots[name])
        return f"For {matched_service.name} with {name} on {target_date.strftime('%B %d')}, available slots are: {slots_text}. Which time works for you?"

    # Show combined unique slots + mention available stylists
    all_slots = []
    for slots in stylist_slots.values():
        all_slots.extend(slots)

    seen = set()
    unique_slots = []
    for slot in sorted(all_slots, key=lambda x: x["start"]):
        if slot["display"] not in seen:
            seen.add(slot["display"])
            unique_slots.append(slot)

    slots_text = format_slots_for_speech(unique_slots)
    stylist_names = ", ".join(stylist_slots.keys())
    return f"For {matched_service.name} on {target_date.strftime('%B %d')}, available slots are: {slots_text}. Available stylists: {stylist_names}. Which time and stylist would you prefer?"


async def book_appointment(args: dict, db: AsyncSession) -> str:
    """
    Book an appointment with optional stylist preference and email confirmation.

    Args expected: { service: str, start_time: "ISO datetime", customer_name: str, phone: str, preferred_stylist?: str }
    """
    service_name = args.get("service", "")
    start_time_str = args.get("start_time", "")
    customer_name = args.get("customer_name", "")
    phone = args.get("phone", "")
    preferred_stylist = args.get("preferred_stylist", "")

    # Validate required fields
    if not all([service_name, start_time_str, customer_name, phone]):
        missing = []
        if not service_name:
            missing.append("service")
        if not start_time_str:
            missing.append("time")
        if not customer_name:
            missing.append("name")
        if not phone:
            missing.append("phone number")
        return f"I still need your {', '.join(missing)} to complete the booking."

    # Parse start time
    try:
        start_time = datetime.fromisoformat(start_time_str)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))  # IST
    except (ValueError, TypeError):
        return "I couldn't understand the time. Could you tell me the time again?"

    # Don't allow past bookings
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    if start_time < now:
        return "That time has already passed. Could you give me a future time?"

    # Find service
    services_result = await db.execute(select(Service).where(Service.is_active == True))
    all_services = services_result.scalars().all()
    matched_service = find_service(service_name, all_services)

    if not matched_service:
        return "I couldn't find that service. Could you tell me again which service you'd like?"

    # Calculate end time
    end_time = start_time + timedelta(minutes=matched_service.duration)
    target_date = start_time.date()

    # Get eligible stylists
    stylists_result = await db.execute(
        select(Stylist).where(
            and_(
                Stylist.is_active == True,
                Stylist.specializations.contains([matched_service.category])
            )
        )
    )
    stylists = stylists_result.scalars().all()

    if not stylists:
        return f"Sorry, no stylist is available for {matched_service.name}."

    # If customer requested a specific stylist, prioritize them
    if preferred_stylist:
        matched = find_stylist_by_name(preferred_stylist, stylists)
        if matched:
            stylists = [matched]  # Only try this stylist
        else:
            stylist_names = ", ".join(s.name for s in stylists)
            return f"I couldn't find stylist '{preferred_stylist}'. Available stylists: {stylist_names}."

    # Find the best available stylist (least busy, no conflict)
    best_stylist = None
    min_bookings = float("inf")

    for stylist in stylists:
        # Check day off
        day_of_week = target_date.isoweekday() % 7
        if day_of_week in (stylist.days_off or []):
            continue

        # Check working hours
        work_start_h, work_start_m = map(int, stylist.work_start.split(":"))
        work_end_h, work_end_m = map(int, stylist.work_end.split(":"))
        if start_time.hour < work_start_h or (start_time.hour == work_start_h and start_time.minute < work_start_m):
            continue
        if end_time.hour > work_end_h or (end_time.hour == work_end_h and end_time.minute > work_end_m):
            continue

        # Check for overlapping appointments
        overlap_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status == "booked",
                    Appointment.start_time < end_time,
                    Appointment.end_time > start_time,
                )
            )
        )
        overlap_count = overlap_result.scalar()
        if overlap_count > 0:
            continue

        # Count total bookings for load balancing
        count_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status == "booked",
                    func.date(Appointment.start_time) == target_date,
                )
            )
        )
        booking_count = count_result.scalar()

        if booking_count < min_bookings:
            min_bookings = booking_count
            best_stylist = stylist

    if not best_stylist:
        if preferred_stylist:
            return f"Sorry, {preferred_stylist} is not available at that time. Would you like to try another time or a different stylist?"
        return f"Sorry, that time slot is not available for {matched_service.name}. Would you like to check another time?"

    # Create the appointment
    appointment = Appointment(
        service_id=matched_service.id,
        stylist_id=best_stylist.id,
        customer_name=customer_name,
        customer_phone=phone,
        start_time=start_time,
        end_time=end_time,
        status="booked",
    )
    db.add(appointment)

    # Upsert customer
    stmt = pg_insert(Customer).values(
        name=customer_name,
        phone=phone,
        total_visits=1,
    ).on_conflict_do_update(
        index_elements=["phone"],
        set_={"name": customer_name, "total_visits": Customer.total_visits + 1},
    )
    await db.execute(stmt)
    await db.flush()

    display_time = start_time.strftime("%-I:%M %p")
    display_date = start_time.strftime("%B %d")

    # Send SMS to customer + salon owner
    await send_booking_confirmation_sms(
        customer_name=customer_name,
        customer_phone=phone,
        service_name=matched_service.name,
        stylist_name=best_stylist.name,
        date_str=display_date,
        time_str=display_time,
        appointment_id=appointment.id,
        price=matched_service.price,
    )

    # Send push notification to admin
    await send_admin_push_notification(
        db=db,
        title="New Booking Confirmed",
        body=f"{customer_name} — {matched_service.name} with {best_stylist.name} at {display_time} on {display_date}",
        data={"appointment_id": appointment.id, "type": "new_booking"},
    )

    return (
        f"Your appointment is confirmed! "
        f"{matched_service.name} on {display_date} at {display_time} "
        f"with {best_stylist.name}. "
        f"Your appointment ID is {appointment.id}. "
        f"A confirmation SMS has been sent to your phone. "
        f"See you then!"
    )


async def cancel_appointment(args: dict, db: AsyncSession) -> str:
    """
    Cancel an existing appointment.

    Args expected: { appointment_id?: str, phone?: str }
    """
    appointment_id = args.get("appointment_id")
    phone = args.get("phone")

    appointment = None

    if appointment_id:
        try:
            appt_id = int(appointment_id)
            result = await db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.id == appt_id,
                        Appointment.status == "booked",
                    )
                )
            )
            appointment = result.scalar_one_or_none()
        except (ValueError, TypeError):
            return "That doesn't seem like a valid appointment ID. Could you check and tell me again?"

    elif phone:
        # Find the latest upcoming booked appointment for this phone
        now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        result = await db.execute(
            select(Appointment)
            .where(
                and_(
                    Appointment.customer_phone == phone,
                    Appointment.status == "booked",
                    Appointment.start_time > now,
                )
            )
            .order_by(Appointment.start_time.asc())
            .limit(1)
        )
        appointment = result.scalar_one_or_none()
    else:
        return "I need your appointment ID or phone number to find your booking."

    if not appointment:
        return "I couldn't find an active booking. Could you verify your appointment ID or phone number?"

    # Check cancellation policy: must be > 1 hour before
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    appt_start = appointment.start_time
    if appt_start.tzinfo is None:
        appt_start = appt_start.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))

    if appt_start - now < timedelta(hours=1):
        return (
            "Sorry, appointments can only be cancelled at least 1 hour before the scheduled time. "
            "Your appointment is too soon to cancel."
        )

    # Cancel it
    appointment.status = "cancelled"
    await db.flush()

    display_time = appointment.start_time.strftime("%-I:%M %p on %B %d")
    return f"Your appointment at {display_time} has been cancelled successfully."


async def reschedule_appointment(args: dict, db: AsyncSession) -> str:
    """
    Reschedule an existing appointment to a new time.

    Args expected: { appointment_id: str, new_time: "ISO datetime" }
    """
    appointment_id = args.get("appointment_id")
    new_time_str = args.get("new_time")

    if not appointment_id:
        return "I need your appointment ID to reschedule. Could you provide it?"

    if not new_time_str:
        return "What new time would you like for your appointment?"

    # Find the appointment
    try:
        appt_id = int(appointment_id)
        result = await db.execute(
            select(Appointment)
            .where(and_(Appointment.id == appt_id, Appointment.status == "booked"))
            .options()
        )
        old_appointment = result.scalar_one_or_none()
    except (ValueError, TypeError):
        return "That doesn't seem like a valid appointment ID."

    if not old_appointment:
        return "I couldn't find an active booking with that ID."

    # Parse new time
    try:
        new_start = datetime.fromisoformat(new_time_str)
        if new_start.tzinfo is None:
            new_start = new_start.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    except (ValueError, TypeError):
        return "I couldn't understand the new time. Could you tell me again?"

    # Get service for duration
    svc_result = await db.execute(select(Service).where(Service.id == old_appointment.service_id))
    service = svc_result.scalar_one_or_none()
    if not service:
        return "There was an error finding your service. Please try again."

    new_end = new_start + timedelta(minutes=service.duration)

    # Find available stylist for new time (load balanced)
    stylists_result = await db.execute(
        select(Stylist).where(
            and_(
                Stylist.is_active == True,
                Stylist.specializations.contains([service.category])
            )
        )
    )
    stylists = stylists_result.scalars().all()

    best_stylist = None
    min_bookings = float("inf")
    target_date = new_start.date()

    for stylist in stylists:
        day_of_week = target_date.isoweekday() % 7
        if day_of_week in (stylist.days_off or []):
            continue

        # Check overlap
        overlap_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status == "booked",
                    Appointment.start_time < new_end,
                    Appointment.end_time > new_start,
                    Appointment.id != old_appointment.id,  # Exclude the current appointment
                )
            )
        )
        if overlap_result.scalar() > 0:
            continue

        # Load balance
        count_result = await db.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status == "booked",
                    func.date(Appointment.start_time) == target_date,
                )
            )
        )
        count = count_result.scalar()
        if count < min_bookings:
            min_bookings = count
            best_stylist = stylist

    if not best_stylist:
        return "Sorry, that new time is not available. Would you like to try another time?"

    # Mark old as rescheduled
    old_appointment.status = "rescheduled"

    # Create new appointment
    new_appointment = Appointment(
        service_id=service.id,
        stylist_id=best_stylist.id,
        customer_name=old_appointment.customer_name,
        customer_phone=old_appointment.customer_phone,
        start_time=new_start,
        end_time=new_end,
        status="booked",
    )
    db.add(new_appointment)
    await db.flush()

    display_time = new_start.strftime("%-I:%M %p on %B %d")
    return (
        f"Your appointment has been rescheduled to {display_time} "
        f"with {best_stylist.name}. "
        f"New appointment ID is {new_appointment.id}."
    )


async def get_customer_appointments(args: dict, db: AsyncSession) -> str:
    """
    Look up upcoming appointments for a customer by phone.

    Args expected: { phone: str }
    """
    phone = args.get("phone")
    if not phone:
        return "I need your phone number to look up your appointments."

    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    result = await db.execute(
        select(Appointment)
        .join(Service)
        .where(
            and_(
                Appointment.customer_phone == phone,
                Appointment.status == "booked",
                Appointment.start_time > now,
            )
        )
        .order_by(Appointment.start_time.asc())
    )
    appointments = result.scalars().all()

    if not appointments:
        return "You don't have any upcoming appointments."

    lines = []
    for appt in appointments:
        svc_result = await db.execute(select(Service).where(Service.id == appt.service_id))
        svc = svc_result.scalar_one_or_none()
        svc_name = svc.name if svc else "Service"
        display_time = appt.start_time.strftime("%-I:%M %p on %B %d")
        lines.append(f"{svc_name} at {display_time}, appointment ID {appt.id}")

    if len(lines) == 1:
        return f"You have 1 upcoming appointment: {lines[0]}."
    else:
        return f"You have {len(lines)} upcoming appointments: {'. '.join(lines)}."


# Tool dispatcher
TOOL_HANDLERS = {
    "checkAvailability": check_availability,
    "bookAppointment": book_appointment,
    "cancelAppointment": cancel_appointment,
    "rescheduleAppointment": reschedule_appointment,
    "getCustomerAppointments": get_customer_appointments,
}
