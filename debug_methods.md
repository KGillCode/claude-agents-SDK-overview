# Debug Methods

## The four debug prints

These go in your agent loop as commented-out lines. Uncomment the one you need.

### Debug 1: Stop reason + turn count
**Position:** right after the API call, before appending assistant message
```python
print("Turn {}: stop_reason={}".format(i, response.stop_reason))
```

### Debug 2: Content block types
**Position:** right after the API call
```python
for b in response.content:
    print("  block: type={} name={}".format(b.type, getattr(b, "name", "-")))
```

### Debug 3: Tool I/O
**Position:** inside the tool execution loop, before and after dispatch
```python
print("  calling {} with {}".format(name, tool_input))
result = dispatch_tool(name, tool_input)
print("  got: {}".format(result))
```

### Debug 4: Full message history (nuclear option)
**Position:** at the end of the while loop, after appending tool results
```python
print(json.dumps(messages, indent=2, default=str))
```


## Symptom → method map

| Symptom | Try first | Why |
|---|---|---|
| API error / crash | Debug 4: full message history | See if messages are malformed (wrong roles, missing fields) |
| Wrong answer | Debug 3: tool I/O | Check if tool got the right input and returned the right output |
| Infinite loop | Debug 1: stop_reason + turn count | See if stop_reason is never changing |
| `"tool_use_id not found"` error | Debug 2 + Debug 3 | Check that tu.id matches what you're sending back |
| Tool crashes / exception | Check the traceback output | The try/except already catches it — read what it prints |
| Agent ignores a tool | Debug 2: content block types | See if the model is even requesting that tool |
| Works on simple prompts, fails on complex | Debug 2: content blocks | Check for parallel tool calls you might not be handling |
| Returns None | Debug 1: stop_reason | Might be "max_tokens" (truncated) instead of "end_turn" |


## Common Python gotchas in agent loops

### Indentation of the safety return
The `return "Stopped after..."` line must be OUTSIDE the `while` loop but INSIDE the function. One indent level, not two.

```python
def run_agent(prompt):
    messages = [...]
    i = 0
    while i < MAX_ITERS:
        i = i + 1
        # ... loop body ...
        messages.append({"role": "user", "content": tool_results_blocks})
                                                                          # ← end of while loop body
    return "Stopped after {} iterations.".format(MAX_ITERS)               # ← OUTSIDE while, INSIDE function
```

If this line is indented to the while-loop level, it runs after every iteration and your agent stops after one turn. If it's at the module level (no indent), it's not inside the function and returns nothing.

### Tool results append placement
`messages.append({"role": "user", "content": tool_results_blocks})` goes inside the `while` loop but OUTSIDE the `for tu in tool_uses` loop. You collect ALL results first, then append ONE message.

```python
        # WRONG — appends a separate message for each tool result:
        for tu in tool_uses:
            result = dispatch_tool(tu.name, tu.input)
            messages.append({"role": "user", "content": [{"type": "tool_result", ...}]})

        # RIGHT — collect all results, then append once:
        tool_results_blocks = []
        for tu in tool_uses:
            result = dispatch_tool(tu.name, tu.input)
            tool_results_blocks.append({"type": "tool_result", ...})
        messages.append({"role": "user", "content": tool_results_blocks})
```

### Mixed tabs and spaces
If code looks correct but Python throws `IndentationError`, you probably have invisible tab characters mixed with spaces. In Colab: select the block, delete the leading whitespace on the problem line, and re-type it with spaces.

### Agent returns None
If your function returns `None` instead of text, you have a code path that falls through without hitting a `return` statement. Most common cause: the `stop_reason` check uses `== "end_turn"` instead of `!= "tool_use"`, and the model returns with `stop_reason == "max_tokens"` which matches neither.

### The three layers to check when results are wrong
1. **Does the tool function actually use all its parameters?** The function accepts the parameter but the body ignores it — no error, just wrong results.
2. **Does the mock data contain what you're searching for?** The function works but there's no matching entry in the hardcoded data.
3. **Is the model sending the right input to the tool?** Use Debug 3 to check what the model actually sent.

Check in this order. Layers 1-2 are your code; layer 3 is model behavior (fix with prompting).
