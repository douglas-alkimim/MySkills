# Code Security Module

Model assets, actors, entry points, trust boundaries, privileges, and failure impact. Do not invent compliance requirements; record applicable ones from evidence or the user.

Plan applicable controls for:

- authentication lifecycle and session handling;
- authorization at every protected resource and operation;
- input validation, output encoding, and unsafe deserialization;
- secrets creation, storage, rotation, and redaction;
- encryption and key ownership;
- tenant and data isolation;
- dependency and supply-chain integrity;
- least privilege for runtime, CI, and operators;
- audit logging without sensitive leakage;
- abuse, rate, replay, and denial-of-service controls;
- secure defaults, migration, rollback, and incident visibility.

Security criteria must name the attack or invariant and its verification. “Secure” is not a criterion. Put destructive or production-affecting security tests behind explicit authorization and safe environments.
