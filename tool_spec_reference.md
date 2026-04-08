# Tool Spec, Tool Result, and Response Object Reference

## Tool spec shape

```python
{
    "name": "snake_case_name",           # must match: ^[a-zA-Z0-9_-]{1,64}$
    "description": "What it does. When to use it. What it returns.",
    "input_schema": {
        "type": "object",               # always "object" at top level
        "properties": {
            "required_param": {
                "type": "string",
                "description": "What this parameter is for.",
            },
            "optional_enum_param": {
                "type": "string",
                "enum": ["option_a", "option_b", "option_c"],
                "description": "Constrained to these values.",
            },
            "number_param": {
                "type": "number",
                "description": "A numeric value.",
            },
            "list_param": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of strings.",
            },
            "list_with_enum": {
                "type": "array",
                "items": {"type": "string", "enum": ["a", "b", "c"]},
                "description": "A list constrained to specific values.",
            },
        },
        "required": ["required_param"],  # same level as "properties", not inside it
    },
}
```

**Supported JSON Schema types:** `string`, `number`, `integer`, `boolean`, `object`, `array`

**Making a parameter optional:** just leave it out of the `required` array. No special syntax needed.


## Tool result format

Each tool call gets one tool_result dict:

```python
{
    "type": "tool_result",               # always this exact string
    "tool_use_id": tu.id,                # must match the tool_use block's .id
    "content": json.dumps(result),       # MUST be a string — use json.dumps() for dicts, str() for simple values
    "is_error": False,                   # True if tool execution failed
}
```

All tool results from one response go in **ONE user message**:

```python
messages.append({"role": "user", "content": tool_results_blocks})
#                 ^^^^^^                      ^^^^^^^^^^^^^^^^^^^
#                 always "user"               list of tool_result dicts
```

This user message **must immediately follow** the assistant message that contained the tool_use blocks. No messages in between.


## Response object attributes

### response.stop_reason

| Value | Meaning | What to do |
|---|---|---|
| `"end_turn"` | Model is done | Extract text, return final answer |
| `"tool_use"` | Model wants tools run | Execute tools, send results, loop |
| `"max_tokens"` | Response was truncated | Increase max_tokens or handle gracefully |

### response.content (list of blocks)

A single response can contain BOTH text blocks AND tool_use blocks. Always iterate all of them.

**TextBlock:**
```python
block.type    # "text"
block.text    # the actual string content
```

**ToolUseBlock:**
```python
block.type    # "tool_use"
block.name    # tool name string (matches spec "name")
block.input   # dict — already parsed, not a string
block.id      # unique ID string — pass this back in tool_result
```

### Quick access patterns

```python
# Get final text from a response
parts = []
for block in response.content:
    if block.type == "text":
        parts.append(block.text)
final_text = "\n".join(parts).strip()

# Get all tool_use blocks from a response
tool_uses = []
for block in response.content:
    if block.type == "tool_use":
        tool_uses.append(block)
```


## tool_choice (controlling tool use behavior)

Pass as a parameter to `client.messages.create()` or mention to interviewer as a follow-up.

```python
tool_choice={"type": "auto"}                                    # Default: model decides
tool_choice={"type": "any"}                                     # Must use at least 1 tool
tool_choice={"type": "tool", "name": "calculate"}               # Must use this specific tool
tool_choice={"type": "none"}                                    # No tools allowed
tool_choice={"type": "any", "disable_parallel_tool_use": True}  # Exactly 1 tool call
tool_choice={"type": "auto", "disable_parallel_tool_use": True} # At most 1 tool call
```

Gotcha: with `"any"` or `"tool"`, Claude skips explanatory text and goes straight to the tool call.
