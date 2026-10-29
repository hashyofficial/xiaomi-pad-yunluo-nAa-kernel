# MIUI 14 — GKI 5.10.168 reconstruction constraints (yunluo)

## Why a version-string bump or straight Lineage merge is unsafe

The Xiaomi-published kernel on `main` is Linux **5.10.101**. The stock Redmi Pad MIUI 14 `boot.img` is Android 12 GKI **5.10.168**. These are distinct build baselines:

- Stock MIUI: `CONFIG_ARCH_MEDIATEK` is disabled **in the generic GKI kernel**. MediaTek-specific hardware support is loaded from `vendor_boot`, `vendor_dlkm` and other vendor modules. This does **not** mean the tablet lacks MTK support.
- Xiaomi's `yunluo_defconfig` in this repository sets `CONFIG_ARCH_MEDIATEK=y` and many board/MTK driver flags. It is not the same as the stock GKI configuration.
- Stock MIUI uses `CONFIG_MODVERSIONS=y`, `CONFIG_CFI_CLANG=y`, `CONFIG_LTO_CLANG=y`, `CONFIG_LTO_CLANG_FULL=y`, and `CONFIG_ANDROID_VENDOR_HOOKS=y`. Its embedded config uses Android Clang **12.0.5**.
- The source's `arch/arm64/configs/gki_defconfig` uses **full** Clang LTO. The Lineage `vic` 5.10.243 GKI defconfig uses **thin** Clang LTO. Rebuilding the Lineage configuration as-is would not reproduce stock MIUI.
- The historical `707c48210a5384a72c82655a37895b7e822755f2` commit in the custom kernel is the generic stable Linux 5.10.168 *version bump*. **It does not prove the MIUI binary derives from that git commit, or that matching 5.10.168 alone gives a module-compatible kernel.**
- Stock vendor module `vermagic` can contain a different commit suffix from the GKI kernel release. With `CONFIG_MODVERSIONS`, **exported symbol CRCs must be compared**, not just string suffixes.

## ABI validation method

`scripts/yunluo/audit_stock_abi.py` runs on the unmodified stock firmware:

1. Decompress the legacy-LZ4 vendor ramdisk in `vendor_boot.img` and inventory its `.ko` modules and their `vermagic`.
2. Extract the EROFS `vendor_dlkm.img` and `odm_dlkm.img` modules using `fsck.erofs --extract`.
3. Collect imported symbol version CRCs with `modprobe --show-modversions`. This documents the actual symbols stock MIUI modules need.
4. Compare important build configuration keys across the stock kernel's embedded `.config`, the Xiaomi GKI defconfig, the Xiaomi MTK yunluo defconfig, and the latest custom Lineage GKI defconfig.
5. Only **after** a candidate kernel is compiled, compare stock module-required CRCs against its actual `Module.symvers` with `--symvers`.

A module's missing symbol in candidate `Module.symvers` may be provided by another vendor module; resolve such symbols with the complete external module builds. A **CRC mismatch** on a known export is a hard stop. Matching CRCs alone does not guarantee compatibility of CFI, DTB/DTBO, toolchain, boot ramdisk or hardware behavior.

## Source integration order

1. Use GKI `gki_defconfig` as the **reference** for the stock generic kernel, and keep the published `yunluo_defconfig` unchanged for now.
2. Determine which Android 12 GKI security/stable commits are already in the 5.10.101 tree and which are absent.
3. Apply small, validated source patches directly on `main`, with upstream references and static/compile tests. Avoid force pushes and avoid adding extra branches.
4. Establish a reproducible **5.10.168** GKI build with the stock Clang/config and an exported symbol list. Only then consider advancing to 5.10.243 or selectively backporting newer Android Security Bulletin fixes.
5. Treat successful compilation and ABI checking as necessary, not sufficient: no automatically flashable MIUI boot package.

**Current status:** stock firmware verified and source backport ledger started; a genuinely buildable MIUI-compatible 5.10.168 kernel has **not** been established yet.

## Stock module ABI inventory — verified on 2026-10-29

The first complete audit [Actions run 40899816068](https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/actions/runs/40899816068) completed successfully, with actual EROFS extraction and vendor-ramdisk decompression:

| Origin | Stock `.ko` files |
|---|---:|
| Vendor ramdisk inside `vendor_boot.img` | **187** |
| `vendor_dlkm.img` EROFS | **171** |
| `odm_dlkm.img` EROFS | **0** |
| **Total** | **358** |

- Imported CRC records across modules: **18,860**.
- Distinct symbols imported with recorded CRCs: **3,675**.
- No candidate kernel has been compiled yet: **zero symbol comparisons were performed**. The absence of reported mismatches means **not tested**, *not* compatible.
- Archive SHA-256 and all four core partition-image hashes passed.
- Audit artifact includes `module-inventory.tsv`, `module-required-crcs.tsv`, `config-compatibility.json`, `stock-compatibility.json`, and stock kernel `.config` reference. Those inventory files have no proprietary kernel modules.

## Next source-build checkpoint

- `build.config.yunluo.miui14-gki-preview` explicitly uses **GKI** source configuration rather than the old `yunluo_defconfig` hardware-in-kernel configuration.
- `.github/workflows/miui-gki-source-smoke.yml` compiles the existing 5.10.101 source's config, build preparation, and two patched objects using the runner's LLVM toolchain; it does **not** claim a stock 5.10.168 build, ABI compatibility, or a bootable kernel.
- If compilation fails, record the actual errors and fix only source/toolchain issues supported by evidence. Do not rename the version or remove MIUI-required flags to force a green build.
