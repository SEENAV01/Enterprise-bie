# BIE-RE-TEMP-052 — Temporal Package Inventory Audit

Classification: MUST-HAVE INTEGRATION HARDENING.

This task exists because the Temporal section audit found a canonical integration blocker: post-TEMP-003 atomic ZIPs package modules under app/bie/reasoning while the canonical repository imports bie/reasoning, and some tests are pytest-function-only while the enterprise runner is unittest-based.

Status: IMPLEMENTED after local unit tests pass. NOT ACCEPTED until the integration session applies the migration/rewrite contract and the canonical enterprise regression passes with zero import errors.
