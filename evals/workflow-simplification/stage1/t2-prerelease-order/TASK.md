# T2: fix release-candidate ordering (debugging)

Bug report from a user:

> `sort_versions(["1.0.0-rc.10", "1.0.0-rc.2", "1.0.0"])` returns
> `["1.0.0-rc.10", "1.0.0-rc.2", "1.0.0"]`. `rc.2` should come before
> `rc.10`.

`semver_order.py` implements Semantic Versioning 2.0.0 precedence
(https://semver.org/#spec-item-11). Find the root cause and fix it so that
`compare` and `sort_versions` follow SemVer 2.0.0 precedence in full, not only
for the reported example. Keep the public signatures and the existing
`ValueError` behavior for invalid input. Add regression tests.

Standard library only.
