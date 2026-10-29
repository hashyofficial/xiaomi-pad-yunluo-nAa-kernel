#!/usr/bin/env python3
"""Inspect stock MIUI 14 vendor modules and compare source Kconfig (read-only).

Requires liblz4 for legacy vendor ramdisk, modinfo/modprobe (kmod).
Optional --symvers is a compiled candidate's Module.symvers; mismatched CRCs
are a strict ABI blocker, but absent symbols may be in external vendor modules.
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile


EXPECTED_STOCK = "5.10.168-android12-9-"
INTERESTING = [
    "CONFIG_ARCH_MEDIATEK", "CONFIG_MODVERSIONS", "CONFIG_CFI_CLANG",
    "CONFIG_CFI_CLANG_SHADOW", "CONFIG_LTO_CLANG", "CONFIG_LTO_CLANG_FULL",
    "CONFIG_LTO_CLANG_THIN", "CONFIG_ANDROID_VENDOR_HOOKS",
    "CONFIG_IKCONFIG", "CONFIG_MODULES", "CONFIG_KALLSYMS",
    "CONFIG_LD_IS_LLD", "CONFIG_GKI_HACKS_TO_FIX",
]


def sh(args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check)


def config_values(path):
    values = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        match = re.match(r"(CONFIG_[A-Z0-9_]+)=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2)
        match = re.match(r"# (CONFIG_[A-Z0-9_]+) is not set$", line)
        if match:
            values[match.group(1)] = "n"
    return values


def decompress_legacy_lz4(data):
    if data[:4] != b"\x02\x21\x4c\x18":
        raise ValueError("Unsupported vendor ramdisk compression; expected legacy LZ4")
    library = ctypes.util.find_library("lz4")
    if not library:
        raise RuntimeError("liblz4 unavailable; install liblz4-1")
    lib = ctypes.CDLL(library)
    decode = lib.LZ4_decompress_safe
    decode.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    decode.restype = ctypes.c_int
    position = 4
    output = bytearray()
    blocks = 0
    while position + 4 <= len(data):
        size = struct.unpack_from("<I", data, position)[0]
        position += 4
        if size == 0:
            break
        if size > 9 * 1024 * 1024 or position + size > len(data):
            raise ValueError("Invalid LZ4 legacy chunk length")
        src = ctypes.create_string_buffer(data[position:position+size])
        dst = ctypes.create_string_buffer(8 * 1024 * 1024)
        decoded = decode(src, dst, size, len(dst))
        if decoded < 0:
            raise ValueError("Invalid LZ4 legacy chunk")
        output.extend(dst.raw[:decoded])
        position += size
        blocks += 1
    if blocks == 0 or not output.startswith(b"070701"):
        raise ValueError("No valid compressed newc CPIO data")
    return bytes(output)


def vendor_boot_modules(path):
    image = Path(path).read_bytes()
    if image[:8] != b"VNDRBOOT":
        raise ValueError("Not an Android vendor boot image")
    header_version = struct.unpack_from("<I", image, 8)[0]
    page_size = struct.unpack_from("<I", image, 12)[0]
    ramdisk_size = struct.unpack_from("<I", image, 24)[0]
    if header_version != 4 or page_size != 4096 or ramdisk_size <= 0:
        raise ValueError("Unexpected vendor boot v4 layout")
    ramdisk = decompress_legacy_lz4(image[page_size:page_size + ramdisk_size])
    pos = 0
    modules = {}
    while pos + 110 <= len(ramdisk):
        if ramdisk[pos:pos+6] != b"070701":
            raise ValueError(f"Unexpected CPIO header at {pos}")
        nums = [int(ramdisk[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        size, name_len = nums[6], nums[11]
        name_bytes = ramdisk[pos+110:pos+110+name_len-1]
        name = name_bytes.decode("utf-8", errors="replace")
        start = (pos + 110 + name_len + 3) & ~3
        if name == "TRAILER!!!":
            break
        if name.endswith(".ko"):
            modules["vendor_boot/" + name] = ramdisk[start:start+size]
        pos = (start + size + 3) & ~3
    return modules


def load_symvers(path):
    symbols = {}
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("0x"):
            symbols[parts[1]] = parts[0].lower()
    return symbols


def analyze_modules(module_entries, output, candidate=None):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    crcs = []
    issues = []
    compared = matched = mismatched = missing = 0
    with tempfile.TemporaryDirectory(prefix="yunluo-modinfo-") as temp:
        for idx, (name, original) in enumerate(sorted(module_entries.items())):
            f = Path(temp) / (str(idx) + ".ko")
            f.write_bytes(original)
            v = sh(["modinfo", "-F", "vermagic", str(f)], check=False)
            vermagic = v.stdout.strip().replace("\t", " ")
            if not vermagic.startswith(EXPECTED_STOCK):
                issues.append(f"Unexpected kernel release in {name}: {vermagic}")
            rows.append((name, str(len(original)), hashlib.sha256(original).hexdigest(), vermagic))
            versioned = sh(["modprobe", "--show-modversions", str(f)], check=False)
            if versioned.returncode != 0:
                issues.append(f"Could not read CRC versions in {name}: {versioned.stderr.strip()[:120]}")
                continue
            for line in versioned.stdout.splitlines():
                fields = line.split()
                if len(fields) < 2 or not fields[0].startswith("0x"):
                    continue
                crc, symbol = fields[:2]
                crc = crc.lower()
                status = "no-candidate-symvers"
                if candidate is not None:
                    if symbol in candidate:
                        compared += 1
                        status = "match" if candidate[symbol] == crc else "MISMATCH"
                        if status == "match":
                            matched += 1
                        else:
                            mismatched += 1
                    else:
                        missing += 1
                        status = "unresolved-candidate-export"
                crcs.append((name, symbol, crc, status))
    (output / "module-inventory.tsv").write_text(
        "origin_and_module\tbytes\tsha256\tvermagic\n" +
        "".join("\t".join(row) + "\n" for row in rows)
    )
    (output / "module-required-crcs.tsv").write_text(
        "module\tsymbol\tneeded_crc\tstatus\n" +
        "".join("\t".join(row) + "\n" for row in crcs)
    )
    return {
        "modules": len(rows),
        "total_import_crc_entries": len(crcs),
        "unique_import_symbols": len(set(row[1] for row in crcs)),
        "candidate_known_symbols_compared": compared,
        "candidate_crc_matches": matched,
        "candidate_crc_mismatches": mismatched,
        "candidate_symbol_unresolved": missing,
        "warnings": issues[:100],
        "status": "NO_BUILD_AVAILABLE" if candidate is None else
                  "BLOCKED_CRC_MISMATCH" if mismatched else
                  "PARTIAL_CRC_MATCH_VERIFIED",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vendor-boot", type=Path, required=True)
    p.add_argument("--vendor-dlkm-dir", type=Path, required=True)
    p.add_argument("--odm-dlkm-dir", type=Path, required=True)
    p.add_argument("--stock-config", type=Path, required=True)
    p.add_argument("--source-gki-config", type=Path, required=True)
    p.add_argument("--source-yunluo-config", type=Path, required=True)
    p.add_argument("--lineage-gki-config", type=Path)
    p.add_argument("--symvers", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    modules = vendor_boot_modules(args.vendor_boot)
    per_source = {"vendor_boot": len(modules)}
    for partition, root in (("vendor_dlkm", args.vendor_dlkm_dir),
                            ("odm_dlkm", args.odm_dlkm_dir)):
        found = list(args_source for args_source in root.rglob("*.ko"))
        per_source[partition] = len(found)
        for item in found:
            modules[partition + "/" + str(item.relative_to(root))] = item.read_bytes()
    if per_source["vendor_boot"] < 100 or per_source["vendor_dlkm"] < 20:
        raise ValueError("Expected MIUI module inventory incomplete: " + repr(per_source))
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = {"stock_boot_config": args.stock_config,
              "xiaomi_gki_defconfig_5_10_101": args.source_gki_config,
              "xiaomi_yunluo_defconfig_5_10_101": args.source_yunluo_config}
    if args.lineage_gki_config:
        inputs["lineage_vic_gki_defconfig_5_10_243"] = args.lineage_gki_config
    sets = {name: config_values(path) for name, path in inputs.items()}
    config_matrix = {key: {name: value.get(key, "UNSPECIFIED")
                           for name, value in sets.items()} for key in INTERESTING}
    (args.output / "config-compatibility.json").write_text(
        json.dumps(config_matrix, indent=2, sort_keys=True) + "\n")
    candidate = load_symvers(args.symvers) if args.symvers else None
    modinfo = analyze_modules(modules, args.output, candidate)
    report = {
        "module_counts_by_origin": per_source,
        "module_abi": modinfo,
        "stock_kernel_expected": EXPECTED_STOCK,
        "kernel_version_in_this_source": "5.10.101",
        "test_type": "READ_ONLY_STOCK_INVENTORY_NOT_KERNEL_BUILD",
        "config_flags": config_matrix,
    }
    (args.output / "stock-compatibility.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "module_counts": per_source, "module_abi_summary": {k: v for k, v in modinfo.items() if k != "warnings"},
        "config_matrix": config_matrix,
    }, indent=2, sort_keys=True))
    if modinfo["warnings"]:
        print("WARNINGS:", *modinfo["warnings"][:20], sep="\n")
    if candidate is not None and modinfo["candidate_crc_mismatches"]:
        raise SystemExit("BLOCKED: candidate Module.symvers CRC mismatch with stock MIUI modules")
    print("PASS: stock module inventory complete; no claim of new-kernel compatibility")


if __name__ == "__main__":
    main()
