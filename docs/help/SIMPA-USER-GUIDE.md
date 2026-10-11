# SIMPA User Guide - Help, Methodology and XAI

Status: ISI-23D CANONICAL USER GUIDE

## 1. Purpose and safety boundary

SIMPA is institutional decision support for aggregate/local-system monitoring. It is not a citizen-level eligibility, benefit, diagnosis, fraud, punitive-risk or automated policy decision engine. Ordinary statistical association is not causality. No screen in this guide authorizes an unapproved LISI formula, weight, threshold, risk band or policy conclusion.

The canonical presentation order is: governed evidence -> indicators/analytics -> deterministic model outputs -> bounded AI interpretation -> human review.

## 2. Access, organization, product and workspace

Use an institutional account and select the authorized organization, SIMPA product entitlement and workspace. Backend RBAC is the authority; UI visibility is not authorization. Typical permissions include `indicator.read`, `indicator.manage`, `analysis.read`, `analysis.run` and `workspace.manage`.

If a module/action is unavailable, verify the selected workspace and permissions or ask the organization administrator. Never bypass API authorization.

## 3. Local-system profile, actors and monitoring cycles

The SIMPA overview records the local-system profile, local actors and monitoring cycles. Profile/actor changes in the current UI require `workspace.manage`; creation of a monitoring cycle requires `indicator.manage`.

Monitoring-cycle states are `planned`, `open` and `closed`. They are workflow states, not an evaluation of policy success. The end date cannot precede the start date.

## 4. Indicator registry and observations

The indicator registry shows conceptual/current indicators, domain/dimension, unit hint and methodology status. A label or name never implies an approved formula. `missing`, absent, not collected and numerical zero are not interchangeable. The system intentionally does not fabricate observations when no governed source exists.

## 5. Governed analytical input

SIMPA analytics accepts only eligible governed analytical artifacts. A snapshot must be VALIDATED/FROZEN and not invalidated. An eligible feature version must be GOVERNED/FROZEN, not invalidated and derived from exactly one eligible snapshot in the current contract.

Always inspect artifact/dataset fingerprints and evidence-quality state before model execution. Artifact eligibility is not the same as methodology validation.

## 6. Methodology lifecycle

`DRAFT -> PROPOSED -> VALIDATED -> RETIRED`

- DRAFT: authoring/testing; not institutionally validated.
- PROPOSED: controlled testing only.
- VALIDATED: human methodology approval after the required deterministic reference evidence gate.
- RETIRED: historical/reproducible; not eligible for new production calculation.

A reference-suite `PASS` proves only that the versioned deterministic reference cases reproduce their expected results. PASS does not itself produce VALIDATED status. Human approval remains separate.

## 7. Monitoring snapshot

An authorized user with `analysis.run` can save the current evidence-quality view as an immutable monitoring snapshot. Evidence-quality score/band, validated-observation ratio, provenance coverage and indicator coverage describe evidence readiness/coverage only. They are not citizen risk or service-outcome scores.

## 8. Statistical methodology contract

Each statistical contract is immutable/versioned and is bound to the exact current VALIDATED target-indicator methodology fingerprint. Model family is selected by target semantics:

| Target semantic | v1 model family | Interpretation scale |
| --- | --- | --- |
| continuous | OLS | target units per feature unit, conditional on included features |
| count | Poisson GLM | log expected-count scale |
| binary_system_state | Binomial/Logit | aggregate positive-state log-odds scale |
| proportion_rate | Fractional Logit | logit-link scale for conditional aggregate mean proportion/rate |

The v1 contract uses `complete_case`, no feature scaling, an intercept, aggregate-only data and explicit non-causal semantics. It does not define prediction thresholds/classes, LISI semantics, citizen scoring or champion/promotion governance.

## 9. Running a deterministic statistical model

Requires `analysis.run`. Select an executable statistical contract and a governed monitoring run. PROPOSED execution additionally requires explicit controlled-testing acknowledgement. VALIDATED execution does not require that checkbox.

A result is immutable for the same analytics run + statistical contract. `production_eligible=true` means the executed contract was VALIDATED at execution. It does not mean the model is an ISI-25 champion or that performance/policy use is automatically approved.

Common fail-closed states include non-estimable target, insufficient residual degrees of freedom, rank-deficient design, invalid count/binary/proportion target, perfect separation, non-convergence and numerical failure. Correct the governed input or methodology; do not convert missing values to zero or weaken validation.

## 10. Coefficients, standard errors, confidence intervals and p-values

Every newly generated v1 result exposes, for each term, model estimate, standard error, confidence interval and the p-value produced by statsmodels under the stored covariance/model specification.

P-value interpretation is deliberately narrow: it is model-based association inference conditional on the current specification. It is not practical significance, policy significance, causality or a generic confidence score. The current v1 contract does not encode a multiplicity adjustment. Do not invent a significance threshold that is not part of an approved methodology.

Historical immutable results created before ISI-23D may not contain a p-value. They remain unchanged and the UI reports `unavailable_legacy_result`; it must not reconstruct or silently backfill a p-value.

## 11. Family-specific interpretation

### OLS

A coefficient is an aggregate conditional association in target units for a one-unit feature increase while the other included features remain fixed. R-squared/adjusted R-squared, RMSE and MAE summarize fit/error. Calibration is stored as `not_applicable` for the current OLS contract.

### Poisson GLM

A coefficient is on the log expected-count scale. The raw coefficient is not a direct count difference. Deviance, Pearson chi-square, dispersion, log-likelihood and AIC are supported summaries. The v1 contract defines no universal diagnostic pass/fail threshold and does not automatically switch to Negative Binomial.

### Binomial/Logit

A coefficient is on the aggregate system-state log-odds scale relative to the contract-defined positive outcome. It is not a citizen probability, percentage-point effect or decision threshold. The stored Brier score and mean observed/predicted values are aggregate probability-error summaries; they are not proof of calibrated confidence or permission to create a class threshold.

### Fractional Logit

A coefficient is on the logit-link scale for the conditional mean of an aggregate proportion/rate. It is not a direct percentage-point effect. Squared probability error and mean observed/predicted summarize aggregate rate/proportion error; they do not certify a generic confidence score.

## 12. Diagnostics, uncertainty and calibration

The UI shows only diagnostics produced by the engine. No universal condition-number, dispersion, deviance, AIC or other pass/fail threshold is invented by Help/XAI. Interpret raw diagnostics in the approved methodology context and with human review.

Calibration can be `not_applicable`. For current binary/fractional results, the implemented error summaries are displayed with their exact semantics; the product must not call them proof that a model is calibrated for an institutional decision.

## 13. Complete-case missing/dropped records

For statistical v1, a candidate record is dropped when the target or any required model feature is missing/blank. Numerical zero is preserved as a valid number. The result shows selected count, used sample size and dropped-missing count so the user can see the impact of complete-case handling.

## 14. Reproducibility and provenance

A statistical result carries exact identifiers/fingerprints where available for the statistical contract, target methodology, analytical artifact, dataset contract, input content and result, plus engine schema and statsmodels version. These fields are evidence for reproduction/review and must not be hidden by a generated narrative.

## 15. Explicit unsupported XAI states

The current deterministic regression layer does not provide a generic confidence score, classical-regression feature importance, prediction threshold, automatic policy recommendation or causal effect. These states are displayed as unavailable rather than fabricated.

## 16. Local AI synthesis and human review

The current SIMPA AI synthesis consumes the bounded evidence-quality monitoring snapshot, not the statistical result. It uses the shared AI gateway and for sensitive SIMPA requests is forced to local-only policy. The UI exposes source snapshot hash, provider/model, effective policy, prompt key/version, job/failure/structured-output state and human-review state.

The AI output is not numerical authority or an institutional conclusion. It must not fabricate coefficients, probabilities, scores, thresholds, forecasts or sources. The reviewer explicitly accepts or rejects the output. Shared model champion/challenger, eval-set, fallback/promotion and broader AI XAI contracts remain ISI-25 scope.

## 17. Privacy and security

Use only data permitted for the active organization/product/workspace. Sensitive SIMPA context must follow the local-only AI policy. Do not copy institutional data into another tenant/product namespace. Help examples are intentionally non-sensitive.

## 18. Quick recovery guide

- No SIMPA workspace: select/configure an authorized workspace.
- No eligible analytical artifact: return to governed data flow and validate/freeze the artifact.
- PROPOSED model cannot run: provide explicit controlled-testing acknowledgement.
- Statistical model not estimable: fix governed input/model specification; do not zero-fill missing data.
- Legacy result has no p-value: accept the explicit unavailable state; do not backfill.
- AI provider/queue/structured output failure: keep the failure explicit and follow approved retry/review policy.
- Missing permission: request the required role/permission; do not bypass backend authorization.

## 19. Human accountability

SIMPA is decision support. Methodology validation, interpretation of statistical evidence, policy meaning and institutional decisions remain human responsibilities. No Help/XAI wording changes that boundary.


## 29A Graphical XAI — pregled grafikona sačuvanih rezultata

**Šta/kada:** grafikon pomaže u pregledu postojeće tabele rezultata; nije novo modeliranje. Otvorite Analitika → sačuvani rezultat. **Prava:** ista analysis.read prava i organization/product/workspace scope kao za rezultat.

**Koraci:** pročitajte model/skaliranje i legendu, pregledajte grafikon, uporedite sa izvornom tabelom, proverite fingerprint i metodološka ograničenja, zatim obavite human review.

**Polja/stanja:** numerička nula ostaje zero; missing interval je unavailable. Nepodržani schema/model, neispravni brojevi ili intervali daju poruku umesto izmišljenog grafikona. NOT_ESTIMATED nema nultu prognozu. SHAP prikaz je dostupan za podržani numerički model u zasebnom detaljnom uputstvu; ne objašnjava istinitost LLM teksta.

**Primer:** coefficient estimate=0 je validna tačka; missing CI nije zero-width interval. **Non-goals:** grafikoni nisu uzročni efekti, policy zaključci ili AI confidence score. Nema novih residual/calibration tačaka kada nisu sačuvane.

**Errors / safe recovery:** koristite tabelu/JSON ako grafikon nije dostupan; proverite verziju/format dokaza kroz postojeći workflow. Ne menjajte stari rezultat da biste dobili grafikon.

**Limits:** najviše 24 koeficijenta, 60 tačaka i 40 selectable origins; svaki ograničen prikaz je označen, postojeće pune tabele/JSON ostaju dostupne. Oznake se skraćuju u grafikonu; puni termini su u tabeli. Chart SVG je responsive; tabelarni fallback ostaje pristupačan tastaturom.

**Provenance/review:** prikaz ne refituje model, ne čita nove izvore i ne menja evidence. Methodology/model/input/result identitet i human review ostaju autoritet.

Koeficijenti i sačuvani CI prikazuju se na postojećoj family/link skali: OLS u target units, Poisson na log-count, logit/fractional na logit skali. Tačke nisu direktni procentni ili kauzalni efekti.
