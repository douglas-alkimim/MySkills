# Example: Synchronized Revision

Plan 8d68b12d-cc56-4d71-91c8-411a98f8ca4b version 2 changes W002 acceptance from “API returns a file” to “API returns a streamed file under the 500 MB memory budget.”

Required actions:

1. Preserve plan ID and created_at.
2. Increment version to 3 and update updated_at.
3. Update R004, the performance contract, I006 scope and criteria, W002 criteria, verification strategy, final acceptance, and revision history.
4. Rename the package with a new local timestamp.
5. Regenerate wave-02.md because its objective, contract, and criterion changed.
6. Regenerate later prompts that consume W002 outputs or repeat the performance contract.
7. Regenerate execute-all.md if wave structure or references changed.
8. Validate source hashes, versions, predecessor gates, paths, and semantics.
9. Update the indexed path/version/hash and record a revision event.

Keeping the old wave-02 prompt would be a failed revision even if README.md were correct. The content hash makes that staleness mechanically visible.
