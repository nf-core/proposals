# Proposal automation — one-time org setup

The approval automation in `.github/workflows/` (pipeline / RFC / SIG) is
self-contained. The project-board `Status` automation below needs a one-time
configuration step from an **org owner**, because a GitHub Actions / app token
cannot grant itself project access.

## 1. Issue types (`Pipeline`, `RFC`, `Special Interest Group`) — optional, not currently enabled

Proposals are already distinguished by their template, their
`new-pipeline` / `new-rfc` / `new-special-interest-group` labels, and their
separate project boards, so native **issue types** are an optional extra rather
than a requirement. They are **not** wired up in this repo today.

If you later decide you want them (e.g. for `type:Pipeline` filtering in issue
search):

1. An org owner creates the types at
   **github.com/organizations/nf-core/settings/issue-types**, named exactly
   `Pipeline`, `RFC`, and `Special Interest Group`.
2. Add the matching `type:` key to each issue-form template, e.g.
   `type: "Pipeline"` in `new_pipeline.yml`.

> Order matters: the types must exist **before** the templates reference them,
> otherwise opening an issue from a template with an unknown `type:` fails
> validation. (The bot token can't manage types itself — it returns
> `403 Resource not accessible by integration` — which is why this is manual.)

## 2. Project board Status automation

The pipeline workflow now mirrors the approval status onto the
[pipelines project board](https://github.com/orgs/nf-core/projects/104) — the
`Status` field is set automatically, replacing the manual curator step that was
previously documented in the repo README:

| Approval status | Board `Status` option |
| --------------- | --------------------- |
| 🕐 Pending      | `proposed`            |
| ✅ Approved     | `accepted`            |
| ❌ Rejected     | `turned-down`         |
| ⏰ Timed Out    | `timed-out`           |

For this to take effect, the bot token (`secrets.nf_core_bot_auth_token`) needs
**read & write access to organisation projects**:

- Classic PAT: the `project` scope.
- Fine-grained PAT / app: organisation permission **Projects → Read and write**.

The update is **best-effort**: if the token lacks project access, the `Status`
field option names don't match, or the issue isn't on the board, the workflow
logs the reason and continues — the labels and status comment are unaffected.
The board's `Status` options must be named `proposed`, `accepted`,
`turned-down`, `timed-out` (they already are); adjust the `PROJECT_STATUS` map
at the top of `pipeline_proposals.yml` if they ever change.

### Enabling it for the RFC and SIG boards

The same capability is available to the RFC (`nf-core/127`) and SIG
(`nf-core/105`) workflows. To enable, add the same block near the top of
`rfc_approval.yml` / `sig_approval.yml`:

```js
const PROJECT_NUMBER = 127; // 105 for SIG
const PROJECT_STATUS = {
  "🕐 Pending": "proposed",
  "✅ Approved": "accepted",
  "❌ Rejected": "turned-down",
  "⏰ Timed Out": "timed-out",
};
```

and call `await approvalManager.updateProjectStatus(PROJECT_NUMBER, PROJECT_STATUS[status]);`
alongside each existing `updateIssueStatus(...)` call. Verify the option names
on those two boards match first.
