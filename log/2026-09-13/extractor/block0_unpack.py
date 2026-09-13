# %%
# Block 0: LongMemEval, unpacked into chat histories.
#
# LongMemEval ships as one file of 500 questions. Each question carries its own history: a list
# of chat sessions, each dated in that history. A real chat archive is a folder of conversations
# whose turns carry timestamps, so this block writes LongMemEval in that shape and the extractor
# reads it like any other chat:
#   chats/longmemeval/<question_id>/<session_id>.json   {"session_id", "turns": [{"role", "content", "timestamp"}]}
# Every turn carries its history's date for the session, as ISO ("2023/05/20 (Sat) 02:38" becomes
# "2023-05-20T02:38"). A session used by several histories is written once in each, with each
# history's date. A history that lists one session twice (15 do, each on two dates) gets a second
# file, <session_id>.2.json, with the second date. Empty sessions are written too; the extractor
# decides what to skip. Nothing from the test itself is written: no question, answer, answer
# sessions, type, question date or has_answer.
import hashlib
import json
from pathlib import Path

LME_CANDIDATES = (Path("/kaggle/input/it494-narrative-corpora-raw/longmemeval"),
                  Path("/kaggle/input/datasets/jhffmn/it494-narrative-corpora-raw/longmemeval"))
CHATS = Path("/kaggle/temp/chats")        # not /kaggle/working: 25,112 files there make the notebook's output too big to list or download


def iso_minute(stamp):
    """'2023/05/20 (Sat) 02:38' -> '2023-05-20T02:38'."""
    day, weekday, clock = stamp.split(" ")
    return f"{day.replace('/', '-')}T{clock}"


LME = next(folder for folder in LME_CANDIDATES if folder.is_dir())
data = (LME / "longmemeval_s.json").read_bytes()
expected = json.loads((LME / "manifest.json").read_text(encoding="utf-8"))["unpacked_from"]["sha256"]
if hashlib.sha256(data).hexdigest() != expected:
    raise SystemExit("longmemeval_s.json is not the file the manifest was built from")

written, with_content = 0, 0
for question in json.loads(data):
    folder = CHATS / "longmemeval" / question["question_id"]
    folder.mkdir(parents=True, exist_ok=True)
    listed = {}                                   # session id -> how many times this history has listed it
    for session_id, stamp, turns in zip(question["haystack_session_ids"], question["haystack_dates"], question["haystack_sessions"]):
        listed[session_id] = listed.get(session_id, 0) + 1
        name = session_id if listed[session_id] == 1 else f"{session_id}.{listed[session_id]}"
        when = iso_minute(stamp)
        chat = {"session_id": session_id,
                "turns": [{"role": turn["role"], "content": turn["content"], "timestamp": when} for turn in turns]}
        (folder / f"{name}.json").write_text(json.dumps(chat, ensure_ascii=False), encoding="utf-8")
        written += 1
        with_content += bool(turns)
print(f"LongMemEval unpacked: {len(list((CHATS / 'longmemeval').iterdir()))} histories, {written:,} session files,"
      f" {with_content:,} with turns, {written - with_content:,} empty")
