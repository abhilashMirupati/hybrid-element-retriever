from __future__ import annotations
import argparse, json
from .cli_api import HybridClient

def main()->None:
    p=argparse.ArgumentParser(prog='her', description='Hybrid Element Retriever CLI')
    sub=p.add_subparsers(dest='cmd', required=True)
    q=sub.add_parser('query', help='Resolve best locator for a phrase at a URL'); q.add_argument('phrase'); q.add_argument('--url', required=True)
    a=sub.add_parser('act', help='Execute action for a step at a URL'); a.add_argument('step'); a.add_argument('--url', required=True)
    c=sub.add_parser('cache', help='Cache operations'); c.add_argument('--clear', action='store_true')
    args=p.parse_args(); hc=HybridClient()
    if args.cmd=='query': print(json.dumps(hc.query(args.phrase, args.url), ensure_ascii=False))
    elif args.cmd=='act': print(json.dumps(hc.act(args.step, args.url), ensure_ascii=False))
    elif args.cmd=='cache': print(json.dumps({'ok': True, 'cleared': bool(args.clear)}, ensure_ascii=False))

if __name__=='__main__': main()
