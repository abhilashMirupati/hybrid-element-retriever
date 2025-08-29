from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class VersionInfo:
    name: str
    version: str


def _get_version_info() -> VersionInfo:
    try:
        from importlib.metadata import version  # type: ignore
    except Exception:  # pragma: no cover - extremely narrow
        def version(_: str) -> str:  # type: ignore[no-redef]
            return "0.0.0"
    try:
        v = version("her")
    except Exception:
        v = "0.0.0"
    return VersionInfo(name="her", version=v)


def _print_json(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        _print_json({"ok": True, "command": "her", "message": "HER CLI available", "version": _get_version_info().version})
        return 0

    cmd = args[0]
    if cmd == "version":
        info = _get_version_info()
        _print_json({"ok": True, "name": info.name, "version": info.version})
        return 0

    if cmd == "cache":
        sub = args[1:] if len(args) > 1 else []
        if sub == ["--clear"]:
            _print_json({"ok": True, "cleared": False, "message": "Cache clear will be implemented in Phase 1+"})
            return 0
        _print_json({"ok": True, "command": "cache", "message": "No action specified"})
        return 0

    _print_json({"ok": False, "error": f"Unknown command: {cmd}"})
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
