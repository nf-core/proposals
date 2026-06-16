# Proposal automation — one-time org setup

The approval automation in `.github/workflows/` (pipeline / RFC / SIG) is
self-contained, but two enhancements need a one-time configuration step from an
**org owner**, because a GitHub Actions / app token cannot perform them itself.

## 1. Issue types (`Pipeline`, `RFC`, `Special Interest Group`)

The issue-form templates set a native **issue type** via the `type:` key:

| Template                         | `type:` value            |
| -------------------------------- | ------------------------ |
| `new_pipeline.yml`               | `Pipeline`               |
| `new_rfc.yml`                    | `RFC`                    |
| `new_special_interest_group.yml` | `Special Interest Group` |

Issue types are defined at the **organisation** level, so they must exist
**before** these template changes are merged, otherwise opening an issue from a
template that references a missing type will fail validation.

**Org owner steps (do this first):**

1. Go to **github.com/organizations/nf-core/settings/issue-types**.
2. Create three types with names matching the table above _exactly_
   (they are case-sensitive). Suggested descriptions:
   - **Pipeline** — A proposal for a new nf-core pipeline.
   - **RFC** — A request for comment on a major cross-community change.
   - **Special Interest Group** — A proposal for a new nf-core special interest group.
3. Once the types exist, this PR is safe to merge.

> The integration token used here returns `403 Resource not accessible by integration` when listing/managing issue types, which is why this step is manual.

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
