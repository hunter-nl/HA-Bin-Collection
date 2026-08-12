---
name: project-change-delivery
description: Deliver changes to the Bin Collection repository through a dedicated branch and pull request. Use for any code, documentation, configuration, workflow, or project-skill change that will modify the repository.
---

# Project Change Delivery

Keep `main` protected and make every change reviewable.

## Start safely

1. Inspect `git status --short --branch` and preserve unrelated changes.
2. Never edit or commit on `main`.
3. Create a purpose-named branch from the current remote main branch. Immediately remove the inherited upstream so VS Code offers **Publish Branch**, rather than trying to sync into `main`:

   ```bash
   git switch -c <prefix>/<description> origin/main
   git branch --unset-upstream
   ```

4. If the workspace contains uncommitted work for a different task, do not carry it into the new branch. Use a separate worktree or ask for direction.

Use `fix/`, `feature/`, `docs/`, or `chore/` as appropriate.

## Implement and validate

1. Keep the diff limited to the requested task.
2. Follow `AGENTS.md`, including the relevant validation commands.
3. For Python changes, run the proportionate checks; run the full project suite when the change warrants it:

   ```bash
   uv run ruff check && uv run ruff format --check && uv run ty check && uv run pytest
   ```

4. Always run `git diff --check` before committing.

## Commit, publish, and open the PR

1. Review the staged diff and commit only task-related files with a concise Conventional Commit message.
2. On the first push, publish the current branch itself. Do not use a `<local-branch>:main` refspec.

   ```bash
   git push -u origin HEAD
   ```

   In VS Code, use **Publish Branch** for this first push. After publishing, **Sync Changes** is safe and targets the branch instead of `main`.

3. Create a pull request with `main` as the base branch. Summarize the change and validation performed. Treat terminal output as private: never include test-session output, absolute local paths, usernames, or other machine-specific details in PR descriptions or comments. State only concise validation results.
4. Write the pull request description as actual Markdown. Use real line breaks and Markdown lists; never send literal `\\n` escape sequences to GitHub.
5. Enable GitHub auto-merge with an allowed merge method after creating the pull request. It must still wait for the required checks and review; do not bypass them.
6. Do not bypass required checks, reviews, branch rules, or deployment gates.
