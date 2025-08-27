# PLACE: src/her/cli.py
"""CLI entrypoints for HER."""
import argparse, json, sys
from .cli_api import HybridClient

def main(argv=None):
    p = argparse.ArgumentParser(prog="her")
    sub = p.add_subparsers(dest="cmd", required=True)
    act = sub.add_parser("act")
    act.add_argument("step", help="Natural language step")
    act.add_argument("--url", help="URL to open", default=None)
    qry = sub.add_parser("query")
    qry.add_argument("phrase", help="Search phrase")
    qry.add_argument("--url", help="URL to open", default=None)
    args = p.parse_args(argv)
    client = HybridClient()
    if args.cmd == "act":
        out = client.act(args.step, url=args.url)
    else:
        out = client.query(args.phrase, url=args.url)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
