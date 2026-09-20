# Track B public verification

**Purpose:** Unauthenticated proof that Track B (personal Trinity fleet) repos exist and match the org chart — same class of check as reading `hamidmatiny/aegis` without a token.

## Public repos (HTTP 200 without auth)

| Agent | Public URL |
|-------|------------|
| aegis-ceo | https://github.com/hamidmatiny/aegis-ceo |
| the-brain | https://github.com/hamidmatiny/the-brain |
| aegis-infra | https://github.com/hamidmatiny/aegis-infra |
| aegis-threat-intel | https://github.com/hamidmatiny/aegis-threat-intel |
| aegis-redteam | https://github.com/hamidmatiny/aegis-redteam |
| aegis-analyst | https://github.com/hamidmatiny/aegis-analyst |
| aegis-core-infra | https://github.com/hamidmatiny/aegis-core-infra |
| aegis-data-quality | https://github.com/hamidmatiny/aegis-data-quality |
| aegis-growth | https://github.com/hamidmatiny/aegis-growth |
| aegis-product-eng | https://github.com/hamidmatiny/aegis-product-eng |
| aegis-gateway | https://github.com/hamidmatiny/aegis-gateway |
| aegis-policy-engine | https://github.com/hamidmatiny/aegis-policy-engine |
| aegis-model-router | https://github.com/hamidmatiny/aegis-model-router |
| aegis-agent-gate | https://github.com/hamidmatiny/aegis-agent-gate |
| aegis-audit | https://github.com/hamidmatiny/aegis-audit |

**Quick check:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api.github.com/repos/hamidmatiny/aegis-infra
# → 200
```

Org chart (this repo): [docs/org-chart.md](./org-chart.md)  
A2A protocols: [docs/a2a-routing.md](./a2a-routing.md)

## Held private

| Repo | Reason |
|------|--------|
| [aegis-scout](https://github.com/hamidmatiny/aegis-scout) | **gitleaks:** API key material was committed in `.env.bak-mid` (history). File removed from HEAD 2026-09-20; **key rotation + history scrub required before public.** Unauthenticated API still returns 404 by design. |

## Audit note (2026-09-20)

Full-history `gitleaks detect --log-opts=--all` on every Track B agent repo: **no leaks** except `aegis-scout` (2 findings, same key). Regex history scan on the eight primary playbook clones found no additional credential patterns.
