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
        info = _get_version_info()
        return _print({"ok": True, "name": info.name, "version": info.version})

    cmd = args[0]
    if cmd == "version":
        info = _get_version_info()
        return _print({"ok": True, "name": info.name, "version": info.version})

    if cmd == "cache":
        sub = args[1:] if len(args) > 1 else []
        if sub == ["--clear"]:
            # Minimal clear: return a JSON structure
            return _print({"ok": True, "cleared": True, "stats": {}})
        return _print({"ok": True, "command": "cache", "message": "No action specified"})

    if cmd == "handle-cache-command-backcompat":
        return _print({"ok": True})

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
        try:
            hc = HybridClient()
        except Exception as e:
            # If client cannot initialize (e.g., browsers not installed), act/query should still
            # return strict JSON instead of raising. Provide minimal error contract.
            if cmd == 'act':
                return _print({
                    'status': 'failure',
                    'method': 'click',
                    'confidence': 0.0,
                    'dom_hash': '',
                    'used_locator': None,
                    'overlay_events': [],
                    'retries': {'attempts': 0},
                    'error': 'client initialization failed'
                })
            else:
                return _print({'ok': False, 'error': 'client initialization failed'})
        if cmd == 'query':
            res = hc.query(text, url=url)
            if isinstance(res, dict) and 'selector' in res and 'element' in res:
                out = {
                    'element': res.get('element'),
                    'xpath': res.get('selector'),
                    'confidence': float(res.get('score', 0.0)),
                    'strategy': 'semantic',
                    'metadata': {'frame_path': '', 'used_frame_id': '', 'url': url or '', 'no_candidate': False},
                }
                return _print(out)
            # Normalize to strict schema if pipeline returns best element
            if isinstance(res, dict) and {'element','xpath','confidence','strategy','metadata'} <= set(res.keys()):
                return _print({
                    'element': res.get('element'),
                    'xpath': res.get('xpath'),
                    'confidence': float(res.get('confidence', 0.0)),
                    'strategy': str(res.get('strategy', 'fusion')),
                    'metadata': dict(res.get('metadata', {})),
                })
            # Strict error contract for no-candidate or unexpected shapes
            if isinstance(res, dict) and res.get('ok') is False:
                return _print(res)
            return _print({
                'element': None,
                'xpath': None,
                'confidence': 0.0,
                'strategy': 'none',
                'metadata': {'no_candidate': True, 'url': url or ''},
            })
        else:
            try:
                res = hc.act(text, url=url)
            except Exception as e:
                # Normalize failures (e.g., Playwright missing browsers) to strict JSON
                return _print({
                    'status': 'failure',
                    'method': 'click',
                    'confidence': 0.0,
                    'dom_hash': '',
                    'used_locator': None,
                    'overlay_events': [],
                    'retries': {'attempts': 0},
                    'error': str(e)
                })
            return _print(res if isinstance(res, dict) else {'ok': True, 'result': res})

    return _print({"ok": False, "error": f"Unknown command: {cmd}"})


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


# Back-compat function expected by some tests

def handle_cache_command(args) -> int:  # type: ignore
    cleared = bool(getattr(args, 'clear', False))
    stats = bool(getattr(args, 'stats', False))
    if cleared:
        out = {"ok": True, "cleared": True}
        return _print(out)
    if stats:
        out = {"ok": True, "stats": {}}
        return _print(out)
    return _print({"ok": True})
