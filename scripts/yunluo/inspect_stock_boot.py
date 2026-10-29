#!/usr/bin/env python3
"""Read-only Android v3/v4 boot.img inspection for the Redmi Pad MIUI kernel.

This does not unpack a flashable image, rebuild a kernel, or modify its input.
Output .config is the kernel's embedded IKCONFIG (for reference, not a defconfig).
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib


def inspect_boot(path):
    image = path.read_bytes()
    if image[:8] != b"ANDROID!":
        raise ValueError("Not an Android boot image")
    kernel_size, ramdisk_size, os_version, header_size = struct.unpack_from("<IIII", image, 8)
    version = struct.unpack_from("<I", image, 40)[0]
    if version not in (3, 4) or not (1580 <= header_size <= 4096):
        raise ValueError(f"Unsupported boot header: v{version}, length {header_size}")
    start = 4096
    end = start + kernel_size
    if end > len(image):
        raise ValueError("Boot header declares kernel data beyond image end")
    if image[start : start + 2] != b"\x1f\x8b":
        raise ValueError("Expected gzip-compressed ARM64 kernel payload")
    kernel = zlib.decompress(image[start:end], wbits=31)
    release = re.search(rb"5\.10\.\d+-android12[^\x00\s]*", kernel)
    if not release:
        raise ValueError("Cannot find Android 12 Linux 5.10 kernel release")
    release = release.group().decode("ascii")
    kconfig_start = kernel.find(b"IKCFG_ST")
    kconfig_end = kernel.find(b"IKCFG_ED", kconfig_start + 8)
    if kconfig_start == -1 or kconfig_end == -1:
        raise ValueError("Missing complete embedded IKCONFIG")
    config_bytes = zlib.decompress(kernel[kconfig_start + 8 : kconfig_end], wbits=31)
    config = config_bytes.decode("utf-8")
    if "# Linux/arm64 5.10.168 Kernel Configuration" not in config:
        raise ValueError("Embedded kernel config does not match stock MIUI 5.10.168")
    needed = (
        "CONFIG_MODVERSIONS=y",
        "CONFIG_CFI_CLANG=y",
        "CONFIG_LTO_CLANG=y",
        "CONFIG_ANDROID_VENDOR_HOOKS=y",
    )
    for key in needed:
        if key not in config.splitlines():
            raise ValueError("Stock MIUI kernel missing expected ABI setting: " + key)
    return {
        "image_name": path.name,
        "image_size": len(image),
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "boot_header_version": version,
        "kernel_compressed_bytes": kernel_size,
        "ramdisk_bytes": ramdisk_size,
        "kernel_release": release,
        "embedded_kconfig_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "embedded_kconfig_lines": len(config.splitlines()),
        "required_settings": list(needed),
    }, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boot_image", type=Path)
    parser.add_argument("--output-config", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    info, config = inspect_boot(args.boot_image)
    if args.output_config:
        args.output_config.parent.mkdir(parents=True, exist_ok=True)
        args.output_config.write_text(config)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n")
    print(json.dumps(info, indent=2, sort_keys=True))
    print("NOTE: MIUI stock 5.10.168 is not reproduced by Xiaomi 5.10.101 source.")


if __name__ == "__main__":
    main()
