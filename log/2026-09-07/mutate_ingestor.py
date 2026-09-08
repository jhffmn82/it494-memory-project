"""Re-introduce each defect and confirm the battery goes red. A check that cannot fail is worse
than no check, so every one of these must produce a FAIL naming the right thing."""
import shutil
import subprocess
import sys
from pathlib import Path

NB = Path("notebooks/factledger-ingestor.py")
BACKUP = Path("C:/Users/jhffm/AppData/Local/Temp/claude/nb_backup.py")
shutil.copy(NB, BACKUP)
first = subprocess.run([sys.executable, "log/2026-09-06/test_ingestor.py"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
assert "FAIL" not in first.stdout, "baseline is not green; refusing to mutate from it"
print("baseline:", first.stdout.strip().splitlines()[-1])

MUTATIONS = {
    "P6  a dumped fact is written anyway (the audit's mutation)": [(
        '''                               "quote": f["quote"], "why": "the passage does not state it and it could not be corrected"})
                continue''',
        '''                               "quote": f["quote"], "why": "the passage does not state it and it could not be corrected"})''')],
    "P1a a correction may move the subject": [(
        '''    if norm(subject) != norm(f["subject"]):''',
        '''    if False and norm(subject) != norm(f["subject"]):''')],
    "P1b a correction pre-empts the direction branch": [(
        '''            if direction == "forward":
                obj, is_node = (fix["object"], False) if fix else (object_node or f["object"], object_node is not None)
            elif direction == "inverse":
                obj, is_node = f["subject"], False''',
        '''            if fix is not None:
                obj, is_node = fix["object"], False
            elif direction == "forward":
                obj, is_node = object_node or f["object"], object_node is not None
            elif direction == "inverse":
                obj, is_node = f["subject"], False''')],
    "P3  the triage row must be first (B4's regression)": [(
        '''    head = next((row for row in rows if "triage" in row), None)''',
        '''    head = rows[0] if rows and "triage" in rows[0] else None''')],
    "P2  an adjudicated item may cite a dumped fact": [(
        '''            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if not sources:                              # every fact it rested on was dumped (P2)''',
        '''            sources = list(item["from_facts"])
            if not sources:                              # every fact it rested on was dumped (P2)''')],
    "P2  a contradiction may hold a dumped fact": [(
        '''            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if len(sources) < 2:''',
        '''            sources = list(item["from_facts"])
            if len(sources) < 2:''')],
}

worst = 0
try:
  for name, edits in MUTATIONS.items():
      text = BACKUP.read_text(encoding="utf-8")
      for old, new in edits:
          if text.count(old) != 1:
              print(f"SKIP  {name}: anchor not unique ({text.count(old)})")
              worst = 1
              break
          text = text.replace(old, new)
      else:
          NB.write_text(text, encoding="utf-8", newline=chr(10))
          run = subprocess.run([sys.executable, "log/2026-09-06/test_ingestor.py"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
          fails = [l for l in run.stdout.splitlines() if l.startswith("FAIL")]
          if fails:
              print(f"CAUGHT  {name}")
              for f in fails[:3]:
                  print(f"          {f[6:96]}")
          else:
              print(f"MISSED  {name}  <-- the battery stayed green")
              worst = 1

finally:
  shutil.copy(BACKUP, NB)          # a crash must never leave a mutation on disk
run = subprocess.run([sys.executable, "log/2026-09-06/test_ingestor.py"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("\nrestored:", run.stdout.strip().splitlines()[-1])
sys.exit(worst)
