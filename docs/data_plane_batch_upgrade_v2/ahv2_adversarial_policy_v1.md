# AHV2 Adversarial Policy v1

## Required Query Families

- A canonical guard: every new AHV2 safe primary object must have at least one canonical query.
- Similar concept false trigger: related or same-character concepts must not hit the wrong AHV2 object.
- Disabled alias recheck: inactive risky/ambiguous aliases must not produce AHV2 normalization or primary.
- Partial word / single-character tests: partial terms must not trigger AHV2 primary.
- Non-definition intent: treatment, formula, mechanism, and comparison questions must not be hijacked by AHV2 definition primary.
- Negative samples: modern or ordinary words must not hit AHV2 primary.
- Guard blocks: formula, gold-safe definition, AHV v1, and review-only boundary queries must not regress.
