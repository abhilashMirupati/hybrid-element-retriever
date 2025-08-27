# PLACE THIS FILE AT: src/her/cli_api.py

import argparse
from src.her.executor.actions import ActionExecutor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    ex = ActionExecutor()
    ex.goto(args.url)
    ex.close()

if __name__ == "__main__":
    main()
