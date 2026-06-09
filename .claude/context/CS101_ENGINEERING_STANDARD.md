# Computer Science 101 Engineering Standard

Every application created under AI Workflow OS should prefer simple, decoupled, testable architecture.

## Design fundamentals

- Separate presentation, business logic, data access, providers, configuration, and deployment.
- Keep side effects at boundaries.
- Keep pure functions pure.
- Make state explicit.
- Make failure states visible.
- Do not hide errors behind fake success.
- Prefer small files with clear ownership.
- Prefer dependency injection over global hidden state.
- Prefer registry patterns for providers and plugins.
- Prefer contracts between frontend and backend.

## Standard app layers

- UI layer
- API route layer
- service/orchestration layer
- provider adapter layer
- repository/storage layer
- validation/schema layer
- security/auth layer
- observability/proof layer
- deployment layer

## Standard proof

- compile or typecheck
- unit tests if present
- safe route proof
- UI contract proof where possible
- diff check
- no secret scan
- final proof report
