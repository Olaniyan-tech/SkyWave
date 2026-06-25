from bookings.models import Passenger, Booking
from django.db import transaction
from flights.services.duffel_service import get_offer
from django.utils.dateparse import parse_datetime
from bookings.tasks import send_booking_confirmation_email, send_booking_cancelled_email
import logging

logger = logging.getLogger(__name__)



def extract_flight_data(offer_id, offer):
    try:
        slice_ = offer['slices'][0]
        segment = slice_['segments'][0]
        airline = segment['marketing_carrier']
        return_slice = offer['slices'][1] if len(offer['slices']) > 1 else None
        baggage = segment.get('passengers', [{}])[0].get('baggages', [])


        return {
            "success": True,
            "data": {
                "offer_id": offer_id,
                "trip_type": "ROUND_TRIP" if return_slice else "ONE_WAY",
                "origin_airport": slice_["origin"]["iata_code"],
                "destination_airport": slice_["destination"]["iata_code"],
                "departure_time": parse_datetime(segment["departing_at"]),
                "arrival_time": parse_datetime(segment["arriving_at"]),
                "airline_name": airline["name"],
                "airline_iata_code": airline["iata_code"],
                "flight_number": segment["marketing_carrier_flight_number"],
                "cabin_class": segment["passengers"][0]["cabin_class"],
                "base_amount": offer["base_amount"],
                "tax_amount": offer["tax_amount"],
                "total_amount": offer["total_amount"],
                "currency": offer["total_currency"],
                "baggage_allowance": baggage,
                "return_departure_time": parse_datetime(return_slice["segments"][0]["departing_at"]) if 
return_slice else None,
                "return_arrival_time": parse_datetime(return_slice["segments"][0]["arriving_at"]) if 
return_slice else None
            }
        }

    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing Duffel offer: {e}")

        return {
            "success": False,
            "error": "Could not parse flight details from offer. Please try again."
        }


def create_booking(user, offer_id, passengers_data):
    offer_result = get_offer(offer_id)
    if not offer_result['success']:
        return {
            "success": False,
            "error": f"Could not retrieve flight offer: {offer_result['error']}"
        }

    flight_data_result = extract_flight_data(offer_id, offer_result["data"])
    if not flight_data_result["success"]:
        return {
            "success": False,
            "error": flight_data_result["error"]
        }
    
    flight_data = flight_data_result["data"]

    try:
        with transaction.atomic():
            booking = Booking.objects.create(user=user, **flight_data)

            for passenger_data in passengers_data:
                passenger = Passenger.objects.create(**passenger_data)
                booking.passengers.add(passenger)
        
        send_booking_confirmation_email.delay(booking.id)
        
        return {"success": True, "booking": booking}
    
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return {
            "success": False,
            "error": "Failed to create booking. Please try again."
        }


def cancel_booking(booking):
    if not booking.is_cancellable:
        return {
            "success": False,
            "error": f"Booking cannot be cancelled. Current status is {booking.booking_status}."
        }

    try:
        booking.booking_status = "CANCELLED"
        booking.save()

        send_booking_cancelled_email.delay(booking.id)
        
        return {"success": True, "message": "Booking cancelled successfully."}
    
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        return {
            "success": False,
            "error": "Failed to cancel booking. Please try again."
        }