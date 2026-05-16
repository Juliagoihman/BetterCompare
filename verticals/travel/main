from mcp.server.fastmcp import FastMCP

mcp = FastMCP("travel-vertical")

@mcp.tool()
def search_travel_offers(destination: str, departure_date: str, return_date: str, travelers: int = 1) -> dict:
    """Search for package travel offers to a destination."""
    return {
        "offers": [
            {"hotel": "Ibis Barcelona", "flight": "Lufthansa", "total": 899.0, "stars": 3},
            {"hotel": "Hilton Barcelona", "flight": "Ryanair", "total": 1199.0, "stars": 5},
        ],
        "destination": destination,
        "dates": {"from": departure_date, "to": return_date},
        "travelers": travelers
    }

@mcp.tool()
def search_flights(origin: str, destination: str, date: str, passengers: int = 1) -> dict:
    """Search for available flights between two cities."""
    return {
        "flights": [
            {"airline": "Lufthansa", "departure": "08:00", "arrival": "10:30", "price": 189.0},
            {"airline": "Ryanair", "departure": "14:00", "arrival": "16:30", "price": 89.0},
        ],
        "route": f"{origin} → {destination}",
        "date": date
    }

@mcp.tool()
def search_hotels(destination: str, checkin: str, checkout: str, guests: int = 1) -> dict:
    """Search for available hotels at a destination."""
    return {
        "hotels": [
            {"name": "Hotel Mitte", "stars": 3, "price_per_night": 89.0},
            {"name": "Grand Hotel", "stars": 5, "price_per_night": 299.0},
        ],
        "destination": destination
    }

@mcp.tool()
def get_travel_insurance(destination: str, travelers: int, duration_days: int) -> dict:
    """Get travel insurance options for a trip."""
    return {
        "options": [
            {"name": "Basic", "price": 12.99, "covers": ["cancellation", "medical"]},
            {"name": "Premium", "price": 24.99, "covers": ["cancellation", "medical", "luggage"]},
        ],
        "destination": destination,
        "travelers": travelers,
        "duration_days": duration_days
    }

if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8803)
