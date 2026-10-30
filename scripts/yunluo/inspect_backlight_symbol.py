#!/usr/bin/env python3
"""Verify the stock MIUI display backlight reference's ELF binding.

This is a read-only diagnostic. A weak undefined import is optional to the
module loader, but NOT proof the backlight code path is safe if invoked.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from audit_stock_abi import vendor_boot_modules

NAME = "mtk_drm_gateic_set_backlight"


def inspect(vendor_boot: Path, output: Path):
    modules = vendor_boot_modules(vendor_boot)
    found = [(path, payload) for path, payload in modules.items()
             if Path(path).name == "leds-mtk-disp.ko"]
    if len(found) != 1:
        raise RuntimeError(f"Expected exactly one stock leds-mtk-disp.ko in vendor_boot, got {len(found)}")

    with tempfile.TemporaryDirectory(prefix="yunluo-stock-backlight-") as tmp:
        path = Path(tmp) / "leds-mtk-disp.ko"
        path.write_bytes(found[0][1])
        process = subprocess.run(["readelf", "-Ws", str(path)],
                                 capture_output=True, text=True, check=True)
    matches = []
    for line in process.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] == NAME:
            matches.append({"type": fields[3], "binding": fields[4],
                            "visibility": fields[5], "index": fields[6]})
    if not matches:
        raise RuntimeError("Stock LEDs driver has no readelf symbol entry for " + NAME)
    is_weak_undefined = all(m["binding"] == "WEAK" and m["index"] == "UND"
                            for m in matches)
    provider = Path("drivers/gpu/drm/panel/mtk_drm_gateic.c").read_text()
    makefile = Path("drivers/gpu/drm/panel/Makefile").read_text()
    consumer = Path("drivers/leds/leds-mtk-disp.c").read_text()
    source_provider = ("EXPORT_SYMBOL(mtk_drm_gateic_set_backlight);" in provider
                       and "mtk_drm_gateic.o" in makefile
                       and "obj-$(CONFIG_DRM_MEDIATEK_PANEL) += mediatek-drm-gateic.o" in makefile)
    source_weak = ("__attribute__ ((weak)) mtk_drm_gateic_set_backlight" in consumer)
    result = {
        "stock_binary": found[0][0],
        "symbol": NAME,
        "stock_binary_elf_references": matches,
        "stock_binary_has_weak_undefined_reference": is_weak_undefined,
        "xiaomi_source_provider": "drivers/gpu/drm/panel/mtk_drm_gateic.c",
        "xiaomi_provider_module_if_enabled": "mediatek-drm-gateic.ko",
        "provider_is_separate_vendor_display_module": source_provider,
        "consumer_source_declares_weak": source_weak,
        "kernel_under_test": "5.10.101",
        "status": "OPTIONAL_AT_MODULE_LINK_TIME_NOT_RUNTIME_VALIDATED"
                  if is_weak_undefined and source_provider and source_weak
                  else "UNVERIFIED_DO_NOT_FLASH",
        "warning": "A weak undefined ELF symbol does not guarantee safe runtime brightness control. Do not add a stub, enable vendor display code in generic GKI, or claim 5.10.168 KMI compatibility.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "stock-backlight-weak-import.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not (is_weak_undefined and source_provider and source_weak):
        raise SystemExit("BLOCKED: Actual stock ELF binding/source assumptions differ")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vendor-boot", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    inspect(args.vendor_boot, args.output)
