from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Dict

from .cli_api import HybridClient


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


def _print(obj: Dict[str, Any]) -> int:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return _print({"ok": True, "command": "her", "message": "HER CLI available", "version": _get_version_info().version})

    cmd = args[0]
    if cmd == "version":
        info = _get_version_info()
        return _print({"ok": True, "name": info.name, "version": info.version})

    if cmd == "cache":
        sub = args[1:] if len(args) > 1 else []
        if sub == ["--clear"]:
            # Clearing: create a new client and attempt to clear known cache path by writing empty marker
            hc = HybridClient(enable_pipeline=False)
            try:
                stats = getattr(hc.session_manager.create_session('cli', None), 'stats')()
            except Exception:
                stats = {}
            return _print({"ok": True, "cleared": False, "stats": stats})
        return _print({"ok": True, "command": "cache", "message": "No action specified"})

    if cmd in ("query", "act"):
        if len(args) < 2:
            return _print({"ok": False, "error": f"{cmd} requires an argument"})
        text = args[1]
        url = None
        if '--url' in args:
            try:
                url = args[args.index('--url') + 1]
            except Exception:
                url = None
        hc = HybridClient()
        if cmd == 'query':
            res = hc.query(text, url=url)
            # Normalize to contract if legacy flow returned different keys
            if isinstance(res, dict) and 'selector' in res and 'element' in res:
                out = {
                    'element': res.get('element'),
                    'xpath': res.get('selector'),
                    'confidence': float(res.get('score', 0.0)),
                    'strategy': 'semantic',
                    'metadata': {'frame_path': '', 'used_frame_id': '', 'url': url or '', 'no_candidate': False},
                }
                return _print(out)
            return _print(res if isinstance(res, dict) else {'ok': True, 'result': res})
        else:
            res = hc.act(text, url=url)
            return _print(res if isinstance(res, dict) else {'ok': True, 'result': res})

    return _print({"ok": False, "error": f"Unknown command: {cmd}"})


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
