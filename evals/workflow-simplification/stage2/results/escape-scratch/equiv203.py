import sys
sys.path.insert(0, sys.argv[1] + "/src")
from brichan.techstacks import model
rows = []
for spec in model.DIAGNOSTIC_REGISTRY:
    c = spec.code
    if c == "FILESYSTEM_ERROR":
        for e in (None, 0, 2, 13, 24):
            rows.append((c, e, model.diagnostic_detail(c, errno_value=e)))
    elif c == "INVALID_LEAF":
        for line in (0, 1, 33):
            for rule in ("TITLE", "LINE_SHAPE"):
                rows.append((c, line, rule, model.diagnostic_detail(c, line=line, rule=rule)))
    else:
        rows.append((c, model.diagnostic_detail(c)))
        assert rows[-1][-1] == spec.detail
for r in rows:
    print(repr(r))
