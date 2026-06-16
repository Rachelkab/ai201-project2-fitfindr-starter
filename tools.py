"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    Returns an empty list if nothing matches — does NOT raise an exception.
    """
    listings = load_listings()

    # Filter by price and size
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and size.lower() not in item["size"].lower():
            continue
        filtered.append(item)

    # Score by keyword overlap with description
    keywords = description.lower().split()
    scored = []
    for item in filtered:
        searchable = (
            item["title"] + " " +
            item["description"] + " " +
            " ".join(item["style_tags"]) + " " +
            item["category"]
        ).lower()
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.
    If wardrobe is empty, offers general styling advice instead.
    """
    client = _get_groq_client()

    item_desc = f"{new_item['title']} (${new_item['price']}, {new_item['condition']} condition, {new_item['platform']})"

    if not wardrobe.get("items"):
        prompt = f"""A user is considering buying this thrifted item: {item_desc}
They haven't set up their wardrobe yet. Give them 1-2 general outfit ideas for this piece — what kinds of items pair well with it, what vibe it suits, and how to style it. Keep it casual and specific."""
    else:
        wardrobe_list = "\n".join(
            f"- {item['name']} ({item.get('color', '')} {item.get('fit', '')})"
            for item in wardrobe["items"]
        )
        prompt = f"""A user is considering buying this thrifted item: {item_desc}

Their current wardrobe includes:
{wardrobe_list}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe. Name the exact wardrobe pieces. Keep it casual and actionable."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable Instagram-style caption for the outfit.
    Returns an error string if outfit is empty — does NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return "Error: No outfit suggestion provided — cannot generate a fit card."

    client = _get_groq_client()

    prompt = f"""Write a 2-4 sentence Instagram caption for this thrift find and outfit.

Item: {new_item['title']} — ${new_item['price']} from {new_item['platform']}
Outfit: {outfit}

Rules:
- Sound like a real person posting an OOTD, not a product description
- Mention the item name, price, and platform once each naturally
- Be specific about the vibe
- Keep it casual, fun, maybe one emoji"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=1.2,
    )
    return response.choices[0].message.content