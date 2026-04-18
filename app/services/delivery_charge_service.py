from dataclasses import dataclass


@dataclass(frozen=True)
class DeliveryChargePolicy:
    base_charge: float
    free_delivery_threshold: float


def calculate_delivery_charge(subtotal: float, policy: DeliveryChargePolicy) -> float:
    """Return delivery charge for a given subtotal based on policy."""
    normalized_subtotal = round(float(subtotal), 2)

    if normalized_subtotal < 0:
        raise ValueError("Subtotal cannot be negative")

    if normalized_subtotal >= policy.free_delivery_threshold:
        return 0.0

    return round(policy.base_charge, 2)


def build_pricing_breakdown(
    subtotal: float,
    policy: DeliveryChargePolicy,
) -> dict:
    """Build a full stateless pricing breakdown for checkout/payment."""
    items_subtotal = round(float(subtotal), 2)
    delivery_charge = calculate_delivery_charge(items_subtotal, policy)
    grand_total = round(items_subtotal + delivery_charge, 2)

    return {
        "items_subtotal": items_subtotal,
        "delivery_charge": delivery_charge,
        "amount": grand_total,
    }
