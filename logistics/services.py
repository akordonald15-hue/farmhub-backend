# logistics/services.py
"""
Reusable service functions for the logistics app.
These functions encapsulate dispatch creation, assignment,
status updates, and delivery confirmation so that other apps
can call them cleanly without import conflicts.
"""

import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Dispatch,
    DispatchStatusUpdate,
    LogisticsAgent,
    Vehicle
)


def generate_reference_code(prefix="DSP"):
    """
    Generates a clean, unique tracking code.
    Example: DSP-3F9A7C
    """
    unique = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{unique}"


def create_dispatch_from_order(order, created_by=None):
    """
    Automatically create a dispatch when an order is placed.

    Returns:
        Dispatch instance
    """
    return Dispatch.objects.create(
        order=order,
        pickup_address=order.pickup_address if hasattr(order, "pickup_address") else "",
        dropoff_address=order.delivery_address if hasattr(order, "delivery_address") else "",
        reference_code=generate_reference_code("ORD"),
        created_by=created_by,
    )


def create_dispatch_from_supply(supply_record, created_by=None):
    """
    Auto-create a dispatch for a supply record coming from farmers.
    """
    return Dispatch.objects.create(
        supply_record=supply_record,
        pickup_address=supply_record.pickup_location if hasattr(supply_record, "pickup_location") else "",
        dropoff_address=supply_record.dropoff_location if hasattr(supply_record, "dropoff_location") else "",
        reference_code=generate_reference_code("SUP"),
        created_by=created_by,
    )


def assign_agent(dispatch_id, agent_id, vehicle_id=None, assigned_by=None):
    """
    Assign a logistics agent (and optionally a vehicle) to a dispatch.
    """
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)
    agent = get_object_or_404(LogisticsAgent, pk=agent_id)

    dispatch.assigned_agent = agent

    if vehicle_id:
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        dispatch.assigned_vehicle = vehicle

    dispatch.status = "ASSIGNED"
    dispatch.save()

    DispatchStatusUpdate.objects.create(
        dispatch=dispatch,
        status="ASSIGNED",
        note="Agent assigned via service",
        created_by=assigned_by,
    )
    return dispatch


def update_dispatch_status(dispatch_id, new_status, note="", location="", updated_by=None):
    """
    Reusable status-updating logic for agents and admin.
    """
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)

    # special timestamps
    if new_status == "PICKED_UP":
        dispatch.pickup_time = timezone.now()

    if new_status == "DELIVERED":
        dispatch.delivery_time = timezone.now()

    dispatch.status = new_status
    dispatch.save(update_fields=["status", "pickup_time", "delivery_time", "updated_at"])

    # log status history
    status_log = DispatchStatusUpdate.objects.create(
        dispatch=dispatch,
        status=new_status,
        note=note,
        location=location,
        created_by=updated_by
    )

    return status_log


def confirm_delivery(dispatch_id, receiver_name, proof_url="", updated_by=None):
    """
    Saves the delivery proof and finalizes the dispatch.
    """
    dispatch = get_object_or_404(Dispatch, pk=dispatch_id)

    dispatch.receiver_name = receiver_name
    dispatch.proof_of_delivery_url = proof_url
    dispatch.status = "DELIVERED"
    dispatch.delivery_time = timezone.now()
    dispatch.save()

    DispatchStatusUpdate.objects.create(
        dispatch=dispatch,
        status="DELIVERED",
        note="Delivery confirmed",
        created_by=updated_by,
    )

    return dispatch


def calculate_logistics_cost(distance_km: float, vehicle_type: str = "MOTORCYCLE"):
    """
    Simple reusable cost calculator.
    You can improve this anytime, but this is a clean baseline.

    Rate examples:
        MOTORCYCLE – ₦120/km
        VAN – ₦200/km
        TRUCK – ₦350/km
        KEKE – ₦80/km
    """
    BASE_RATES = {
        "MOTORCYCLE": 120,
        "VAN": 200,
        "TRUCK": 350,
        "Keke": 80,
    }

    rate = BASE_RATES.get(vehicle_type, 120)
    return round(rate * distance_km, 2)
