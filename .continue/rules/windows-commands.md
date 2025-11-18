---
description: A description of your rule
---

Example Prompt Rule
“Generate only Windows CMD commands, not Unix or Linux commands.”

“Do not use any instructions that rely on chmod, chown, mkdir -p, bash, or Linux/Unix shell syntax.”

“File paths should be Windows style (e.g., C:\folder\file.txt).”

“For permission changes, use icacls, and for directory creation, use mkdir without flags.”

“Explicitly avoid any commands that are recognized only in Unix shells.”