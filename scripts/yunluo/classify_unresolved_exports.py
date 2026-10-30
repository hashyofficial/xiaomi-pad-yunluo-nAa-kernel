#!/usr/bin/env python3
"""Classify unresolved stock MIUI module imports by actual stock .ko exports.

This is a source/ELF *ownership* inventory, not an ABI or boot-compatibility proof:
an __ksymtab_ symbol proves that a module defines an export but NOT that the
candidate's loaded module CRCs and dependency ordering are safe.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import subprocess
import tempfile

from audit_stock_abi import vendor_boot_modules

def exported_symbols(blob: bytes, nm: str, directory: Path, index: int):
    module = directory / f"{index}.ko"
    module.write_bytes(blob)
    proc = subprocess.run([nm, "-a", "--defined-only", str(module)],
                          capture_output=True, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"{nm} failed for stock module #{index}: {proc.stderr[:300]}")
    exports = set()
    for line in proc.stdout.splitlines():
        fields = line.split()
        if fields and fields[-1].startswith("__ksymtab_"):
            symbol = fields[-1][len("__ksymtab_"):]
            if symbol:
                exports.add(symbol)
    return exports

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imports", type=Path, required=True)
    parser.add_argument("--vendor-boot", type=Path, required=True)
    parser.add_argument("--vendor-dlkm", type=Path, required=True)
    parser.add_argument("--odm-dlkm", type=Path, required=True)
    parser.add_argument("--nm", default="aarch64-linux-gnu-nm")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    with args.imports.open(newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    unresolved = [r for r in rows if r["status"] == "unresolved-candidate-export"]
    if not unresolved:
        raise RuntimeError("No unresolved-candidate-export records in existing ABI report")
    candidates = {r["symbol"] for r in unresolved}
    modules = vendor_boot_modules(args.vendor_boot)
    for location, root in (("vendor_dlkm", args.vendor_dlkm),
                           ("odm_dlkm", args.odm_dlkm)):
        for item in sorted(root.rglob("*.ko")):
            modules[f"{location}/{item.relative_to(root)}"] = item.read_bytes()
    if len(modules) != 358:
        raise RuntimeError(f"Unexpected original MIUI module count: {len(modules)} (expected 358)")

    providers = collections.defaultdict(set)
    with tempfile.TemporaryDirectory(prefix="yunluo-export-nm-") as tmp:
        for i, (name, payload) in enumerate(sorted(modules.items())):
            for symbol in exported_symbols(payload, args.nm, Path(tmp), i) & candidates:
                providers[symbol].add(name)

    counts = collections.Counter()
    with (args.output / "unresolved-symbol-providers.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("importing_module", "symbol", "stock_import_crc",
                         "classification", "stock_vendor_exporters"))
        for row in unresolved:
            matching = sorted(providers[row["symbol"]])
            kind = "STOCK_VENDOR_EXPORT_POSSIBLE" if matching else "NOT_IN_STOCK_VENDOR_EXPORTS"
            counts[kind] += 1
            writer.writerow((row["module"], row["symbol"], row["needed_crc"],
                             kind, ";".join(matching)))

    distinct = collections.Counter()
    with (args.output / "unresolved-distinct-symbols.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("symbol", "imported_by_count", "classification", "stock_vendor_exporters"))
        for symbol in sorted(candidates):
            matches = [r for r in unresolved if r["symbol"] == symbol]
            kind = "STOCK_VENDOR_EXPORT_POSSIBLE" if providers[symbol] else "NOT_IN_STOCK_VENDOR_EXPORTS"
            distinct[kind] += 1
            writer.writerow((symbol, len(matches), kind, ";".join(sorted(providers[symbol]))))

    report = {
        "status": "OWNERSHIP_ONLY_CRC_NOT_VERIFIED",
        "kernel_source": "5.10.101; stock boot uses 5.10.168",
        "checked_stock_modules": len(modules),
        "unresolved_import_entries": len(unresolved),
        "unresolved_distinct_symbols": len(candidates),
        "entry_classifications": dict(counts),
        "symbol_classifications": dict(distinct),
        "warning": "Vendor provider detected via defined __ksymtab_ symbols only; CRC, dependencies, module loading and KMI remain UNVERIFIED. Symbols absent from both candidate vmlinux.symvers and stock vendor exports require investigation.",
    }
    (args.output / "unresolved-summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not counts["NOT_IN_STOCK_VENDOR_EXPORTS"]:
        print("No unowned imports found; however CRC and KMI are still unverified.")

if __name__ == "__main__":
    main()
