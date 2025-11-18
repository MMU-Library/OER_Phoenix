
# The One Rule

<important_rules>

## System Environment

You are assisting a user working in:
- **OS**: Windows
- **Shell**: CMD (Command Prompt)
- **IDE**: VS Code with Continue extension
- **Primary Languages**: Python, HTML, YAML, Shell scripts (.bat, .cmd)
- **Tech Stack**: Django, OAI-PMH, PostgreSQL, ChromaDB, Docker Compose
- **Package Manager**: pip
- **Container Tool**: docker-compose (with hyphen)

**Generate only Windows CMD commands**, never Unix/Linux shell commands.

**Do not** use chmod, chown, mkdir -p, bash, sh, or any Linux/Unix shell syntax.

**File paths must use Windows style:** `C:\folder\file.txt` (not `/folder/file.txt`).

For permissions: use `icacls` (not chmod/chown).  
For directory creation: use `mkdir` (not mkdir -p).  
For directory listing: use `dir` (not ls).  
For file operations: use `copy`, `move`, `del` (not cp, mv, rm).

---

## Code Block Formatting

**Always** include the language **and** file path in code blocks.  
If editing `src\main.py`, your code block should start with:

Use Windows path separators (\) in code block headers, not forward slash.

Example:

python

---

## Code Modification Format

When addressing code modification requests, present concise snippets emphasizing only necessary changes with abbreviated placeholders for unmodified sections.

Example:

... existing code ...
{{ modified code here }}

... existing code ...
{{ another modification }}

... rest of code ...


**Always** restate the function or class that the snippet belongs to:

... existing code ...
class OERResource(models.Model):
# ... existing fields ...


{{ new field or modification here }}

# ... rest of class ...
... rest of code ...


For large code blocks (>20 lines), use brief, language-appropriate placeholders:  
- Python/YAML: `# ... existing code ...`  
- HTML: `<!-- ... existing code ... -->`  
- JavaScript: `// ... existing code ...`  

**Only provide complete files when explicitly requested.**

---

## Code Modification Specificity

When adding code to files, specify exact locations using:
- **Line numbers** (e.g., "Add after line 45"), OR
- **Surrounding con** (show 2-3 lines before/after insertion point)

Show clear before/after snippets for modifications.

Explicitly denote new additions vs existing code.

**Never** say "add this somewhere" — always specify WHERE with con.

---

## Response Format

Lead with the exact command or syntax needed for immediate use.

Format commands in code blocks for easy copying:

docker-compose build --no-cache && docker-compose up



After the command, provide a brief explanation of what it does and why.

Keep answers concise, structured, and easily searchable.

---

## Common Command Patterns (Quick Reference)

Docker fresh build without cache:
docker-compose build --no-cache && docker-compose up



Docker build and run:
docker-compose up --build



Install Python requirements:
pip install -r requirements.txt



Create directory:
mkdir foldername



Create nested directories:
mkdir parent\child\grandchild



List directory contents:
dir



Change file permissions (grant read/write to user):
icacls C:\path\to\file.txt /grant username:(R,W)



---

## Project Con Awareness

Before proposing fixes:
- Review project scope and architecture
- List any overlooked dependencies, configurations, or external calls
- Reference code/metadata summaries when available

Tech stack details:
- **Web Framework**: Django
- **Metadata Protocol**: OAI-PMH
- **Databases**: PostgreSQL (primary), ChromaDB (vector store)
- **Containerization**: Docker Compose
- **Vector Store**: ChromaDB for Meta-RAG code summaries

---

**This is "The One Rule" — your overarching base rule for this project.  
Any other rules must defer to this rule.**

</important_rules>