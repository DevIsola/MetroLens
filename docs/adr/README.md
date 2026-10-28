# Architecture Decision Record index

ADRs document decisions and their **scope**. An accepted planning ADR is not permission to publish official source data, deploy, or activate scheduled processing.

| ADR | Decision | Scope and status |
| --- | --- | --- |
| [ADR-0001](ADR-0001-static-release-control.md) | Static pipeline and controlled release | Accepted **for planning**; production inactive |
| [ADR-0002](ADR-0002-unjoined-indicators.md) | Separate rent and income series | Accepted; no joined affordability ratio |
| [ADR-0003](ADR-0003-naming-and-identity.md) | UrbanGauge research repository identity | Accepted for repository, not commercial brand clearance |
| [ADR-0004](ADR-0004-manual-verification-and-docs-as-code.md) | Manual verification and documentation contract | Accepted for M01 implementation; no automatic triggers |

Create future ADRs with a unique next sequence number, context, decision, alternatives, consequences and evidence. Update this index and `CHANGELOG.md` in the same pull request. Do not replace historical ADR references during an identity rename.
