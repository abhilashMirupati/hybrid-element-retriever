from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .cli_api import HybridClient
from .embeddings.cache import EmbeddingCache


def handle_cache_command(args) -> int:
    if getattr(args, 'clear', False):
        # Clear embeddings cache file directory
        cache_dir = Path.home() / '.cache' / 'her'
        if cache_dir.exists() and cache_dir.is_dir():
            for p in cache_dir.iterdir():
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    continue
        print("Cache cleared.")
        return 0
    if getattr(args, 'stats', False):
        cache = EmbeddingCache()
        stats = cache.stats()
        print("Cache Statistics:\n" + json.dumps(stats, indent=2))
        return 0
    print("No cache operation specified.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog='her', description='Hybrid Element Retriever CLI')
    sub = p.add_subparsers(dest='cmd', required=True)

    q = sub.add_parser('query', help='Resolve best locator for a phrase at a URL')
    q.add_argument('phrase')
    q.add_argument('--url', required=True)
    q.add_argument('--json', action='store_true', help='Output strict JSON')

    a = sub.add_parser('act', help='Execute action for a step at a URL')
    a.add_argument('step')
    a.add_argument('--url', required=True)
    a.add_argument('--json', action='store_true', help='Output strict JSON')

    c = sub.add_parser('cache', help='Cache operations')
    c.add_argument('--clear', action='store_true')
    c.add_argument('--stats', action='store_true')

    v = sub.add_parser('version', help='Print version')

    args = p.parse_args()

    try:
        if args.cmd == 'version':
            from . import __version__
            print(__version__)
            return 0
        if args.cmd == 'cache':
            return handle_cache_command(args)

        hc = HybridClient()
        if args.cmd == 'query':
            res = hc.query(args.phrase, args.url)
            out = json.dumps(res if getattr(args,'json',False) else res, ensure_ascii=False)
            print(out)
            return 0
        if args.cmd == 'act':
            res = hc.act(args.step, args.url)
            out = json.dumps(res if getattr(args,'json',False) else res, ensure_ascii=False)
            print(out)
            return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
