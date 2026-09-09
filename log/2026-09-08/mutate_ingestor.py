"""Re-introduce known defects into the refactor and require its battery to go red."""
import shutil
import subprocess
import sys
from pathlib import Path

NB = Path("notebooks/factledger-ingestor.py")
BACKUP = Path("C:/Users/jhffm/AppData/Local/Temp/claude/nb09_backup.py")
BATTERY = "log/2026-09-08/test_ingestor.py"
shutil.copy(NB, BACKUP)


def run():
    r = subprocess.run([sys.executable, BATTERY], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return [l for l in (r.stdout or "").splitlines() if l.startswith("FAIL")], (r.stdout or "")


base_fails, out = run()
assert not base_fails, "baseline is not green"
print("baseline:", out.strip().splitlines()[-1])

MUTATIONS = {
    "a dumped fact is written anyway": (
        '''                               "why": "the passage does not state it and it could not be corrected"})
                continue''',
        '''                               "why": "the passage does not state it and it could not be corrected"})'''),
    "a refused second check drops the facts anyway": (
        '''        if not refused:
            for fid in failed:
                corrections.pop(fid, None)''',
        '''        if True:
            for fid in failed:
                corrections.pop(fid, None)'''),
    "carrying a proper name promotes an entity to major": (
        '''"major": any(l["major"] for l in members),''',
        '''"major": any(l["major"] or l["named"] for l in members),'''),
    "a version bump invalidates every package again": (
        '''    if not rows or rows[-1].get("record") != "completion":''',
        '''    if not rows or rows[-1].get("record") != "completion" or rows[-1].get("ingestor") != INGESTOR:'''),
    "decision 52 stops demoting an entity with nothing to summarise": (
        '''        if e["major"] and not e["children"]:      # nothing to summarise: not a major (decision 52)
            e["major"] = False''',
        '''        if False and e["major"] and not e["children"]:
            e["major"] = False'''),
    "the pair score drops profile without renormalising": (
        '''    return name, cooc, 0.7 * name + 0.3 * cooc''',
        '''    return name, cooc, 0.6 * name + 0.25 * cooc'''),
    "the profile record comes back": (
        '''        if r["summary"]:
            lines.append({"record": "cell", "node_id": doc_node,''',
        '''        lines.append({"record": "profile", "node_id": doc_node, "attribute": "animacy", "value": "animate"})
        if r["summary"]:
            lines.append({"record": "cell", "node_id": doc_node,'''),
    "a correction is written without being checked": (
        '''        failed, refused, more = unsupported_of(checked, ctx, stage="verify")''',
        '''        failed, refused, more = [], False, 0'''),
}

worst = 0
try:
    for name, (old, new) in MUTATIONS.items():
        text = BACKUP.read_text(encoding="utf-8")
        if text.count(old) != 1:
            print(f"SKIP    {name}: anchor matched {text.count(old)} times")
            worst = 1
            continue
        NB.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        fails, _ = run()
        if fails:
            print(f"CAUGHT  {name}")
            for f in fails[:2]:
                print(f"          {f[6:100]}")
        else:
            print(f"MISSED  {name}")
            worst = 1
finally:
    shutil.copy(BACKUP, NB)

_, out = run()
print("\nrestored:", out.strip().splitlines()[-1])
sys.exit(worst)
