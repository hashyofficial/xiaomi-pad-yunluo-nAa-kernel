# Xiaomi Redmi Pad (yunluo) — kernel source backport ledger

## Scope and compatibility baseline

This repository contains Xiaomi's publicly released Linux **5.10.101** kernel source for the Redmi Pad (yunluo). The stock **MIUI 14 boot image is 5.10.168**, and the shipped modules depend on an Android GKI/KMI interface and symbol versions. This repository is not currently a verified reconstruction of the shipped 5.10.168 kernel.

**Working branch:** `main` only. No experimental branches, history rewrites, or forced pushes.

**Safety gate:** Do NOT flash a kernel built from this source until stock 5.10.168 source/config/ABI alignment, device tree checks, external module validation and real hardware testing have succeeded. Do not change the Makefile sublevel without incorporating the corresponding source updates.

## Applied directly to kernel source

### Backport 001 — userfaultfd ioctl output values

- **Upstream:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/e686428f8af350901f2204d6a900b8607bc0a3ad
- **File:** `fs/userfaultfd.c`
- **Functions:** `userfaultfd_copy`, `userfaultfd_zeropage`, `userfaultfd_continue`.
- **Problem:** An `-EAGAIN` early return while `ctx->mmap_changing` could leave the result field uninitialized.
- **Change:** Write `-EAGAIN` to the relevant user result field using `put_user`; return `-EFAULT` if that write fails. No kernel interface or config knobs intentionally changed.
- **Static check:** `python3 scripts/yunluo/verify_backports.py`
- **State:** Applied to source; compile, ABI and device tests are pending.
- **Security interpretation:** This fix is present in a security-maintained upstream Android 5.10 branch. This single backport does **not** certify any Android Security Bulletin level or claim that every vulnerability is fixed.

### Backport 002 — vsock autobind port rollover guard

- **Upstream:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/67f157746ba7b3b824a12a1337593413f40cadcf
- **File:** `net/vmw_vsock/af_vsock.c`
- **Problem:** A generated autobind port can wrap to `VMADDR_PORT_ANY`, which must not be used as an assigned port.
- **Change:** When generating a port, skip both `VMADDR_PORT_ANY` and the reserved range, as in the upstream one-condition fix.
- **State:** Applied to source; static regression checked; compilation, KMI and device testing pending.

### Build compatibility 003 — LLVM full-LTO and CFI detection on modern tools

- **File:** `arch/Kconfig`.
- **Reason:** The original Xiaomi Kconfig examined only the first line of `llvm-nm --help` and `llvm-ar --help`; recent LLVM prints a blank first line, which makes Kconfig incorrectly select `CONFIG_LTO_NONE=y` and disables CFI.
- **Change:** Check each LLVM tool's `--version` output instead. This checks the actual tool identity and does not weaken the LTO or CFI requirements.
- **Kernel source commit:** https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/commit/41aa29db0268ec4e5dcc5f0f4d37cc7334fcb174
- **Classification:** Build compatibility fix, **not** a claimed Android Security Bulletin patch. Source is still Linux 5.10.101; a successful native-clang smoke test does not prove compatibility with the stock Clang 12.0.5 build.

### Backport 004 — zero-limit packet FIFO drop

- **Upstream reference:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/85d1db8a9d1293a979f81f4f8b5cc142822be9cb (fix included in a later Android 12 security-maintained history). This specific hunk was independently verified against the current Xiaomi source.
- **File:** `net/sched/sch_fifo.c`, `pfifo_tail_enqueue()`.
- **Change:** Immediately drop the packet if `sch->limit == 0` before inspecting or removing a non-existent queue head.
- **Validation:** Static check plus AArch64 Clang 12 object compilation. No Android Security Bulletin patch level is implied.

### Backport 005 — minimum USB video format descriptor length

- **Upstream reference:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/1e269581b3aa5962fdc52757ab40da286168c087
- **File:** `drivers/media/usb/uvc/uvc_driver.c`, `uvc_parse_format()`.
- **Change:** Reject a format descriptor shorter than four bytes before accessing `buffer[2]` or `buffer[3]`.
- **Validation:** Static check plus AArch64 Clang 12 object compilation. No CVE/ASB level certified.

## Reviewed but deliberately NOT applied

- **MediaTek CQDMA:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/dab666be25dae4c9c5d0746a018e78b2c0d53e24 — the latest source's physical-channel locking model is different from the code in Xiaomi 5.10.101. The patch does not apply directly; examine prerequisites before adapting it.
- **5.10.243 / October 2025 ASB merge:** NOT applied. Requires reconciling the old Xiaomi source against stock MIUI 5.10.168 and testing relevant kernel module compatibility.
- **LineageOS config cleanups:** NOT applied. In particular, keep the original MIUI-required MediaTek and Xiaomi functionality until confirmed unnecessary.

## Firmware source of truth

The `archive.7z` repository file is a **Git LFS pointer**, referring to an archive of 148,181,775 bytes with SHA-256:

`24db429b340660f2d9626e4bed3a4a626841bcb2dc638b854b1a21da1508ad53`

The `miui-source-audit.yml` workflow downloads the LFS object on a GitHub runner and produces a read-only 7z inventory. It must never overwrite or redistribute the proprietary firmware images. Inspect firmware modules from `boot.img`, `vendor_boot.img`, `vendor_dlkm.img`, and `odm_dlkm.img` without modifying the originals.

## Next milestones

1. Inspect firmware archive inventory and compare all image versions and hashes with the uploaded baseline.
2. Reconstruct/verify the MIUI 5.10.168 kernel and its build configuration, compiler, device tree and KMI.
3. Review and backport relevant upstream stable and ASB changes in small, auditable source commits on `main`; do not merely change the version string.
4. Check symbol CRCs, module dependencies, and hardware-specific behavior before producing any experimental boot image.
5. Build/test with compatible toolchain and external MediaTek modules, then validate on device with a stock rollback package.

A green source/firmware audit is **not** evidence of a flash-ready kernel.
