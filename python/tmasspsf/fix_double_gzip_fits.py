#!/usr/bin/env python3

import argparse
import gzip
from pathlib import Path

GZIP_MAGIC = b"\x1f\x8b"
FITS_MAGIC = b"SIMPLE  ="


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def classify_bytes(raw):
    """
    Returns:
        kind, payload

    kind:
      - plain_fits
      - single_gzipped_fits
      - double_gzipped_fits
      - gzipped_nonfits
      - double_gzipped_nonfits
      - unknown

    payload:
      - for plain_fits: raw FITS bytes
      - for single_gzipped_fits: decompressed FITS bytes
      - for double_gzipped_fits: the once-decompressed bytes
        (which should themselves be a valid single .gz stream containing FITS)
    """
    if raw.startswith(FITS_MAGIC):
        return "plain_fits", raw

    if not raw.startswith(GZIP_MAGIC):
        return "unknown", raw

    try:
        once = gzip.decompress(raw)
    except Exception:
        return "unknown", raw

    if once.startswith(FITS_MAGIC):
        return "single_gzipped_fits", once

    if once.startswith(GZIP_MAGIC):
        try:
            twice = gzip.decompress(once)
        except Exception:
            return "double_gzipped_nonfits", once

        if twice.startswith(FITS_MAGIC):
            return "double_gzipped_fits", once
        return "double_gzipped_nonfits", twice

    return "gzipped_nonfits", once


def normalized_output_path(path, outdir=None):
    """
    Ensure the repaired file ends with .fits.gz.
    """
    name = path.name

    if name.endswith(".fits.gz"):
        outname = name
    elif name.endswith(".fit.gz"):
        outname = name[:-7] + ".fits.gz"
    elif name.endswith(".fts.gz"):
        outname = name[:-7] + ".fits.gz"
    elif name.endswith(".gz"):
        outname = name[:-3] + ".fits.gz"
    elif name.endswith(".fits"):
        outname = name + ".gz"
    elif name.endswith(".fit"):
        outname = name[:-4] + ".fits.gz"
    elif name.endswith(".fts"):
        outname = name[:-4] + ".fits.gz"
    else:
        outname = name + ".fits.gz"

    if outdir is None:
        return path.with_name(outname)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir / outname


def process_file(path, fix=False, overwrite=False, outdir=None):
    raw = read_bytes(path)
    kind, payload = classify_bytes(raw)

    result = {
        "path": path,
        "kind": kind,
        "fixed": False,
        "output": None,
        "message": "",
    }

    if kind != "double_gzipped_fits":
        return result

    if not fix:
        result["message"] = "needs_fix"
        return result

    outpath = normalized_output_path(path, outdir=outdir)

    if outpath.exists() and not overwrite and outpath != path:
        result["message"] = f"skip_exists:{outpath}"
        return result

    # payload is the once-decompressed byte stream, which is already
    # a proper single gzip stream containing the FITS file.
    if outpath == path:
        # overwrite original in-place
        with open(outpath, "wb") as f:
            f.write(payload)
    else:
        with open(outpath, "wb") as f:
            f.write(payload)

    result["fixed"] = True
    result["output"] = outpath
    result["message"] = "fixed"
    return result


def iter_files(root, recursive=True):
    root = Path(root)
    if root.is_file():
        yield root
        return

    if recursive:
        for p in root.rglob("*"):
            if p.is_file():
                yield p
    else:
        for p in root.glob("*"):
            if p.is_file():
                yield p


def main():
    parser = argparse.ArgumentParser(
        description="Detect and fix double-gzipped FITS files so the output is singly-gzipped .fits.gz."
    )
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--fix", action="store_true", help="Actually fix the files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--inplace", action="store_true", help="Rewrite bad files in place")
    parser.add_argument("--outdir", default=None, help="Optional output directory")
    parser.add_argument("--no-recursive", action="store_true", help="Do not scan subdirectories")
    parser.add_argument(
        "--extensions-only",
        action="store_true",
        help="Only inspect files ending in .fits, .fit, .fts, .gz, .fz",
    )
    args = parser.parse_args()

    if args.inplace and args.outdir is not None:
        raise ValueError("--inplace and --outdir cannot be used together")

    exts = {".fits", ".fit", ".fts", ".gz", ".fz"}
    counts = {}

    for path in iter_files(args.path, recursive=not args.no_recursive):
        if args.extensions_only and path.suffix.lower() not in exts:
            continue

        try:
            result = process_file(
                path,
                fix=args.fix,
                overwrite=args.overwrite or args.inplace,
                outdir=None if args.inplace else args.outdir,
            )
        except Exception as e:
            print(f"ERROR  {path}  {e}")
            counts["error"] = counts.get("error", 0) + 1
            continue

        kind = result["kind"]
        counts[kind] = counts.get(kind, 0) + 1

        if kind == "double_gzipped_fits":
            if result["fixed"]:
                print(f"FIXED  {path}  ->  {result['output']}")
            else:
                print(f"BAD    {path}  [{result['message']}]")
        else:
            print(f"OK     {path}  [{kind}]")

    print("\nSummary:")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")


if __name__ == "__main__":
    main()
