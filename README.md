# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Built for CodePath AI201 Project 2.

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file:
GROQ_API_KEY=your_key_here

Run the app:
```bash
python app.py
```

Then open http://127.0.0.1:7860 in your browser.

---

## Tool Inventory

### `search_listings(description: str, size: str | None, max_price: float | None) → list[dict]`
Searches 40 mock secondhand listings by keyword relevance, filtered by size and price. Returns a list of matching listing dicts sorted by score (best match first). Each dict contains: id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Returns empty list if nothing matches.

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`
Calls the Groq LLM to suggest 1-2 outfit combinations using the new item and the user's existing wardrobe pieces. If the wardrobe is empty, returns general styling advice instead. Always returns a non-empty string.

### `create_fit_card(outfit: str, new_item: dict) → str`
Calls the Groq LLM to generate a 2-4 sentence Instagram-style caption for the thrifted find and outfit. Uses temperature=1.2 for variety. Returns an error string if outfit is empty — never raises an exception.

---

## How the Planning Loop Works

The agent parses the user's natural language query using regex to extract a description, size, and max_price. It then calls search_listings. If results come back empty, the agent sets an error message and returns early — suggest_outfit is never called with empty input. If results exist, the top result is selected and passed into suggest_outfit along with the user's wardrobe. The outfit suggestion is then passed into create_fit_card. Each step's output flows directly into the next — the agent does not call all three tools unconditionally.

---

## State Management

All state lives in a session dict initialized at the start of each run:
- `query` — original user input
- `parsed` — extracted description, size, max_price
- `search_results` — full list of matches from search_listings
- `selected_item` — top result, passed to suggest_outfit
- `wardrobe` — user's wardrobe dict
- `outfit_suggestion` — LLM output from suggest_outfit, passed to create_fit_card
- `fit_card` — final LLM output
- `error` — set on early termination, None on success

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Sets session["error"] with message: "No listings found for '...'. Try broader keywords, a higher price, or skip the size filter." Returns early — remaining tools are skipped. |
| `suggest_outfit` | Wardrobe is empty | Prompts the LLM for general styling advice instead of specific combinations. Always returns a non-empty string. |
| `create_fit_card` | Outfit string is empty or whitespace | Returns "Error: No outfit suggestion provided — cannot generate a fit card." Never raises an exception. |

**Concrete example from testing:**
```bash
python -c "from tools import create_fit_card; print(create_fit_card('', {'title': 'Test', 'price': 10, 'platform': 'depop'}))"
# Output: Error: No outfit suggestion provided — cannot generate a fit card.
```

---

## Interaction Walkthrough

**User query:** "vintage graphic tee under $30"

**Step 1 — search_listings**
- Input: description="vintage graphic tee", size=None, max_price=30.0
- Why: First tool always called to find matching listings
- Output: List of matching listings; top result = Y2K Baby Tee — Butterfly Print, $18, depop

**Step 2 — suggest_outfit**
- Input: new_item=Y2K Baby Tee dict, wardrobe=example_wardrobe (10 items)
- Why: Results were found, so agent proceeds to styling
- Output: Two outfit combinations using baggy straight-leg jeans + chunky white sneakers, and wide-leg khaki trousers + black combat boots

**Step 3 — create_fit_card**
- Input: outfit=suggestion string, new_item=Y2K Baby Tee dict
- Why: Outfit suggestion exists, so agent generates shareable caption
- Output: "I just scored this adorable Y2K Baby Tee with a butterfly print for $18 on Depop..."

**Final output to user:**
Three panels in the Gradio UI — listing details, outfit suggestion, and fit card caption.

---

## Spec Reflection

**One way planning.md helped during implementation:**
Defining the exact failure mode for each tool before writing any code made error handling straightforward. Knowing that search_listings should return an empty list (not raise an exception) and that the agent should stop early meant the planning loop logic was clear before a single line was written.

**One divergence from the spec, and why:**
The original spec suggested the planning loop might use the LLM to parse the user's query. In implementation, regex was used instead for extracting size and price. This was faster, more predictable, and didn't require an extra API call for something that pattern matching handles reliably.

---

## AI Usage

**Instance 1 — search_listings implementation:**
Gave Claude the Tool 1 spec (inputs, return value, failure mode) and asked it to implement the function using load_listings() from the data loader. Reviewed the generated code to confirm it filtered by all three parameters and returned an empty list on no matches. Tested with 3 queries before trusting it.

**Instance 2 — planning loop implementation:**
Gave Claude the architecture diagram and planning loop description from planning.md and asked it to implement run_agent() in agent.py. Reviewed to confirm it branched on empty search results and stored values in the session dict at each step. Ran both the happy path and no-results path to verify correct behavior.