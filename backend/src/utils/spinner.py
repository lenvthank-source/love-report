import sys
from contextlib import contextmanager
from typing import Generator, Any

class DummySpinner:
    def ok(self, text):
        print(f" {text}")
    def fail(self, text):
        print(f" {text}")
    def write(self, text):
        print(text)

@contextmanager
def spinner_context(text: str, spinner_name: str = "line") -> Generator[Any, None, None]:
    """
    Context manager to display a spinner during long-running tasks.
    Avoids yaspin entirely on Windows/non-UTF-8 console environments to prevent UnicodeEncodeError.
    """
    is_utf8 = False
    if sys.stdout and sys.stdout.encoding:
        try:
            "✔".encode(sys.stdout.encoding)
            is_utf8 = True
        except Exception:
            pass

    if not is_utf8 or sys.platform.startswith("win"):
        # Fallback to plain printing instead of yaspin animation
        print(f"[INFO] {text}...", end="", flush=True)
        try:
            yield DummySpinner()
            print(" Done.")
        except Exception as e:
            print(" Failed.")
            raise e
    else:
        from yaspin import yaspin
        with yaspin(text=text, spinner=spinner_name) as sp:
            try:
                yield sp
                sp.ok("✔")
            except Exception as e:
                sp.fail("✘")
                raise e


