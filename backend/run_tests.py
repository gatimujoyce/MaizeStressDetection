import io
import contextlib
import pytest
import sys

def main():
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        pytest.main(["tests/"])
    with open("pytest_out_direct.txt", "w", encoding="utf-8") as out:
        out.write(f.getvalue())

if __name__ == "__main__":
    main()
