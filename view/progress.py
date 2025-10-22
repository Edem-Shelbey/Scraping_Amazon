# view/progress.py
# Context manager simple pour la progress bar.
# Utilise tqdm si présent, sinon fallback console.

from contextlib import contextmanager

try:
    from tqdm import tqdm as _tqdm
except Exception:
    _tqdm = None

@contextmanager
def get_progress(total=0, desc="", unit="it", ncols=80):
    """Usage:
       with get_progress(total=10, desc='x') as p:
           p.update(1)
    """
    if _tqdm:
        p = _tqdm(total=total, desc=desc, unit=unit, ncols=ncols)
        try:
            yield p
        finally:
            p.close()
    else:
        # fallback minimal
        class Dummy:
            def __init__(self, total, desc):
                self.total = total
                self.count = 0
                self.desc = desc
            def update(self, n=1):
                self.count += n
                print(f"{self.desc} {self.count}/{self.total}")
            def set_description(self, s): pass
            def close(self): pass
        d = Dummy(total, desc)
        try:
            yield d
        finally:
            pass
