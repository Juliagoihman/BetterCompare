# verticals/internet/main.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("internet-vertical")

@mcp.tool()
def compare_internet_offers(address: str, min_speed: int = 0) -> dict:
    """Compare internet offers for a given address and minimum speed."""
    return {
        "offers": [
            {"provider": "Telekom", "speed": 100, "price": 39.99, "contract_months": 24},
            {"provider": "Vodafone", "speed": 250, "price": 44.99, "contract_months": 12},
            {"provider": "O2", "speed": 50, "price": 29.99, "contract_months": 24},
        ],
        "address": address,
        "min_speed_filter": min_speed
    }

@mcp.tool()
def get_best_internet_deal(address: str, max_price: float = 999.0) -> dict:
    """Get the single best internet deal for a given address."""
    return {
        "best_offer": {"provider": "Telekom", "speed": 100, "price": 39.99},
        "address": address,
        "filtered_by_max_price": max_price
    }

@mcp.tool()
def check_availability(address: str, provider: str = None) -> dict:
    """Check if internet service is available at a given address."""
    return {
        "available": True,
        "address": address,
        "provider": provider or "all",
        "technologies": ["DSL", "Fiber", "Cable"]
    }

if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8801)
