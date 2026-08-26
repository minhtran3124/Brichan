### Exact doctor `agent_skill_export` details

```text
SOURCE_CHECKOUT_NOT_APPLICABLE=skill export comparison is not applicable in source-checkout mode
OUTPUT_PATH_BYTE_LIMIT=an absolute skill path exceeds 4096 UTF-8 bytes
OUTPUT_PATH_NOT_CANONICAL=an absolute skill path is not strict UTF-8 NFC
MANAGED_STATE_UNINITIALIZED=managed state is not initialized
MANAGED_STATE_MALFORMED=managed state is malformed or unsafe
MANAGED_STATE_INCOMPATIBLE=managed state is incompatible with this package
UNSUPPORTED_SAFE_OPEN=required safe-open primitives are unavailable
RESOURCE_LIMIT=a process filesystem resource was exhausted
SAFE_OPEN_HELPER_BUSY=another bounded safe-open helper is active
SAFE_OPEN_HELPER_TIMEOUT=the bounded safe-open helper timed out
SAFE_OPEN_HELPER_FAILED=the bounded safe-open helper failed
SAFE_OPEN_HELPER_LEAK=the bounded safe-open helper could not be reaped
SKILL_ENTRY_NAME_BYTE_LIMIT=a skill entry name exceeds 255 or a path exceeds 1024 bytes
SKILL_ENTRY_NAME_INVALID=a skill entry name is not strict UTF-8 NFC
SKILL_ENTRY_LIMIT=skill file count exceeds 64
SKILL_DIRECTORY_LIMIT=skill directory count exceeds 64
SKILL_DEPTH_LIMIT=skill directory depth exceeds 6
MANAGED_SKILL_AGGREGATE_BYTE_LIMIT=managed skill bytes exceed 4194304
EXPORTED_SKILL_AGGREGATE_BYTE_LIMIT=exported skill bytes exceed 4194304
MANAGED_SKILL_BYTE_LIMIT=a managed skill file exceeds 262144 bytes
EXPORTED_SKILL_BYTE_LIMIT=an exported skill file exceeds 262144 bytes
SKILL_UNSAFE=a skill entry is not a safe regular file or directory
SKILL_UNREADABLE=a skill entry could not be read
EXPORT_EXTRA=the export contains paths absent from managed state
EXPORT_STALE=managed and exported skill bytes differ
EXPORT_MISSING=the export or an expected exported file is missing
EXPORT_CURRENT=managed and exported skill files are current
```
