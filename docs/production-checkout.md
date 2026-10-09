# Production checkout (2026-10-08)

The Oracle VM checkout of `hamidmatiny/aegis` is **not** `main`.

| | |
|---|---|
| Branch | `fix/xml-config-credential-framing` |
| Commit on the VM | `d9132a3099f66c8e7595c2c8e78801c5f3abb732` |
| Later commit on the PR, not on the VM | `3931b02` (quote-aware XML scan and a narrower negation) |
| PR | https://github.com/hamidmatiny/aegis/pull/96 (open, not merged) |
| Why it is deployed | BYPASS-005 and BYPASS-006 (XML config credential framing) are fixed on the deployed commit. `main` does not contain the fix. |

**Do not redeploy production from `main` until PR #96 is merged through the normal gate** (CI green and CodeRabbit APPROVED on the current head, then the armed auto-merge). A redeploy from `main` before that merge removes the XML rules and reopens both bypasses.

After the merge, redeploy from `main` and retest BYPASS-005 and BYPASS-006 (expect HTTP 403) and a benign control (expect HTTP 200).

This note is the warning. It is not a merge and not a force-merge.
