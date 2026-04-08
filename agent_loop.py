"""
Agent Loop — Canonical Reference Implementation
=================================================
A complete tool-using agent loop for the Anthropic Messages API.
Uses if/elif dispatch, json.dumps for tool results, and four
commented-out debug prints in the correct positions.

ENVIRONMENT ADAPTATION (side by side):

  Production (this file):
      response = client.messages.create(**BASE_REQUEST, messages=messages)

  Interview (with pre-provided call_claude helper):
      response = call_claude(messages, tools)

  If call_claude is provided, you don't need: client, MODEL, SYSTEM,
  BASE_REQUEST, or the anthropic import. Just use call_claude directly.

  To change the system prompt for Part 2, either:
    (a) Edit the system= line inside call_claude directly, or
    (b) Copy call_claude, rename it, and change the system= line, or
    (c) If system prompt is in a separate file, edit that file

CODESIGNAL ENVIRONMENT NOTES:
  - Full Ubuntu Linux environment with terminal access
  - Python 3.10.6 — match/case syntax IS supported (Python 3.10+)
  - pip install works: run in terminal if a package is missing
  - Filesystem-based: code may be in .py files, not notebook cells
  - To run: use the terminal with `python filename.py`
  - No autorun on save — you must manually run each time
  - The interviewer sees your screen AND your terminal output
  - If system prompt is in a separate file:
      from system_prompt import SYSTEM
    or just open the file, copy the string, and edit it inline
"""

import json
import traceback
import anthropic

# ============================================================
# 1) Client + config
# ============================================================

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

MODEL = "claude-sonnet-4-20250514"
SYSTEM = "You are a helpful agent. Use tools when needed."
MAX_ITERS = 10

# Tool specs go here (see tool_spec_reference.md for the shape)
TOOLS = [
    # lookup_item_spec,
    # calculate_spec,
]

BASE_REQUEST = {
    "model": MODEL,
    "max_tokens": 1024,
    "system": SYSTEM,
    "tools": TOOLS,
}


# ============================================================
# 2) Tool dispatch
#
# Pattern A — interview-style (functions take positional args):
#     if name == "get_item":
#         return get_item(tool_input["item_id"])
#
# Pattern B — production-style (functions take the full dict):
#     if name == "lookup_customer":
#         return lookup_customer(tool_input)
#
# Rule: if parameter is in the spec's "required" list,
#       use tool_input["key"] (safe to crash if missing).
#       If optional, use tool_input.get("key") or
#       tool_input.get("key", default_value).
# ============================================================

def dispatch_tool(name, tool_input):
    if name == "lookup_item":
        return lookup_item(tool_input["item_id"])
    elif name == "calculate":
        return calculate(tool_input["op"], tool_input["input1"], tool_input["input2"])
    else:
        raise Exception("Unknown tool: " + name)


# ============================================================
# 3) Agent loop
# ============================================================

def run_agent(prompt):
    messages = [{"role": "user", "content": prompt}]

    i = 0
    while i < MAX_ITERS:
        i = i + 1

        # --- API call ---
        response = client.messages.create(
            **BASE_REQUEST,
            messages=messages,
        )

        ## ----- DEBUG 1: Stop reason + turn count ----- ##
        # print("Turn {}: stop_reason={}".format(i, response.stop_reason))

        ## ----- DEBUG 2: Content block types ----- ##
        # for b in response.content:
        #     print("  block: type={} name={}".format(b.type, getattr(b, "name", "-")))

        # Always append assistant message first (may include tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        # If no tools requested, extract and return final text
        if response.stop_reason != "tool_use":
            parts = []
            for block in response.content:
                if block.type == "text":
                    parts.append(block.text)
            return "\n".join(parts).strip()

        # Gather all tool_use blocks from this response
        tool_uses = []
        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append(block)

        # Execute each tool and build tool_result blocks
        tool_results_blocks = []
        for tu in tool_uses:
            name = tu.name
            tool_input = tu.input

            try:
                ## ----- DEBUG 3: Tool I/O ----- ##
                # print("  calling {} with {}".format(name, tool_input))
                result = dispatch_tool(name, tool_input)
                # print("  got: {}".format(result))

                tool_results_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                    "is_error": False,
                })
            except Exception as e:
                traceback.print_exc()
                tool_results_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps({"error": str(e)}),
                    "is_error": True,
                })

        # All tool results go in ONE user message, immediately after the assistant message
        messages.append({"role": "user", "content": tool_results_blocks})

        ## ----- DEBUG 4: Full message history (nuclear option) ----- ##
        # print(json.dumps(messages, indent=2, default=str))

    # This return is OUTSIDE the while loop but INSIDE the function
    return "Stopped after {} iterations.".format(MAX_ITERS)


# ============================================================
# 4) Run
# ============================================================

if __name__ == "__main__":
    print(run_agent("Your test prompt here"))
