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

## Reviewed but deliberately NOT applied

- **MediaTek CQDMA:** https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo/commit/dab666be25dae4c9c5d0746a018e78b2c0d53e24 — the latest source's physical-channel locking model is different from the code in Xiaomi 5.10.101. The patch does not apply directly; examine prerequisites before adapting it.
- **5.10.243 / October 2025 ASB merge:** NOT applied. Requires reconciling the old Xiaomi source against stock MIUI 5.10.168 and testing relevant kernel module compatibility.
- **LineageOS config cleanups:** NOT applied. In particular, keep the original MIUI-required MediaTek and Xiaomi functionality until confirmed unnecessary.

## Firmware source of truth

The `archive.7z` repository file is a **Git LFS pointer**, referring to an archive of 127,652,831 bytes with SHA-256:

`70a529a1aa61d8677127fc19c1fa3707908b3fcd09030808fe36489c94444c59`

The `miui-source-audit.yml` workflow downloads the LFS object on a GitHub runner and produces a read-only 7z inventory. It must never overwrite or redistribute the proprietary firmware images. Inspect firmware modules from `boot.img`, `vendor_boot.img`, `vendor_dlkm.img`, and `odm_dlkm.img` without modifying the originals.

## Next milestones

1. Inspect firmware archive inventory and compare all image versions and hashes with the uploaded baseline.
2. Reconstruct/verify the MIUI 5.10.168 kernel and its build configuration, compiler, device tree and KMI.
3. Review and backport relevant upstream stable and ASB changes in small, auditable source commits on `main`; do not merely change the version string.
4. Check symbol CRCs, module dependencies, and hardware-specific behavior before producing any experimental boot image.
5. Build/test with compatible toolchain and external MediaTek modules, then validate on device with a stock rollback package.

A green source/firmware audit is **not** evidence of a flash-ready kernel.
