from mcp.server.fastmcp import FastMCP

mcp = FastMCP("insurance-vertical")

@mcp.tool()
def compare_insurance_plans(insurance_type: str, age: int) -> dict:
    """Compare insurance plans for a given type and customer age."""
    return {
        "plans": [
            {"provider": "Allianz", "monthly": 29.99, "deductible": 500},
            {"provider": "HUK", "monthly": 19.99, "deductible": 1000},
        ],
        "insurance_type": insurance_type,
        "age": age
    }

@mcp.tool()
def get_insurance_quote(insurance_type: str, age: int, coverage_amount: float) -> dict:
    """Get a specific insurance quote based on type, age, and desired coverage."""
    return {
        "quote": {
            "monthly_premium": round(coverage_amount * 0.001 + age * 0.5, 2),
            "annual_premium": round((coverage_amount * 0.001 + age * 0.5) * 12, 2),
            "coverage_amount": coverage_amount
        },
        "insurance_type": insurance_type
    }

@mcp.tool()
def list_insurance_types() -> dict:
    """List all available insurance types offered by CHECK24."""
    return {
        "types": [
            {"id": "haftpflicht", "name": "Haftpflichtversicherung", "description": "Personal liability"},
            {"id": "hausrat", "name": "Hausratversicherung", "description": "Home contents"},
            {"id": "kfz", "name": "Kfz-Versicherung", "description": "Car insurance"},
            {"id": "kranken", "name": "Krankenversicherung", "description": "Health insurance"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8804)
