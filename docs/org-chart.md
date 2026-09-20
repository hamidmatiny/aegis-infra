# Fleet org chart (Track B — personal Trinity agents)

**Canonical location:** this file in `aegis-infra` (`docs/org-chart.md`).  
**Also linked from:** each agent's `CLAUDE.md` (pointer only) and `aegis-infra/docs/a2a-routing.md`.  
**Public verification:** [docs/public-verification.md](./public-verification.md) (unauthenticated GitHub URLs).

**How to refresh:** call Trinity `list_agents` (exclude `trinity-system`). Do **not** treat this table as forever-true — tags + live list win when they disagree.

**Standing rule — Cursor workspace:** every new hire’s repo/folder is added to `/Users/hamidrezamatiny/Cursor/aegis-fleet.code-workspace` during onboarding (same pass as Trinity deploy / `/propose-agent-tier`), not later. See `/propose-agent-tier` Step 0.

*Snapshot: 2026-09-20 from live `list_agents` — **16** fleet agents (was 15 before `aegis-redteam`).*

```
Hamid (founder)
└── aegis-ceo                          [Executive · L5]
    ├── the-brain                      [Executive · VP]
    ├── aegis-infra                    [Infrastructure & Compute]
    ├── aegis-scout                    [Capability / Learning]
    ├── aegis-threat-intel             [Cybersecurity]
    ├── aegis-redteam                  [Cybersecurity · Red Team]  ← new
    ├── aegis-analyst                  [Finance]
    ├── aegis-core-infra               [Engineering]
    ├── aegis-data-quality             [Data / Quality]
    ├── aegis-growth                   [Growth / Marketing]
    └── aegis-product-eng              [Product Engineering · Manager · L5]
        ├── aegis-gateway
        ├── aegis-policy-engine
        ├── aegis-model-router
        ├── aegis-agent-gate
        └── aegis-audit
```

| Agent | Department | Reports to | Notes |
|-------|------------|------------|-------|
| aegis-ceo | Executive | Hamid | Founder-facing CEO agent |
| the-brain | Executive | aegis-ceo (peer VP) | Same-branch with CEO |
| aegis-infra | Infrastructure & Compute | aegis-ceo | OmniRoute, capacity HOLD |
| aegis-scout | Capability / Learning | aegis-ceo | Learning finds; does not install skills unilaterally |
| aegis-threat-intel | Cybersecurity | aegis-ceo | CVE / news watch |
| aegis-redteam | Cybersecurity | aegis-ceo | Live gateway attacks; Protocol D sink |
| aegis-analyst | Finance | aegis-ceo | MRR read-only |
| aegis-core-infra | Engineering | aegis-ceo | Product-repo infra diff review |
| aegis-data-quality | Data / Quality | aegis-ceo | Fleet output drift |
| aegis-growth | Growth / Marketing | aegis-ceo | Signups / SEO / directories |
| aegis-product-eng | Product Engineering | aegis-ceo | Manager of PE ICs |
| aegis-gateway | Product Engineering | aegis-product-eng | IC |
| aegis-policy-engine | Product Engineering | aegis-product-eng | IC |
| aegis-model-router | Product Engineering | aegis-product-eng | IC |
| aegis-agent-gate | Product Engineering | aegis-product-eng | IC |
| aegis-audit | Product Engineering | aegis-product-eng | IC |

`trinity-system` is platform infrastructure — **not** on this chart.

Peers with no reporting line (e.g. `aegis-infra` ↔ `aegis-scout`) still use this chart for orientation. Cross-branch **tasks** still follow Protocol A (manager-routed) unless an approved exception (verify-revenue, Protocol C HOLD, Protocol D technique handoff) applies.
