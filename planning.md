# FitFindr — planning.md

---

## Tools

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset for items matching the user's description, filtered by size and price. Returns the best matches sorted by keyword relevance score.

**Input parameters:**
- `description` (str): Keywords describing what the user wants (e.g. "vintage graphic tee")
- `size` (str | None): Size to filter by, case-insensitive. None skips size filtering.
- `max_price` (float | None): Maximum price inclusive. None skips price filtering.

**What it returns:**
A list of matching listing dicts sorted by relevance. Each dict contains: id, title, description, category, style_tags (list), size, condition, price (float), colors (list), brand, platform. Returns empty list if nothing matches.

**What happens if it fails or returns nothing:**
Agent sets session["error"] to a helpful message telling the user to try broader keywords, higher price, or remove size filter. Returns early — does NOT call suggest_outfit with empty input.

---

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item and the user's wardrobe, calls the Groq LLM to suggest 1-2 complete outfit combinations using specific wardrobe pieces.

**Input parameters:**
- `new_item` (dict): The listing dict for the item the user is considering buying.
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty.

**What it returns:**
A non-empty string with outfit suggestions. If wardrobe is empty, returns general styling advice for the item instead.

**What happens if it fails or returns nothing:**
If wardrobe is empty, the LLM is prompted for general styling ideas rather than specific combinations. Never returns an empty string.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short 2-4 sentence Instagram-style caption for the thrifted find and outfit, using the Groq LLM at high temperature for variety.

**Input parameters:**
- `outfit` (str): The outfit suggestion string from suggest_outfit.
- `new_item` (dict): The listing dict for the thrifted item.

**What it returns:**
A casual, authentic caption mentioning the item name, price, and platform naturally. Sounds different each time due to temperature=1.2.

**What happens if it fails or returns nothing:**
If outfit is empty or whitespace, returns a descriptive error string — does NOT raise an exception.

---

## Planning Loop

After initializing the session, the agent parses the query with regex to extract description, size, and max_price. It then calls search_listings. If results is empty, it sets session["error"] and returns early — suggest_outfit is never called with empty input. If results exist, it sets selected_item = results[0] and calls suggest_outfit. The output is stored in session["outfit_suggestion"] and passed into create_fit_card. The final fit card is stored in session["fit_card"] and the session is returned.

---

## State Management

All state is stored in a session dict initialized at the start of each run. Fields: query (original input), parsed (extracted description/size/price), search_results (list of matches), selected_item (top result), wardrobe (user's wardrobe), outfit_suggestion (LLM output), fit_card (LLM output), error (set on early termination). Each tool reads from and writes to this dict — no global state, no re-prompting the user between steps.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Sets session["error"] with message to try broader keywords or higher price. Returns early, skips remaining tools. |
| suggest_outfit | Wardrobe is empty | Prompts LLM for general styling advice instead of specific combinations. Always returns a non-empty string. |
| create_fit_card | Outfit input is missing or empty | Returns a descriptive error string instead of raising an exception. |

---

## Architecture
User query

│

▼

_parse_query() — extracts description, size, max_price via regex

│

▼

Planning Loop

│

├─► search_listings(description, size, max_price)

│       │ results=[]

│       ├──► session["error"] = "No listings found..." → return session (early exit)

│       │

│       │ results=[item, ...]

│       ▼

│   session["selected_item"] = results[0]

│       │

├─► suggest_outfit(selected_item, wardrobe)

│       │ wardrobe empty → general styling advice

│       │ wardrobe has items → specific outfit combinations

│       ▼

│   session["outfit_suggestion"] = "..."

│       │

└─► create_fit_card(outfit_suggestion, selected_item)

│ outfit empty → return error string

▼

session["fit_card"] = "..."

│

▼

return session

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**
Used Claude. Gave it the tool spec for each function (inputs, return value, failure mode) one at a time and asked it to implement the function in tools.py using load_listings() from the data loader. Verified each tool worked with isolated terminal tests before moving on.

**Milestone 4 — Planning loop and state management:**
Used Claude. Gave it the architecture diagram and planning loop description and asked it to implement run_agent() in agent.py. Verified by running python agent.py and checking both the happy path and no-results path produced correct output.

---

## A Complete Interaction (Step by Step)

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers."

**Step 1:**
Agent parses the query: description="vintage graphic tee", max_price=30.0, size=None. Calls search_listings("vintage graphic tee", size=None, max_price=30.0). Returns 3 matching listings sorted by relevance. Top result: Y2K Baby Tee — Butterfly Print, $18, depop.

**Step 2:**
Agent sets selected_item = Y2K Baby Tee listing. Calls suggest_outfit(selected_item, example_wardrobe). LLM returns two outfit combinations using baggy straight-leg jeans + chunky white sneakers, and wide-leg khaki trousers + black combat boots.

**Step 3:**
Agent calls create_fit_card(outfit_suggestion, selected_item). LLM returns a casual Instagram caption mentioning the tee, $18 price, and Depop naturally.

**Final output to user:**
Three panels in the UI: listing details (title, price, platform, condition, style tags), outfit suggestions with specific wardrobe pieces named, and a shareable fit card caption.