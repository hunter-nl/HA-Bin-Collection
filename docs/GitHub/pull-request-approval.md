# Maintainer-approved pull requests

`main` is protected and requires one approving review. GitHub does not allow a
pull request author to approve their own pull request. This repository uses a
dedicated GitHub App to submit an ordinary GitHub approval after an authorized
maintainer comments `/approve` on a pull request targeting `main`.

The review is shown as `maintainer-approver[bot]`, not as the pull
request author, and therefore can satisfy the required-review rule.

## One-time setup

1. Open your GitHub account **Settings** → **Developer settings** → **GitHub
   Apps** → **New GitHub App**.
2. Name it `maintainer-approver` (the exact name is your choice), set a
   homepage URL to this repository, and disable **Active** under Webhook.
3. Under **Repository permissions**, set both **Contents** and **Pull
   requests** to **Read and write**. Leave all other permissions at **No
   access**.
4. Create the app and install it for each repository that should use it. The
   same app installation can serve multiple repositories.
5. On the app's settings page, generate a private key. Download the PEM file;
   it is shown only once.
6. In the repository, open **Settings** → **Secrets and variables** →
   **Actions** and add:

   | Type | Name | Value |
   | --- | --- | --- |
   | Variable | `APPROVAL_BOT_APP_ID` | The numeric App ID from the app settings page. |
   | Secret | `APPROVAL_BOT_PRIVATE_KEY` | The complete contents of the downloaded PEM file. |

## Use

After all required checks pass, comment exactly:

```
/approve
```

The **Maintainer approval** workflow submits an official GitHub approval at the
current PR head commit. A later code change dismisses that approval when the
branch rule's stale-review setting is enabled, so comment `/approve` again only
after reviewing the new diff.

## Branch rule for `main`

Under **Settings** → **Branches** → the `main` rule, enable:

- Require a pull request before merging.
- Require approvals: `1`.
- Dismiss stale pull request approvals when new commits are pushed.
- Require status checks to pass before merging.
- Require conversation resolution before merging.
- Do not allow bypassing the above settings.

Do not enable **Require review from Code Owners** if this bot is intended to
satisfy the required approval; an app review is not a code-owner review.

## Bootstrap

The workflow is evaluated from the default branch. It cannot approve the pull
request that first introduces it. Temporarily relax the required-approval rule
to merge this workflow once, then restore the rule immediately. All later pull
requests can use `/approve`.
