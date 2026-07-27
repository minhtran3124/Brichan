# Transfer service intent

Implement `transfer` so that:

1. Only the owner of the source account can initiate a transfer.
2. Transfer amounts must be strictly positive.
3. Transfers that exceed the source balance must be rejected.
4. Audit records may contain account IDs and the amount, but never credentials
   or API tokens.
5. A successful transfer subtracts from the source and adds to the target.

Review the implementation for correctness and security. Do not modify it.
