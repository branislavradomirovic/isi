# ISI-14 Security QA Matrix

| Area | Expected |
|---|---|
| Health/public HTTP | security headers + X-Request-ID |
| Auth responses | Cache-Control no-store |
| Trusted host | localhost / 127.0.0.1 accepted in development |
| Login abuse | 5 invalid attempts -> normal 401; next attempt -> 429 + Retry-After |
| Valid demo login | continues to work |
| Session storage | new session has IP/UA hashes and no new raw IP/UA values |
| Session lifecycle | idle timeout revokes with explicit reason |
| Production config | missing pepper / HTTP URLs / wildcard hosts / null delivery fail closed |
| Browser | login, SIMPA, ORDO, administration and reporting remain usable |
| Isolation | existing tenant/product regression suite remains green |
