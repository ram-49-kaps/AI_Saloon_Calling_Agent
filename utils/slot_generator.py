"""Slot generator — creates available time slots for stylists."""

from datetime import date, datetime, timedelta, time

from models.stylist import Stylist
from models.appointment import Appointment


def parse_time(time_str: str) -> time:
    """Parse 'HH:MM' string to time object."""
    h, m = map(int, time_str.split(":"))
    return time(h, m)


def generate_available_slots(
    target_date: date,
    service_duration: int,
    stylist: Stylist,
    existing_appointments: list[Appointment],
) -> list[dict]:
    """
    Generate available time slots for a stylist on a given date.

    Args:
        target_date: The date to check availability for.
        service_duration: Duration of the service in minutes.
        stylist: The stylist to check.
        existing_appointments: List of existing appointments for this stylist on this date.

    Returns:
        List of dicts with 'start' and 'display' keys.
    """
    work_start = parse_time(stylist.work_start)
    work_end = parse_time(stylist.work_end)

    # Check if the target date is a day off
    day_of_week = target_date.isoweekday() % 7  # 0=Sunday, 1=Monday, ..., 6=Saturday
    if day_of_week in (stylist.days_off or []):
        return []

    # Generate all possible slots
    slots = []
    current = datetime.combine(target_date, work_start)
    end_of_day = datetime.combine(target_date, work_end)

    while current + timedelta(minutes=service_duration) <= end_of_day:
        slot_end = current + timedelta(minutes=service_duration)

        # Check if this slot overlaps with any existing appointment
        is_available = True
        for appt in existing_appointments:
            appt_start = appt.start_time.replace(tzinfo=None) if appt.start_time.tzinfo else appt.start_time
            appt_end = appt.end_time.replace(tzinfo=None) if appt.end_time.tzinfo else appt.end_time

            # Overlap check: slot_start < appt_end AND slot_end > appt_start
            if current < appt_end and slot_end > appt_start:
                is_available = False
                break

        if is_available:
            # Don't show past slots for today
            now = datetime.now()
            if target_date == now.date() and current <= now:
                current += timedelta(minutes=30)
                continue

            slots.append({
                "start": current.isoformat(),
                "display": current.strftime("%-I:%M %p"),  # "10:00 AM"
            })

        # Move to next slot (30-minute intervals)
        current += timedelta(minutes=30)

    return slots


def format_slots_for_speech(slots: list[dict], max_slots: int = 5) -> str:
    """Format slots into a voice-friendly string."""
    if not slots:
        return "No available slots."

    display_slots = [s["display"] for s in slots[:max_slots]]

    if len(display_slots) == 1:
        return display_slots[0]
    elif len(display_slots) == 2:
        return f"{display_slots[0]} and {display_slots[1]}"
    else:
        return ", ".join(display_slots[:-1]) + f", and {display_slots[-1]}"
