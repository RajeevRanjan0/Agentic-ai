def calculate_price(quantity: int, unit_price: float) -> float:
    """
    Calculate the total price based on quantity and unit price.

    Args:
        quantity (int): The number of items.
        unit_price (float): The price per item.

    Returns:
        float: The total price.
    """
    return quantity * unit_price

def display_total_price(quantity: int, unit_price: float) -> str:
    """
    Create a message displaying the total price.

    Args:
        quantity (int): The number of items.
        unit_price (float): The price per item.

    Returns:
        str: A message displaying the total price.
    """
    total_price = calculate_price(quantity, unit_price)
    return f"The total cost for {quantity} items at ${unit_price} each is ${total_price}."