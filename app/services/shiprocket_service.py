import httpx
from typing import Optional
from fastapi import HTTPException, status
from core.config import settings

# Default weight for basic serviceability check (in kg)
DEFAULT_SERVICEABILITY_WEIGHT = 0.5


class ShiprocketService:
    BASE_URL = "https://apiv2.shiprocket.in/v1/external"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token: Optional[str] = None

    async def authenticate(self):
        """
        Authenticate with Shiprocket API and store the token.
        """
        url = f"{self.BASE_URL}/auth/login"
        payload = {"email": self.email, "password": self.password}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            self.token = response.json().get("token")

    async def _get_headers(self):
        """
        Return headers with the authorization token.
        """
        if not self.token:
            raise ValueError("Authentication token is missing. Please authenticate first.")

        return {"Authorization": f"Bearer {self.token}"}

    async def check_serviceability(self, pickup_pincode: str, delivery_pincode: str, cod: bool, weight: float = 0.5):
        """
        Check serviceability for a given pickup and delivery pincode.
        """
        url = f"{self.BASE_URL}/courier/serviceability/"
        params = {
            "pickup_postcode": pickup_pincode,
            "delivery_postcode": delivery_pincode,
            "cod": int(cod),
            "weight": weight
        }

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def create_order(self, order_data: dict):
        """
        Create an order in Shiprocket.
        """
        url = f"{self.BASE_URL}/orders/create/adhoc"

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            return response.json()

    async def assign_courier(self, shipment_id: int):
        """
        Assign a courier to the shipment.
        """
        url = f"{self.BASE_URL}/courier/assign/awb"
        payload = {"shipment_id": shipment_id}

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_pickup(self, shipment_id: int):
        """
        Generate a pickup request for the shipment.
        """
        url = f"{self.BASE_URL}/courier/generate/pickup"
        payload = {"shipment_id": shipment_id}

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_manifest(self, shipment_id: int):
        """
        Generate a manifest for the shipment.
        """
        url = f"{self.BASE_URL}/manifests/generate"
        payload = {"shipment_id": shipment_id}

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_label(self, shipment_id: int):
        """
        Generate a shipping label for the shipment.
        """
        url = f"{self.BASE_URL}/courier/generate/label"
        payload = {"shipment_id": shipment_id}

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def print_invoice(self, order_id: int):
        """
        Print the invoice for the order.
        """
        url = f"{self.BASE_URL}/orders/print/invoice"
        payload = {"order_id": order_id}

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def track_shipment(self, awb_code: str):
        """
        Track the shipment using the AWB code.
        """
        url = f"{self.BASE_URL}/courier/track/awb/{awb_code}"

        async with httpx.AsyncClient() as client:
            headers = await self._get_headers()
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()


async def check_pincode_serviceability(
    shiprocket_service: ShiprocketService,
    delivery_pincode: str,
    weight: float = DEFAULT_SERVICEABILITY_WEIGHT
):
    """
    Check if a pincode is serviceable.
    Used for both address addition (default weight) and checkout (actual weight).
    """
    serviceability = await shiprocket_service.check_serviceability(
        pickup_pincode=settings.WAREHOUSE_PINCODE,
        delivery_pincode=delivery_pincode,
        cod=True,
        weight=weight
    )

    # Check if the response has available courier companies
    is_serviceable = (
        serviceability.get("status") == 200 and
        serviceability.get("data", {}).get("available_courier_companies")
    )

    return {
        "is_serviceable": is_serviceable,
        "available_couriers": serviceability.get("data", {}).get("available_courier_companies", []),
        "recommended_courier_id": serviceability.get("data", {}).get("recommended_courier_company_id"),
        "raw_response": serviceability
    }


async def check_checkout_serviceability(
    shiprocket_service: ShiprocketService,
    delivery_pincode: str,
    cart_weight: float
):
    """
    Check serviceability at checkout with actual cart weight.
    Returns available couriers with accurate pricing.
    """
    result = await check_pincode_serviceability(shiprocket_service, delivery_pincode, weight=cart_weight)

    if not result["is_serviceable"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery is not available for this address with the current cart items."
        )

    # Extract useful courier info for checkout
    couriers = []
    for courier in result["available_couriers"]:
        couriers.append({
            "courier_id": courier.get("courier_company_id"),
            "courier_name": courier.get("courier_name"),
            "rate": courier.get("rate"),
            "estimated_delivery_days": courier.get("estimated_delivery_days"),
            "etd": courier.get("etd"),
            "cod_available": courier.get("cod") == 1,
            "cod_charges": courier.get("cod_charges"),
            "is_recommended": courier.get("courier_company_id") == result["recommended_courier_id"]
        })

    return {
        "is_serviceable": True,
        "couriers": couriers,
        "recommended_courier_id": result["recommended_courier_id"]
    }