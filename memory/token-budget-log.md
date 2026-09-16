# Token budget log

Append-only. Source: OmniRoute `~/.omniroute/storage.sqlite` `call_logs` unless noted. Never invent remaining balances.

## Investigation baseline — 2026-09-15

### Provider visibility

| Provider | Monthly balance API? | Best real signal |
|----------|----------------------|------------------|
| Gemini (free API key, OmniRoute connection `gemini`) | No — rate limits only | `call_logs`; RPD/RPM proxies; 429 count |
| Cloudflare Playground (DeepSeek Pro, gpt-oss-120b) | No balance in OmniRoute | `call_logs` usage only |
| Claude Pro (subscription) | N/A flat sub | Trinity execution volume |

OmniRoute tables `provider_quota_state`, `api_key_token_limits`, `api_key_token_counters`, `daily_usage_summary`: **empty / unused** on this host. Admin HTTP quota routes require a management token distinct from the runtime API key (`Invalid management token` with chat key).

### Today (2026-09-15 UTC) — real call_logs

- Total calls: 1389 · tokens_in ≈ 28.9M · tokens_out ≈ 156k · **429s: 232**
- Shared key name on errors: `aegis-infra-runtime` (1214 calls, all 232 of today's 429s)
- Gemini `gemini-flash-lite-latest`: 386 calls, 110 errors (incl. 93×429 on flash-lite family aggregate)
- Gemini `gemini-3.7-flash`: 61 calls, 59 errors (near-exhausted)
- CFP DeepSeek: 57 calls · CFP gpt-oss: 36 calls (high error rates; no remaining-balance field)

### Horizon interpretation (honest)

- **Remaining today (Gemini Flash-Lite proxy):** community ceiling ≈ 500 RPD − today's flash-lite request volume. Given sustained 429s, treat Flash / 3.7-flash as **exhausted for practical purposes today**, not a fabricated leftover.
- **Remaining this week / month:** **not queryable** for any fleet provider — no weekly/monthly balance API. Show rolling consumption only.

Proxy ceilings used when needed (label as proxy, not project-certified): Flash ≈ 20 RPD / 5 RPM; Flash-Lite ≈ 500 RPD / 15 RPM (community measurement 2026-09-02; Google: check AI Studio).
