# Agent Patterns

Reference implementations and patterns for building tool-using agents with the Anthropic Python SDK.


## Table of contents

### agent_loop.py — The canonical agent loop
- Environment adaptation (production vs interview side-by-side)
- CodeSignal environment notes
- Client + config setup
- Tool dispatch (if/elif pattern, .get() vs ["key"] rule)
- Agent loop (5 beats: call → append → check exit → execute tools → send results)
- Four debug prints in correct positions

### tool_spec_reference.md — Schemas, results, and response objects
- Tool spec shape (complete annotated skeleton)
- Supported JSON Schema types
- Enum constraints, arrays, optional parameters
- Tool result format (four fields, wrapping message shape)
- Response object attributes (stop_reason values, TextBlock, ToolUseBlock)
- Quick access patterns (extracting text, extracting tool_use blocks)
- tool_choice options (auto, any, tool, none, disable_parallel)

### debug_methods.md — Debugging techniques
- Debug 1: Stop reason + turn count
- Debug 2: Content block types
- Debug 3: Tool I/O
- Debug 4: Full message history
- Symptom-to-method map (API error, wrong answer, infinite loop, etc.)
- Common Python gotchas (indentation of safety return, tool results placement, mixed tabs/spaces, agent returns None)
- Three layers to check when results are wrong

### optimization_playbook.md — Part 2 turn reduction
- System prompt fill-in-the-blank skeleton
- Key phrases that reduce turns
- Tool description improvements (before/after examples)
- Pattern 1: Retrieve + Math
- Pattern 2: Search + Filter
- Pattern 3: Lookup + Validate + Act
- Pattern 4: Batch Operations
- Pattern 5: Compare Entities
- Quick decision guide (which pattern do I need?)
- Combo A: Retrieve + Math + Compare
- Combo B: Search + Filter + Act
- Combo C: Batch + Compute
- Combo D: Lookup + Compare
- Modifying the system prompt in the interview (3 options)

### python_quick_ref.md — Python patterns for agent code
- Dict access (.get, ["key"], .get with default)
- String operations (.strip, .lower, normalization order)
- Type conversion (str, float, int)
- JSON (json.dumps, json.loads)
- String formatting (.format)
- Lists (append, join, len)
- Math (sum, max, min, abs, round, average)
- Building dicts and lists from loops
- Dict iteration (.items)
- Checking existence (in, not in)
- Safe attribute access (getattr)
- Raising errors
- Global variables
- Common error types table
- match/case syntax (recognizing it in provided code)
- **kwargs unpacking (recognizing ** in provided code)

### error_reference.md — Error messages and fixes
- API errors (roles must alternate, tool_use_id not found, max_tokens)
- Python errors (TypeError, KeyError, NameError, IndentationError, AttributeError)
- Agent returns None
- Tool execution errors (wrong results, unknown tool, lookup returns nothing)

### checklist.md — Pre-run sanity check
- Tool specs checklist
- Tool handlers checklist
- Agent loop checklist
- Dispatch checklist


## Key resources

- [Anthropic tool use overview](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [How to implement tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Agent SDK overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
