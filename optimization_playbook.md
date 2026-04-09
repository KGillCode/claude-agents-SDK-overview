# Part 2 Optimization Playbook

Three levers to reduce API turn count. System prompt changes model behavior, tool descriptions change model understanding, tool design changes what's possible in one call.


## Lever 1: System prompt

### Fill-in-the-blank skeleton

```python
SYSTEM = """
You are a [ROLE] assistant. Use the provided tools for ALL [DOMAIN] operations.

RULES:
- NEVER do [OPERATION TYPE] in your head. Always use the [TOOL NAME] tool for any math or calculations.
- When you need multiple independent pieces of data, request ALL relevant tools in a single response rather than one at a time.
- [DOMAIN-SPECIFIC RULE, e.g., "Always normalize city names to lowercase."]
- [DOMAIN-SPECIFIC RULE, e.g., "Available items: chicken_breast, salmon, brown_rice, broccoli, avocado, egg, banana."]

WORKFLOW:
1. Gather all needed data first (use parallel tool calls when data is independent)
2. Perform any required calculations using the [TOOL NAME] tool
3. Provide a clear, concise final answer with the specific numbers

Keep your responses short and direct. Do not explain your reasoning unless asked.
""".strip()
```

### Key phrases that reduce turns
- "request ALL relevant tools in a single response" → enables parallel tool calls
- "NEVER do math in your head" → forces calculator usage, prevents wrong answers
- "Available items: ..." → prevents the model from guessing invalid inputs
- "Keep responses short" → reduces unnecessary back-and-forth


## Lever 2: Tool description improvements

### Before (minimal, Part 1 style):
```python
"description": "returns the current temperature for a city"
```

### After (optimized, Part 2 style):
```python
"description": (
    "Look up the current temperature for a city by name. "
    "Returns the temperature as a float in Fahrenheit. "
    "Available cities: denver, seattle, phoenix, miami, chicago, boston, portland. "
    "Always pass the city name in lowercase."
)
```

### What to improve:
- **Add enum constraints** to string parameters: `"enum": ["denver", "seattle", "phoenix"]`
- **List available values** in the description when the tool searches a fixed dataset
- **Explain what the tool returns** so the model knows what to expect
- **Explain when to use this tool** vs. other tools
- **Add input format guidance**: "pass as lowercase", "use ISO date format", etc.
- **Improve parameter descriptions**: `"description": "input1"` → `"description": "The first number in the calculation"`


## Lever 3: Tool redesign patterns

The biggest turn-count reduction comes from merging multiple tools into one so the model can accomplish in one call what previously took 3-4.

---

### Building block A: Expression-Based Calculator

**When to use:** They give you a calculator tool that takes two numbers and an operator. Replace it with one that takes a full expression string — collapses multi-step arithmetic into a single tool call.

```python
def evaluate(expression: str):
    allowed = set("0123456789+-*/.() ")
    if all(c in allowed for c in expression):
        return eval(expression)
    raise ValueError("Invalid expression")
```

One call handles the full expression: `(247.80 + 198.35 + 389.60) / 3`

---

### Building block B: Batch Lookup Tool

**When to use:** They give you a single-item lookup tool (e.g., get one city's temperature). Replace it with one that accepts a list — returns all values in one call, eliminates multiple parallel lookups.

```python
def get_weather_data(cities: list[str]):
    return {c: weather_db[c.lower()] for c in cities}
```

Spec param: `"type": "array", "items": {"type": "string"}`

---

### Pattern 1: Retrieve + Math

**When to use:** They give you a lookup tool and a separate calculator tool, and prompts require looking up multiple values then computing on them.

**The merge:** One tool that accepts a list of keys and an optional math operation.

```python
def compute_item_math(tool_input):
    items = tool_input.get("items", [])
    op = tool_input.get("op")

    catalog = {
        "item_a": 247.80,
        "item_b": 389.60,
        "item_c": 712.50,
        "item_d": 198.35,
        "item_e": 223.90,
    }

    # Look up all values
    values_by_name = {}
    value_list = []
    for item in items:
        key = item.lower()
        if key not in catalog:
            return {"error": "Unknown item: " + item}
        values_by_name[key] = catalog[key]
        value_list.append(catalog[key])

    # If no operation, just return the values
    if op is None:
        return values_by_name

    # Apply the operation
    if len(value_list) == 0:
        return {"error": "No items provided"}

    if op == "sum":
        result = sum(value_list)
    elif op == "average":
        result = sum(value_list) / len(value_list)
    elif op == "max":
        result = max(value_list)
    elif op == "min":
        result = min(value_list)
    elif op == "difference":
        if len(value_list) < 2:
            return {"error": "Need at least 2 items for difference"}
        result = abs(value_list[0] - value_list[1])
    else:
        return {"error": "Unknown operation: " + str(op)}

    return {"result": round(result, 2), "values": values_by_name}


compute_item_math_spec = {
    "name": "compute_item_math",
    "description": (
        "Look up values for one or more items, and optionally apply a math operation. "
        "Use this for ANY lookup or calculation instead of calling lookup and calculate separately. "
        "Available items: item_a, item_b, item_c, item_d, item_e."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of item names to look up.",
            },
            "op": {
                "type": "string",
                "enum": ["sum", "average", "max", "min", "difference"],
                "description": "Optional math operation to apply across the values.",
            },
        },
        "required": ["items"],
    },
}
```

---

### Pattern 2: Search + Filter

**When to use:** They give you a search tool and a separate filter tool, and prompts require searching then narrowing results.

**The merge:** One tool with the search query plus optional filter parameters.

```python
def search_catalog(tool_input):
    query = str(tool_input.get("query", "")).strip().lower()
    category = tool_input.get("category")
    max_price = tool_input.get("max_price")
    min_rating = tool_input.get("min_rating")

    catalog = [
        {"id": "P-1", "name": "Wireless Headphones", "category": "electronics", "price": 64.99, "rating": 4.3},
        {"id": "P-2", "name": "Running Shoes", "category": "apparel", "price": 95.00, "rating": 4.7},
        {"id": "P-3", "name": "Yoga Mat", "category": "fitness", "price": 42.00, "rating": 4.5},
        {"id": "P-4", "name": "Bluetooth Speaker", "category": "electronics", "price": 54.00, "rating": 3.7},
        {"id": "P-5", "name": "Water Bottle", "category": "fitness", "price": 22.00, "rating": 4.4},
    ]

    # Search by query (substring match on name and category)
    results = []
    for p in catalog:
        if query in p["name"].lower() or query in p["category"].lower():
            results.append(p)

    # Apply optional filters
    filtered = []
    for p in results:
        if category and p["category"] != category.lower():
            continue
        if max_price is not None and p["price"] > float(max_price):
            continue
        if min_rating is not None and p["rating"] < float(min_rating):
            continue
        filtered.append(p)

    return {"results": filtered, "count": len(filtered)}


search_catalog_spec = {
    "name": "search_catalog",
    "description": (
        "Search the product catalog by keyword, with optional filters. "
        "Use this instead of calling search and filter separately. "
        "Categories: electronics, apparel, fitness."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keyword."},
            "category": {
                "type": "string",
                "enum": ["electronics", "apparel", "fitness"],
                "description": "Optional category filter.",
            },
            "max_price": {"type": "number", "description": "Optional maximum price."},
            "min_rating": {"type": "number", "description": "Optional minimum rating."},
        },
        "required": ["query"],
    },
}
```

---

### Pattern 3: Lookup + Validate + Act

**When to use:** The prompt requires looking something up, checking a condition, then performing an action. Three separate tools become one gated tool.

**The merge:** One tool that does lookup → validation → action internally, returning the appropriate result at each gate.

```python
def process_item_return(tool_input):
    order_id = str(tool_input.get("order_id", "")).strip()
    item_id = str(tool_input.get("item_id", "")).strip()
    reason = str(tool_input.get("reason", "")).strip()

    if not order_id or not item_id or not reason:
        return {"error": "Missing required field(s)"}

    # Step 1: Lookup
    order = ORDERS.get(order_id)
    if not order:
        return {"status": "rejected", "reason": "order_not_found"}

    # Step 2: Find the item in the order
    item = None
    for it in order.get("items", []):
        if it.get("item_id") == item_id:
            item = it
    if not item:
        return {"status": "rejected", "reason": "item_not_in_order"}

    # Step 3: Validate against policy
    if item.get("final_sale"):
        return {"status": "rejected", "reason": "final_sale", "item": item}
    if not item.get("returnable"):
        return {"status": "rejected", "reason": "not_returnable", "item": item}

    # Step 4: Act — compute refund
    refund = item["unit_price"] * item["qty"]
    fee_pct = item.get("handling_fee_pct", 0)
    if fee_pct > 0:
        refund = refund * (1 - fee_pct / 100)

    return {
        "status": "approved",
        "item": item,
        "refund_amount": round(refund, 2),
        "handling_fee_pct": fee_pct,
    }


process_item_return_spec = {
    "name": "process_item_return",
    "description": (
        "Look up an order, validate an item against return policy, and process the return in one step. "
        "Use this instead of calling lookup, validate, and process separately."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order ID."},
            "item_id": {"type": "string", "description": "The item ID within the order."},
            "reason": {"type": "string", "description": "Reason for the return."},
        },
        "required": ["order_id", "item_id", "reason"],
    },
}
```

---

### Pattern 4: Batch Operations

**When to use:** They give you a single-item tool (e.g., add one expense) and test prompts require adding multiple items. Turn it into one call with an array.

```python
LEDGER = []
ENTRY_COUNTER = 0

def manage_expenses(tool_input):
    global ENTRY_COUNTER
    action = str(tool_input.get("action", "")).strip()

    if action == "add":
        entries = tool_input.get("entries", [])
        if not entries:
            return {"error": "No entries provided"}

        added = []
        for e in entries:
            ENTRY_COUNTER = ENTRY_COUNTER + 1
            record = {
                "entry_id": "EXP-{}".format(ENTRY_COUNTER),
                "amount": float(e.get("amount", 0)),
                "category": str(e.get("category", "other")),
                "description": str(e.get("description", "")),
            }
            LEDGER.append(record)
            added.append(record)
        return {"added": added, "total_entries": len(LEDGER)}

    elif action == "summary":
        totals = {}
        for e in LEDGER:
            cat = e["category"]
            totals[cat] = totals.get(cat, 0) + e["amount"]
        return {
            "totals_by_category": totals,
            "grand_total": sum(totals.values()),
            "entry_count": len(LEDGER),
        }

    elif action == "list":
        category = tool_input.get("category")
        if category:
            filtered = []
            for e in LEDGER:
                if e["category"] == category:
                    filtered.append(e)
        else:
            filtered = list(LEDGER)
        return {"entries": filtered, "count": len(filtered)}

    else:
        return {"error": "Unknown action: " + action}


manage_expenses_spec = {
    "name": "manage_expenses",
    "description": (
        "Add, list, or summarize expenses in one tool call. "
        "For 'add': pass an array of entries to add multiple at once. "
        "For 'summary': returns totals by category. "
        "For 'list': optionally filter by category."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "summary", "list"],
                "description": "What to do.",
            },
            "entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["amount", "category"],
                },
                "description": "Entries to add (only for action='add').",
            },
            "category": {
                "type": "string",
                "description": "Filter category (only for action='list').",
            },
        },
        "required": ["action"],
    },
}
```

---

### Pattern 5: Compare Entities

**When to use:** They give you a single-item lookup and the prompt asks "compare X vs Y" or "which is better, X or Y?" Turn it into one call that accepts a list.

```python
def compare_plans(tool_input):
    plan_names = tool_input.get("plans", [])
    if len(plan_names) < 2:
        return {"error": "Provide at least 2 plan names to compare"}

    catalog = {
        "starter": {"name": "Starter", "price": 0, "seats": 1, "storage_gb": 10},
        "pro": {"name": "Pro", "price": 39, "seats": 15, "storage_gb": 250},
        "enterprise": {"name": "Enterprise", "price": 119, "seats": 500, "storage_gb": 2000},
    }

    # Look up all plans
    plans = {}
    for name in plan_names:
        p = catalog.get(name.lower())
        if not p:
            return {"error": "Unknown plan: " + name}
        plans[name.lower()] = p

    # Build comparison between first two
    names = list(plans.keys())
    a = plans[names[0]]
    b = plans[names[1]]

    return {
        "plans": plans,
        "price_difference": abs(a["price"] - b["price"]),
        "seat_difference": abs(a["seats"] - b["seats"]),
        "storage_difference_gb": abs(a["storage_gb"] - b["storage_gb"]),
    }


compare_plans_spec = {
    "name": "compare_plans",
    "description": (
        "Look up two or more plans and return a structured comparison. "
        "Use this instead of calling get_plan multiple times. "
        "Available plans: starter, pro, enterprise."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "plans": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Plan names to compare.",
            },
        },
        "required": ["plans"],
    },
}
```

---

## Quick decision guide: which pattern do I need?

| The exercise gives you... | The prompt requires... | Use pattern |
|---|---|---|
| Lookup tool + calculator tool | Look up values then do math on them | **1: Retrieve + Math** |
| Search tool + filter tool | Search then narrow results | **2: Search + Filter** |
| Lookup + check + action as 3 tools | Multi-step gated workflow | **3: Lookup + Validate + Act** |
| Single-item add/create tool | Adding multiple items at once | **4: Batch Operations** |
| Single-item lookup tool | "Compare X vs Y" or "which is more" | **5: Compare Entities** |


## Combining patterns

Real exercises may need a mix of patterns. Here are the most likely combos:

### Combo A: Retrieve + Math + Compare (Patterns 1 + 5)

**When:** "Which of X, Y, Z is the most expensive, and by how much?"

Merge into one tool that accepts a list of items and an operation that includes comparison:

```python
def analyze_items(tool_input):
    items = tool_input.get("items", [])
    op = tool_input.get("op")

    catalog = {
        "item_a": 247.80, "item_b": 389.60, "item_c": 712.50,
        "item_d": 198.35, "item_e": 223.90,
    }

    values_by_name = {}
    value_list = []
    for item in items:
        key = item.lower()
        if key not in catalog:
            return {"error": "Unknown item: " + item}
        values_by_name[key] = catalog[key]
        value_list.append(catalog[key])

    if op is None:
        return values_by_name

    if len(value_list) == 0:
        return {"error": "No items provided"}

    if op == "sum":
        result = sum(value_list)
    elif op == "average":
        result = sum(value_list) / len(value_list)
    elif op == "max":
        result = max(value_list)
    elif op == "min":
        result = min(value_list)
    elif op == "difference":
        if len(value_list) < 2:
            return {"error": "Need at least 2 items"}
        result = abs(value_list[0] - value_list[1])
    elif op == "compare":
        # Find highest and lowest
        highest_name = ""
        highest_val = -1
        lowest_name = ""
        lowest_val = float("inf")
        for name in values_by_name:
            v = values_by_name[name]
            if v > highest_val:
                highest_val = v
                highest_name = name
            if v < lowest_val:
                lowest_val = v
                lowest_name = name
        result = {
            "highest": {"name": highest_name, "value": highest_val},
            "lowest": {"name": lowest_name, "value": lowest_val},
            "spread": round(highest_val - lowest_val, 2),
        }
        return {"comparison": result, "values": values_by_name}
    else:
        return {"error": "Unknown operation: " + str(op)}

    return {"result": round(result, 2), "values": values_by_name}
```

Spec adds `"compare"` to the enum:
```python
"op": {
    "type": "string",
    "enum": ["sum", "average", "max", "min", "difference", "compare"],
    "description": "Operation to apply. Use 'compare' to find highest/lowest.",
},
```

### Combo B: Search + Filter + Act (Patterns 2 + 3)

**When:** "Find available flights under $350 and book the cheapest one."

Merge search/filter into one tool, and add an optional `book` action:

```python
def search_and_book(tool_input):
    query = str(tool_input.get("query", "")).strip().lower()
    max_price = tool_input.get("max_price")
    book_id = tool_input.get("book_id")

    catalog = [
        {"id": "F-1", "route": "SFO-JFK", "price": 385.00, "available": True},
        {"id": "F-2", "route": "SFO-JFK", "price": 245.00, "available": True},
        {"id": "F-3", "route": "SFO-LAX", "price": 115.00, "available": False},
        {"id": "F-4", "route": "LAX-JFK", "price": 310.00, "available": True},
    ]

    # If booking, handle that first
    if book_id:
        match = None
        for f in catalog:
            if f["id"] == book_id:
                match = f
        if not match:
            return {"status": "error", "reason": "Flight not found: " + book_id}
        if not match["available"]:
            return {"status": "error", "reason": "Flight not available"}
        return {"status": "booked", "flight": match, "confirmation": "BK-7742"}

    # Otherwise, search and filter
    results = []
    for f in catalog:
        if query in f["route"].lower():
            if max_price is not None and f["price"] > float(max_price):
                continue
            results.append(f)

    return {"results": results, "count": len(results)}
```

### Combo C: Batch + Compute (Patterns 4 + 1)

**When:** "Add these 5 expenses and tell me the total by category."

The batch pattern already supports this — the `"summary"` action computes aggregates. Just make sure the spec description says "use action='add' to add multiple entries, then action='summary' to get totals."

### Combo D: Lookup + Compare (Patterns 3 + 5)

**When:** "Look up customer A and customer B and tell me which one has a higher plan tier."

```python
def compare_customers(tool_input):
    emails = tool_input.get("emails", [])
    if len(emails) < 2:
        return {"error": "Provide at least 2 emails"}

    customers = {}
    for email in emails:
        rec = CUSTOMER_DATA.get(email.lower())
        if not rec:
            return {"error": "Customer not found: " + email}
        customers[email.lower()] = rec

    # Build comparison
    names = list(customers.keys())
    plan_tiers = {"free": 0, "starter": 1, "pro": 2, "enterprise": 3}

    a = customers[names[0]]
    b = customers[names[1]]
    a_tier = plan_tiers.get(a.get("plan", "free"), 0)
    b_tier = plan_tiers.get(b.get("plan", "free"), 0)

    if a_tier > b_tier:
        higher = names[0]
    elif b_tier > a_tier:
        higher = names[1]
    else:
        higher = "same"

    return {
        "customers": customers,
        "higher_plan": higher,
        "plans": {names[0]: a.get("plan"), names[1]: b.get("plan")},
    }
```


## Important: modifying the system prompt in the interview

The pre-provided `call_claude` helper hardcodes the system prompt. To change it for Part 2:

**Option A** — Edit `call_claude` directly (simplest):
```python
def call_claude(messages, tools=[]):
    return client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        temperature=0.0,
        system="""
You are a helpful travel planning assistant. Use tools for ALL calculations.
NEVER do math in your head. Always use the calculate tool.
When you need temperatures for multiple cities, request ALL lookups in a single response.
""".strip(),
        tools=tools,
        messages=messages,
    )
```

**Option B** — If system prompt is in a separate file:
```python
# Open the file in the IDE, edit the string, save
# or import and override:
SYSTEM = """Your new system prompt here.""".strip()
```

**Option C** — Add a system parameter to call_claude:
```python
def call_claude(messages, tools=[], system="You are a helpful assistant."):
    return client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        temperature=0.0,
        system=system,
        tools=tools,
        messages=messages,
    )
```
