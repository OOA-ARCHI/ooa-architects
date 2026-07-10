---
description: Stage all changes, commit with an auto-generated message, and push to origin master
argument-hint: "[optional commit message]"
allowed-tools: Bash, Read
---

Run the following git workflow:

1. `git status` and `git diff` to see all changes (staged and unstaged).
2. `git add .` to stage everything.
3. Commit:
   - If the user supplied `$ARGUMENTS`, use it as the commit message verbatim.
   - Otherwise, write a concise commit message (1-2 sentences, focused on why) based on the diff, following this repo's existing commit style (see `git log -5 --oneline`).
4. `git push origin master`.
5. Report the resulting commit hash and confirm the push succeeded.

Do not use `--force`, `--no-verify`, or skip hooks. If the push is rejected (e.g. remote has new commits), stop and report it instead of force-pushing.
