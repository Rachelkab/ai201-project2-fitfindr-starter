"""
agent.py
FitFindr planning loop — orchestrates the three tools via a session dict.
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from natural language query."""
    parsed = {}

    # Extract price
    price_match = re.search(r"under\s+\$?(\d+)", query, re.IGNORECASE)
    if price_match:
        parsed["max_price"] = float(price_match.group(1))

    # Extract size
    size_match = re.search(r"\bsize\s+([A-Z0-9/]+)\b", query, re.IGNORECASE)
    if size_match:
        parsed["size"] = size_match.group(1).upper()

    # Description = query minus the size/price parts
    description = re.sub(r"under\s+\$?\d+", "", query, flags=re.IGNORECASE)
    description = re.sub(r"\bsize\s+[A-Z0-9/]+\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\b(looking for|i want|find me|a|an|the)\b", "", description, flags=re.IGNORECASE)
    parsed["description"] = description.strip()

    return parsed


def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query
    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    # Step 3: Search listings
    results = search_listings(
        description=parsed.get("description", query),
        size=parsed.get("size"),
        max_price=parsed.get("max_price"),
    )
    session["search_results"] = results

    if not results:
        session["error"] = (
            f"No listings found for '{query}'. "
            "Try broader keywords, a higher price, or skip the size filter."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=wardrobe,
    )

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )

    # Step 7: Return session
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")