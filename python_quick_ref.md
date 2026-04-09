# Python Quick Reference for Agent Code

## Dict access

```python
d["key"]                    # crashes with KeyError if key missing
d.get("key")                # returns None if key missing
d.get("key", "default")    # returns "default" if key missing
d.get("key", 0)            # returns 0 if key missing (good for numbers)
```

## String operations

```python
s.strip()                   # remove leading/trailing whitespace
s.lower()                   # lowercase — ALWAYS do this BEFORE validation checks
s.upper()                   # uppercase
```

**Order matters:**
```python
# WRONG — validates before normalizing:
if city not in weather_db:    # "Denver" not in {"denver": ...} → fails
    return {"error": "..."}
city = city.lower()

# RIGHT — normalize first:
city = city.lower()
if city not in weather_db:    # "denver" in {"denver": ...} → works
    return {"error": "..."}
```

## Type conversion

```python
str(value)                  # anything to string (for tool results)
float(tool_input.get("amount"))  # string/int to float
int(tool_input.get("count"))     # string/float to int
```

## JSON

```python
json.dumps(result)          # dict/list → string (for tool_result content)
json.dumps(result, default=str)  # safety net for non-serializable objects
json.loads(string)          # string → dict/list (rarely needed — tu.input is already parsed)
```

## String formatting

```python
"Turn {}: stop={}".format(i, reason)       # positional
"Unknown tool: " + name                     # concatenation (simple cases)
"SUP-{}".format(counter)                    # ID generation
```

## Lists

```python
parts = []                  # create empty list
parts.append(item)          # add item to end
"\n".join(parts).strip()    # join list of strings with newlines
len(items)                  # length of list or dict
```

## Math (used in tool redesign patterns)

```python
sum(values)                 # sum a list of numbers: sum([1, 2, 3]) → 6
max(values)                 # largest: max([1, 2, 3]) → 3
min(values)                 # smallest: min([1, 2, 3]) → 1
len(values)                 # count: len([1, 2, 3]) → 3
abs(a - b)                  # absolute difference: abs(5 - 8) → 3
round(value, 2)             # round to 2 decimal places: round(3.14159, 2) → 3.14
sum(values) / len(values)   # average (watch for len == 0!)
```

## Building dicts and lists from loops

```python
# Building a dict from a loop
result = {}
for item in items:
    key = item.lower()
    result[key] = catalog[key]

# Building a list from a loop
values = []
for item in items:
    values.append(catalog[item.lower()])

# Filtering a list with a loop
filtered = []
for p in products:
    if p["price"] <= max_price:
        filtered.append(p)
```

## Dict iteration

```python
for key in my_dict:                        # iterate keys only
    print(key)

for key, value in my_dict.items():         # iterate key-value pairs
    print(key, value)

# Summing values in a dict
total = 0
for key in totals:
    total = total + totals[key]
# or just: total = sum(totals.values())
```

## Checking existence

```python
if key in my_dict:          # check if key exists in dict
if item not in my_list:     # check if item is NOT in list
```

## Safe attribute access (for SDK response objects)

```python
getattr(block, "name", "-")     # returns "-" if block has no .name attribute
block.type                       # direct access (use when you know it exists)
```

## Raising errors in tool functions

```python
raise Exception("Unknown tool: " + name)     # general exception
raise ValueError("Unknown operation: " + op)  # more specific
```

## Global variables (for stateful tools like counters)

```python
COUNTER = 0

def my_tool(tool_input):
    global COUNTER              # required to modify a module-level variable
    COUNTER = COUNTER + 1
    return {"id": "ID-{}".format(COUNTER)}
```

## Common error types you'll see

| Error | Cause | Fix |
|---|---|---|
| `KeyError: 'city'` | Dict key doesn't exist | Use `.get("key")` or check `if key in dict` first |
| `TypeError: not JSON serializable` | Passing non-serializable to json.dumps | Add `default=str` or convert the value first |
| `NameError: name 'X' not defined` | Variable/function not defined or cell not run | Check spelling, run the cell that defines it |
| `IndentationError` | Mixed tabs/spaces or wrong nesting | Re-type the indentation with spaces |
| `AttributeError: 'X' has no attribute 'Y'` | Accessing wrong attribute on an object | Check the object type — TextBlock has .text, ToolUseBlock has .name/.input/.id |


## match/case syntax (Python 3.10+)

The interview exercise may use this for a calculator tool. It's Python's version of a switch statement.

```python
match op:
    case "+":
        return input1 + input2
    case "-":
        return input1 - input2
    case "*":
        return input1 * input2
    case "/":
        return input1 / input2
```

You don't need to write match/case yourself — `if/elif` works identically and is what you've memorized. But recognize it when you see it in the provided code.


## **kwargs unpacking

You may see this in provided example code:

```python
get_weather(**tool_call.input)
# is equivalent to:
get_weather(city=tool_call.input["city"])
```

`**dict` unpacks a dict into keyword arguments. It works when the dict keys match the function parameter names exactly. Your dispatch approach (explicitly extracting each parameter) is safer and more readable for the interview.
