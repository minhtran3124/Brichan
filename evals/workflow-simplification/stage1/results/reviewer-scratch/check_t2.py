"""Differential + spec checks for T2: X vs Y semver_order."""
import os
import importlib.util
import itertools
import random

BASE = os.environ.get("WFS_REVIEW_DIR", "wfs-review")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


X = load("x_semver", f"{BASE}/X/t2-prerelease-order/semver_order.py")
Y = load("y_semver", f"{BASE}/Y/t2-prerelease-order/semver_order.py")


def call(mod, a, b):
    try:
        return mod.compare(a, b)
    except ValueError:
        return "ValueError"
    except Exception as exc:  # noqa: BLE001
        return f"RAISED {type(exc).__name__}"


# 1. Spec item 11 chain, strict ascending, checked pairwise on both.
CHAIN = [
    "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.1.1", "1.0.0-alpha.beta",
    "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1",
    "1.0.0-rc.1.a", "1.0.0-rc.2", "1.0.0-rc.10", "1.0.0", "1.0.1-0",
    "1.0.1--", "1.0.1-a", "1.0.1", "1.1.0-alpha", "1.1.0", "2.0.0",
]
bad = 0
for (i, a), (j, b) in itertools.product(enumerate(CHAIN), repeat=2):
    want = (i > j) - (i < j)
    for tag, mod in (("X", X), ("Y", Y)):
        got = call(mod, a, b)
        if got != want:
            bad += 1
            print(f"SPEC FAIL {tag}: compare({a!r}, {b!r}) = {got}, want {want}")
print(f"spec chain: {'OK' if not bad else f'{bad} failures'} over {len(CHAIN)**2} pairs x2")

# 2. Random fuzz: generated valid-ish and invalid strings, X vs Y must agree.
random.seed(42)
ALPH = "0123456789.-+aAzZ \n\t١"
diffs = 0
for _ in range(200000):
    s = "".join(random.choice(ALPH) for _ in range(random.randint(0, 12)))
    t = "".join(random.choice(ALPH) for _ in range(random.randint(0, 12)))
    rx, ry = call(X, s, t), call(Y, s, t)
    if rx != ry:
        diffs += 1
        if diffs <= 10:
            print(f"DIFF: compare({s!r}, {t!r}): X={rx} Y={ry}")
print(f"random fuzz: {diffs} disagreements")

# 3. Structured fuzz over valid versions: agreement + antisymmetry + sanity.
def rand_version(r):
    core = f"{r.randint(0, 3)}.{r.randint(0, 3)}.{r.randint(0, 3)}"
    parts = []
    for _ in range(r.randint(0, 3)):
        kind = r.random()
        if kind < 0.5:
            parts.append(str(r.choice([0, 1, 2, 9, 10, 11, 99])))
        else:
            parts.append(r.choice(["alpha", "beta", "rc", "a", "A", "a-1", "-", "0a"]))
    v = core + ("-" + ".".join(parts) if parts else "")
    if r.random() < 0.3:
        v += "+" + r.choice(["build", "b.1", "001"])
    return v


r = random.Random(7)
problems = 0
for _ in range(100000):
    a, b = rand_version(r), rand_version(r)
    rx, ry = call(X, a, b), call(Y, a, b)
    if rx != ry:
        problems += 1
        print(f"DIFF valid: compare({a!r}, {b!r}): X={rx} Y={ry}")
        continue
    if isinstance(rx, int):
        if call(X, b, a) != -rx:
            problems += 1
            print(f"X antisymmetry fail: {a!r} {b!r}")
        if call(Y, b, a) != -ry:
            problems += 1
            print(f"Y antisymmetry fail: {a!r} {b!r}")
print(f"structured fuzz: {problems} problems")

# 4. Targeted edges.
edges = [
    ("1.0.0\n", "1.0.0"), ("1١.0.0", "1.0.0"), ("1.0.0-١1", "1.0.0"),
    ("1.0.0-01", "1.0.0"), ("01.0.0", "1.0.0"), ("1.0.0+", "1.0.0"),
    ("1.0.0-", "1.0.0"), ("1.0.0-rc..1", "1.0.0"), ("v1.0.0", "1.0.0"),
    (" 1.0.0", "1.0.0"), ("1.0.0 ", "1.0.0"), ("1.0.0+b\n", "1.0.0"),
    ("1.0.0-99999999999999999999", "1.0.0-100000000000000000000"),
    ("1.0.0-1", "1.0.0--"), ("1.0.0+a.b", "1.0.0+c"), ("1.0.0-0.3.7", "1.0.0-0.3.8"),
]
for a, b in edges:
    rx, ry = call(X, a, b), call(Y, a, b)
    mark = "SAME" if rx == ry else "DIFF"
    print(f"[{mark}] compare({a!r}, {b!r}): X={rx} Y={ry}")

# 5. sort_versions stability on equal-precedence inputs.
vs = ["1.0.0+z", "1.0.0+a", "1.0.0", "1.0.0+m"]
print("X sort stable:", X.sort_versions(vs) == vs, "Y sort stable:", Y.sort_versions(vs) == vs)
