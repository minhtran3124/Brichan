import io, json, sys, tempfile, contextlib
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/src")
from brichan.orchestration import worker_launch, worker_ledger

def run(fn, argv):
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        try:
            code = fn(argv)
        except SystemExit as e:
            code = int(e.code or 0)
    return code, err.getvalue().strip()

LID = "00000000-0000-4000-8000-000000000001"
with tempfile.TemporaryDirectory() as t:
    root = Path(t)
    (root/".git").mkdir(); (root/".brichan/ledger").mkdir(parents=True)
    (root/".brichan/manifest.json").write_text("{}\n")
    led = root/".brichan/ledger/workers.jsonl"
    led.write_text(json.dumps({"event":"launched","launch_id":LID})+"\n")
    base = ["finish","--project",str(root),"--worker","brichan-w","--launch-id",LID,"--evidence","report.md"]
    print("finish ok:", run(worker_ledger.main, base))
    print("double finish:", run(worker_ledger.main, base))
    print("unmatched id:", run(worker_ledger.main, base[:5]+["--launch-id","00000000-0000-4000-8000-00000000dead","--evidence","x"]))
    print("bad prefix:", run(worker_ledger.main, ["finish","--project",str(root),"--worker","w","--launch-id",LID,"--evidence","x"]))
    print("empty evidence:", run(worker_ledger.main, ["finish","--project",str(root),"--worker","brichan-w2","--launch-id",LID,"--evidence","  "]))
    print("ledger-file on installed finish:", run(worker_ledger.main, base+["--ledger-file","x.jsonl"]))
with tempfile.TemporaryDirectory() as t2:
    print("non-git project:", run(worker_ledger.main, ["finish","--project",t2,"--worker","brichan-w","--launch-id",LID,"--evidence","x"]))
    print("no manifest:", end=" ")
    Path(t2,".git").mkdir()
    print(run(worker_ledger.main, ["finish","--project",t2,"--worker","brichan-w","--launch-id",LID,"--evidence","x"]))
    print("launch --ledger-file installed:", run(worker_launch.main, ["brichan-w","--cwd",t2,"--route","implement","--task","T-1","--ledger-file","x.jsonl","--dry-run"]))
