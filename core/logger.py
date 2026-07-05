import logging
import os
import sys
from pathlib import Path

# Basisverzeichnis ermitteln (Poseidon-Hauptordner)
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


class _SafeStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if not isinstance(msg, str):
                msg = str(msg)
            term = self.terminator if isinstance(self.terminator, str) else self.terminator.decode("utf-8", "replace")
            clean = (msg + term).encode("utf-8", "replace").decode("utf-8", "replace")
            stream = self.stream or sys.stderr
            try:
                stream.write(clean)
                if hasattr(stream, "flush"):
                    stream.flush()
            except (UnicodeEncodeError, AttributeError):
                target = getattr(stream, "buffer", stream)
                if hasattr(target, "write"):
                    target.write(clean.encode("utf-8", "replace"))
                    if hasattr(target, "flush"):
                        target.flush()
        except Exception:
            try:
                self.handleError(record)
            except Exception:
                pass


class PoseidonLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PoseidonLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        self.logger = logging.getLogger("Poseidon")
        self.logger.setLevel(logging.DEBUG)
        self.audit = logging.getLogger("Poseidon.Audit")
        self.audit.setLevel(logging.INFO)

        fh = logging.FileHandler(LOG_DIR / "poseidon.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        ah = logging.FileHandler(LOG_DIR / "audit.log", encoding='utf-8')
        ah.setLevel(logging.INFO)
        sh = _SafeStreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        fh.setFormatter(formatter)
        ah.setFormatter(formatter)
        sh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)
        self.audit.addHandler(ah)
        self.audit.propagate = False
        self.logger.propagate = False

    def get_logger(self):
        return self.logger

    def get_audit_logger(self):
        return self.audit


# Globaler Logger für einfachen Import
logger = PoseidonLogger().get_logger()
audit_logger = PoseidonLogger().get_audit_logger()
