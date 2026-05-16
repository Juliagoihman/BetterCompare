from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mobile-vertical")

@mcp.tool()
def compare_mobile_plans(data_gb: int, calls_flat: bool = True) -> dict:
    """Compare mobile plans based on data volume and call options."""
    return {
        "plans": [
            {"provider": "Telekom", "data_gb": data_gb, "price": 29.99, "network": "5G"},
            {"provider": "Vodafone", "data_gb": data_gb, "price": 24.99, "network": "5G"},
            {"provider": "O2", "data_gb": data_gb, "price": 19.99, "network": "4G"},
        ]
    }

@mcp.tool()
def get_best_mobile_deal(data_gb: int, max_price: float = 999.0) -> dict:
    """Get the best mobile deal for given data needs and budget."""
    return {
        "best_plan": {"provider": "O2", "data_gb": data_gb, "price": 19.99},
        "max_price_filter": max_price
    }

@mcp.tool()
def check_network_coverage(address: str, provider: str) -> dict:
    """Check network coverage for a provider at a specific address."""
    return {
        "address": address,
        "provider": provider,
        "coverage": {"4G": True, "5G": True, "signal_strength": "excellent"}
    }

@mcp.tool()
def compare_phone_hardware(budget: float, brand: str = None) -> dict:
    """Compare available phones within a budget."""
    return {
        "phones": [
            {"model": "iPhone 15", "price": 799.0, "brand": "Apple"},
            {"model": "Samsung Galaxy S24", "price": 699.0, "brand": "Samsung"},
        ],
        "budget_filter": budget
    }

if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8802)
