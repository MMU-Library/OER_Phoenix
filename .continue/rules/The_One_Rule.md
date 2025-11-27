---
name: The One Rule
description: Windows CMD-First Overarching OER Agent Rule (Meta-RAG)
priority: highest
binding: true
category: system
version: v1.2
# No agent or rule may override The One Rule
---

# The One Rule (MANDATORY CONTEXT)

You are assisting a user working in:
- **OS:** Windows
- **Shell:** CMD (Command Prompt)
- **IDE:** VS Code with Continue extension
- **Primary Languages:** Python, HTML, YAML, Shell scripts (.bat, .cmd)
- **Tech Stack:** Django, OAI-PMH, PostgreSQL, ChromaDB, Docker Compose
- **Package Manager:** pip
- **Container Tool:** docker-compose (with hyphen)

**MANDATORY CONSTRAINTS:**
- Only generate Windows CMD commands, scripts, and file paths (never Unix/Linux shell commands).
- Never use or suggest chmod, chown, mkdir -p, bash, sh, or any Linux/Unix-specific syntax.
- All file paths must use explicit Windows syntax: `C:\folder\file.txt`.
- File operations must use CMD-native commands:
  - Permissions: `icacls`
  - Directory creation: `mkdir` (not mkdir -p)
  - Directory listing pipeline: `dir`
  - File operations: `copy`, `move`, `del`
- For Python, pip, Docker Compose, always use explicit file references (e.g., `requirements.txt`, `docker-compose.yml`).

# Response Standards

## Output Format
- **Commands/Code**: Always start with the immediate CMD or script a user should run, formatted in a syntax-highlighted code block.
- **Modification Snippets**: Always show file path and language, then only changed lines with clear before/after context (use ... for unmodified lines).
    ```
    # C:\project\api\oer_resource.py (python)
    ... existing code ...
    {{ modified/new code here }}
    ... existing code ...
    ```
- **Location Specification**: Always state "Add after line 37" or "Between lines 10–12", or cite the closest method/class boundaries.
- **Log Reference**: For all operational/log commands, direct agent output to the appropriate log file as specified in `logging` from local config.
- **Change Trace**: After each file operation or mod, output a brief, structured summary block listing: `file_path`, `lines_changed`, and a one-line summary of what was changed.

## Instructional Process

- **Do not guess**: If context, file, or location is ambiguous, request clarification before acting.
- **Project Awareness**: Before any fix, review project scope, relevant config, and recent agent actions. List all discovered dependencies/configs/external calls before proposing code or fixes.
- **Environment Validation**: For any new/modified script or config, always provide a one-line CMD for validation/testing, when possible (or brief instructions).
- **Explicit Routing**: When a task is out-of-scope (e.g., API/web search, metadata mapping), escalate to the agent role defined in `agent_roles` who explicitly handles it.
- **Self-verification**: Step through logic verbally before final output; check that all constraints above are met.

# Examples and Patterns

## Quick Reference (Windows CMD)
- Docker: `docker-compose build --no-cache && docker-compose up`
- Install Python requirements: `pip install -r requirements.txt`
- Make directory/tree: `mkdir parent\child\grandchild`
- List directory: `dir`
- Permissions: `icacls C:\folder\file.txt /grant username:(R,W)`

## Code Edit
- For large mods:
    ```
    # ... existing code ...
    # ... see full source for unmodified logic ...
    ```
- For new files: Output only when explicitly requested and show path.

# Versioning and Upgradability

- When project tech, vector store, or agent config changes, note schema/version increment in summary.
- Agents should log all changes referencing config version and timestamp (for audit/reproducibility).

# Overriding and Deference

- **All other agent rules or role instructions must defer to The One Rule.**
- This includes code/metadata, web search, harvesting, mapping, and setup agents.

# Scope Review/Dependency Checklist (PRE-FIX STEP — MANDATORY)
Before proposing any fix or action, list:
  - External dependencies (libraries, APIs)
  - Related/affected configuration files
  - Required environment variables
  - Any external service calls
Cross-reference each proposed change with project context (`config`, `vector_store`, `agent_roles`, etc.).

