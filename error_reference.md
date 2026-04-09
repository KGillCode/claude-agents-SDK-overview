# Error Reference

## API errors

**`"messages: roles must alternate between 'user' and 'assistant'"`**
You forgot to append the assistant message before appending tool results, or you appended two user messages in a row. The correct order is always: assistant message → user message (with tool results) → assistant message → ...

**`"tool_use_id not found"`**
The `tool_use_id` in your tool_result doesn't match any `tool_use` block's `.id` from the assistant response. Make sure you're using `tu.id` (the exact ID from the current response), not a hardcoded string or an ID from a previous turn.

**`"max_tokens" stop reason`**
The response was cut off before the model finished. Increase `max_tokens` in the API call. This can also cause the agent to return None if your exit condition only checks for `"end_turn"` — use `!= "tool_use"` instead.


## Python errors

**`TypeError: Object of type X is not JSON serializable`**
You're passing something to `json.dumps()` that can't be serialized (often an SDK object). Use `json.dumps(result, default=str)` as a safety net, or make sure your tool function returns a plain dict with only strings, numbers, booleans, lists, dicts, and None.

**`KeyError: 'city'`**
The model didn't send that parameter, or the key name doesn't match. Use `tool_input.get("key")` instead of `tool_input["key"]` for optional parameters. For required parameters, check that the key name in your code matches exactly what's in the tool spec's `properties`.

**`NameError: name 'X' is not defined`**
You're referencing a variable or function that hasn't been defined yet. Common causes: typo in variable name, forgot to run the cell that defines it, referencing a simulated data dict by the wrong name.

**`IndentationError: unexpected indent` / `unindent does not match`**
Mixed tabs and spaces, or wrong nesting level. In Colab: delete the leading whitespace on the problem line and re-type it with spaces. Select the whole block and check for consistency.

**`AttributeError: 'TextBlock' object has no attribute 'name'`**
You're trying to access `.name` on a text block. Text blocks have `.type` and `.text`. Tool use blocks have `.type`, `.name`, `.input`, and `.id`. Use `if block.type == "tool_use":` before accessing `.name`.

**Agent returns `None`**
A code path falls through without hitting a `return` statement. Most common cause: the stop_reason check uses `== "end_turn"` instead of `!= "tool_use"`, and the model returns with `"max_tokens"` which matches neither branch.


## Tool execution errors

**Tool returns wrong results but no error**
Check the three layers in order: (1) Does the function body actually use all parameters? (2) Does the mock data contain a matching entry? (3) Is the model sending the right input? See debug_methods.md.

**`"error": "Unknown tool: X"`**
Your dispatch function doesn't have a branch for that tool name. Add an `elif name == "X":` branch. Make sure the tool name string matches exactly (case-sensitive).

**Simulated data lookup returns nothing**
Check key format: if the dict keys are lowercase (`"denver"`) but the model sends uppercase (`"Denver"`), use `.lower()` before the lookup.
