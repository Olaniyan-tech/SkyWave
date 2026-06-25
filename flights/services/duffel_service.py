import requests
import logging
from django.conf import settings


logger = logging.getLogger(__name__)

DUFFEL_BASE_URL = settings.DUFFEL_BASE_URL

def get_headers():
    return {
        "Authorization": f"Bearer {settings.DUFFEL_ACCESS_TOKEN}",
        "Duffel-Version": "v2",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def search_flights(origin, destination, departure_date, adults=1, cabin_class='economy', return_date=None):
    slices = [
        {
            "origin": origin,
            "destination": destination,
            "departure_date": str(departure_date),
        }
    ]

    if return_date:
        slices.append({
            "origin": destination,
            "destination": origin,
            "departure_date": str(return_date),
        })

    url = f"{DUFFEL_BASE_URL}/air/offer_requests"
    payload = {
        "data": {
            "slices": slices,
            "passengers": [{"type": "adult"} for _ in range(adults)],
            "cabin_class": cabin_class.lower(),
        }
    }

    try:
        response = requests.post(
            url, 
            headers=get_headers(),
            json=payload, 
            timeout=30
        )
        data = response.json()

        if response.status_code != 201:
            logger.error(f"Duffel search error: {data}")
            return {"success": False, "error": data.get("errors", [{}])[0].get("message", "Search failed")}

        offers = data.get("data", {}).get("offers", [])
        return {"success": True, "data": offers, "count": len(offers)}
    
    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out.'}

    except requests.RequestException as e:
        logger.error(f"Duffel request error: {e}")
        return {'success': False, 'error': 'Service is currently unavailable. Please try again later.'}
    

def get_offer(offer_id):
    try:
        response = requests.get(
            f"{DUFFEL_BASE_URL}/air/offers/{offer_id}", 
            headers=get_headers(),
            timeout=30
        )
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Duffel get offer error: {data}")
            return {"success": False, "error": data.get("errors", [{}])[0].get("message", "Failed to retrieve offer")}

        offer = data.get("data", {})
        return {"success": True, "data": offer}
    
    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out.'}

    except requests.RequestException as e:
        logger.error(f"Duffel get offer error: {e}")
        return {'success': False, 'error': 'Service is currently unavailable. Please try again later.'}


def search_airports(query):
    #Search airports and cities by keyword.#

    try:
        response = requests.get(
            f"{DUFFEL_BASE_URL}/places/suggestions", 
            headers=get_headers(),
            params={"query": query},
            timeout=30
        )
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Duffel search airports error: {data}")
            return {"success": False, "error": "Failed to search airports"}

        airports = data.get("data", [])
        return {"success": True, "data": airports, "count": len(airports)}
    
    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out.'}

    except requests.RequestException as e:
        logger.error(f"Duffel search airports error: {e}")
        return {'success': False, 'error': 'Service is currently unavailable. Please try again later.'}