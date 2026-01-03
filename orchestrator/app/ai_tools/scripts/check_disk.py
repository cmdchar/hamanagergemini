#!/usr/bin/env python3
import shutil
import sys

def check_disk(path="/"):
    total, used, free = shutil.disk_usage(path)
    print(f"Disk Usage for {path}:")
    print(f"Total: {total // (2**30)} GB")
    print(f"Used: {used // (2**30)} GB")
    print(f"Free: {free // (2**30)} GB")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/"
    check_disk(path)
