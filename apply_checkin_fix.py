"""Wording pass: Urgent or Act soon on every alert, no "Disease Confirmed", and the source placeholder hidden from farmers.

Run from the Development folder (the one that contains backend and dashboard):
    python apply_checkin_fix.py

It changes nothing unless every edit fits. Run it again and it says "already applied" for what is done."""
import hashlib
import sys
from pathlib import Path

NEW_FILES = {}

EDITS = {'backend/app/routers/checkins.py': [('            record_sms(db, user_id=current_user.id, farm_id=farm.id, '
                                      'alert_id=new_alert.id, kind="photo_alert",',
                                      '            await db.flush()   # the alert row must exist before the SMS log '
                                      'row that points at it\n'
                                      '            record_sms(db, user_id=current_user.id, farm_id=farm.id, '
                                      'alert_id=new_alert.id, kind="photo_alert",')]}

DELETE_FILES = []


def read(path):
    raw = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def main():
    root = Path.cwd()
    if not (root / "backend" / "app" / "models" / "__init__.py").exists() or not (root / "dashboard" / "src").is_dir():
        sys.exit("Run this from the Development folder (it must contain backend and dashboard).")
    problems, plan, notes = [], [], []

    for rel, edits in EDITS.items():
        path = root / rel
        if not path.exists():
            problems.append(f"{rel}: file not found")
            continue
        text, crlf = read(path)
        changed = False
        for number, edit in enumerate(edits, 1):
            if edit[0] == "@append":
                _, marker, tail = edit
                if marker in text:
                    notes.append(f"{rel} edit {number}: already applied")
                else:
                    text = text.rstrip("\n") + "\n" + tail
                    changed = True
                continue
            if edit[0] == "@to_eof":
                _, start, tail = edit
                if tail in text:
                    notes.append(f"{rel} edit {number}: already applied")
                elif text.count(start) == 1:
                    text = text[:text.index(start)] + tail
                    changed = True
                else:
                    problems.append(f"{rel} edit {number}: could not find `{start}` exactly once (found {text.count(start)})")
                continue
            old, new = edit
            if (new in text) if new else (old not in text):
                notes.append(f"{rel} edit {number}: already applied")
            elif text.count(old) == 1:
                text = text.replace(old, new)
                changed = True
            else:
                problems.append(f"{rel} edit {number}: expected text found {text.count(old)} times (needs exactly 1):\n"
                                + "\n".join("      | " + line for line in old.strip("\n").split("\n")[:4]))
        if changed:
            plan.append((path, text.replace("\n", "\r\n") if crlf else text, rel))

    for rel, content in NEW_FILES.items():
        path = root / rel
        if path.exists():
            if read(path)[0] == content:
                notes.append(f"{rel}: already there")
            else:
                problems.append(f"{rel}: exists and is different; not overwriting it")
        elif not path.parent.is_dir():
            problems.append(f"{rel}: folder {path.parent} not found")
        else:
            plan.append((path, content, rel))

    deletions = []
    for rel in DELETE_FILES:
        path = root / rel
        if path.exists():
            deletions.append((path, rel))
        else:
            notes.append(f"{rel}: already removed")

    if problems:
        print("Nothing was changed. These did not fit:\n")
        print("\n".join(" - " + p for p in problems))
        print("\nSend me the files named above (as they are now) and I will adjust.")
        sys.exit(1)
    for path, content, rel in plan:
        path.write_bytes(content.encode("utf-8"))
        print("wrote  ", rel)
    for path, rel in deletions:
        path.unlink()
        print("removed", rel)
    for note in notes:
        print("skipped", note)
    print(f"\nDone: {len(plan)} file(s) written, {len(deletions)} removed.")


if __name__ == "__main__":
    main()
