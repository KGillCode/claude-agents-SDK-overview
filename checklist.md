# Pre-Run Checklist

Scan this before running your code. Takes 10 seconds.

## Tool specs
- [ ] Tool `name` in spec matches the function name in dispatch
- [ ] `input_schema` has `"type": "object"`, has `"properties"`, has `"required"`
- [ ] Types match: strings are `"string"`, numbers are `"number"`, arrays are `"array"` with `"items"`
- [ ] Array enums use: `"items": {"type": "string", "enum": [...]}` not `"type": "string"` on the array itself
- [ ] `"required"` is at the same level as `"properties"` (not inside it)

## Tool handlers
- [ ] Variables assigned from `tool_input` BEFORE being used (no NameError)
- [ ] Handler returns a dict — not a set (`{"error": "msg"}` not `{"error"}`)
- [ ] No duplicate keys in simulated data dicts

## Agent loop
- [ ] Assistant message appended BEFORE checking stop_reason
- [ ] Tool results use `tu.id` for `tool_use_id` and `json.dumps()` for content
- [ ] Tool results appended as `role: "user"` not `role: "assistant"`
- [ ] All tool results from one response go in ONE user message
- [ ] The safety return (`"Stopped after..."`) is outside `while` but inside the function

## Dispatch
- [ ] Every tool name has a matching branch
- [ ] `else: raise Exception("Unknown tool: " + name)` is present
- [ ] Required params use `tool_input["key"]`, optional params use `tool_input.get("key")`
