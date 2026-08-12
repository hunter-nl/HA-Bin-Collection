---
name: release-pipeline
description: Maintain, test, or diagnose Bin Collection release preparation, publishing, changelog, and release-note automation. Use for changes or failures involving Prepare release, Publish release, Release Drafter, git-cliff, release PRs, tags, or release assets.
---

# Release Pipeline

Treat the manually entered Prepare Release version as authoritative for published releases. Release Drafter may suggest a version only for its preview draft.

## Release flow

1. **Prepare release** is manually dispatched with a semantic version. It updates version files and `CHANGELOG.md`, then creates `release/<version>` as a PR to `main`.
2. The release PR is labelled `release`; exclude that label from Release Drafter output so a release PR never appears in its own notes.
3. Required PR checks and approval complete before auto-merge or manual merge. The merged release PR triggers **Publish release**.
4. **Publish release** reads the merged version, renders Release Drafter in dry-run mode with that explicit version/tag, and passes its `name` and `body` to `softprops/action-gh-release` with the Release Bot token.
5. Publish creates the tag, uploads `bin-collection.zip`, and may wait for the `release` environment’s configured deployment approval.

Do not use Release Drafter’s calculated version for the published tag. Do not use git-cliff for GitHub release notes; use it only for `CHANGELOG.md`.

## Changelog rules

- Use git-cliff’s per-commit remote fields: `remote.pr_number`, `remote.pr_title`, and `remote.pr_labels`.
- Keep one entry per pull request. Filter commits with an actual `remote.pr_number` before applying `unique(attribute="remote.pr_number")`; otherwise mixed null/number values make Tera fail.
- Group PRs through ordered `commit_parsers`; list breaking changes before fixes/features when labels overlap.
- Link the PR once. Do not apply a generic `#123` issue parser because it re-links a merge commit’s PR number as an issue.
- Link only explicit closing references such as `Fixes #123`, `Closes #123`, or `Resolves #123`, and preserve that closing verb in the rendered issue link.
- Use a semantic-version `tag_pattern`; git-cliff then ranges each version from the previous matching release tag.

git-cliff cannot infer closing issue references from a PR body unless that reference is available in the commit text or separate API automation is added.

## Validate changes

1. Parse changed workflow/configuration files:

   ```bash
   ruby -e 'require "yaml"; YAML.load_file(".github/workflows/prepare-release.yaml"); YAML.load_file(".github/workflows/publish-release.yaml"); YAML.load_file(".github/release-drafter.yml")'
   git-cliff --config .github/.git-cliff.toml --unreleased --tag vX.Y.Z --strip all --offline
   git diff --check
   ```

2. Treat an offline git-cliff output without PR entries as expected: offline mode has no GitHub PR metadata.
3. Validate remote-data behavior in GitHub Actions using the Release Bot token; diagnose from the exact workflow logs rather than generic suggestions.
4. Preserve GitHub tag rules that allow the Release Bot to create/update semver tags.
