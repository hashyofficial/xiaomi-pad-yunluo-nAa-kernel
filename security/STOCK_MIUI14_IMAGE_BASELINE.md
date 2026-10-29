# MIUI 14 stock-image reference — Redmi Pad (yunluo)

## Locally supplied original images

SHA-256 and byte counts below were calculated from the user-provided images without modifying them. Their names in this environment include numeric upload suffixes; those are not partition names.

| Uploaded file | Bytes | SHA-256 |
|---|---:|---|
| `boot(5).img` | 67,108,864 | `f2a20fd26ebaee6eee4e1d9fb0602afb97be7c3a8072ceb3c0e1bb840953ab95` |
| `vendor_boot(1).img` | 67,108,864 | `d9724f2712fb81745c26519e430375bbc9c759ac6df056496a404ef8ee456950` |
| `vendor_dlkm(1).img` | 11,231,232 | `41f4c4b443bbf10cb6522874738df8c3e3351ade8f2e20a06da71d171da83ce0` |
| `odm_dlkm(1).img` | 348,160 | `9de9cd73c9d6274f7aa21662a7a863a330abeeef279650155ce18d58cd6082c0` |

- Uploaded `boot(5).img`: Android boot image; stock Linux **5.10.168**.
- Uploaded `vendor_boot(1).img`: Android vendor boot image, header version **4**.
- Uploaded `vendor_dlkm(1).img` and `odm_dlkm(1).img`: EROFS filesystems.
- Preserve these exact files as reference images; no image is modified by these source changes.

## Archive stored with Git LFS

- Repo path: `archive.7z` (LFS; **148,181,775 bytes**).
- SHA-256: `24db429b340660f2d9626e4bed3a4a626841bcb2dc638b854b1a21da1508ad53`.
- GitHub Actions archive inventory validation: https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/actions/runs/40894026873 (passed).
- The archive contains `boot.img`, `cust.img`, `dpm.img`, `dtbo.img`, `efuse.img`, `gsort.img`, `gz.img`, `lk.img`, `mcupm.img`, `odm_dlkm.img`, `oem_misc1.img`, `pi_img.img`, `rescue.img`, `scp.img`, `spmfw.img`, `sspm.img`, `tee.img`, `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img`, `vendor_boot.img`, and `vendor_dlkm.img`.
- **`boot.img` is present in the current `archive.7z` and matches the separately uploaded `boot(5).img` byte-for-byte.**
- Four relevant image hashes have been verified against the separately uploaded MIUI reference images: boot, vendor_boot, vendor_dlkm and odm_dlkm.

## Guardrails

The original source repository remains Linux 5.10.101. Source changes applied here do **not** reconstruct Xiaomi's stock 5.10.168 binary, establish ASB compliance, or authorize flashing. Never replace or alter `efuse`, `tee`, `lk`, or other proprietary firmware images during a kernel-source maintenance build.

## Verified archive-to-upload comparison (2026-10-29)

GitHub Actions [run 40894735099](https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/actions/runs/40894735099) verified the archive SHA-256, selectively extracted **four** partitions on the runner, and compared hashes without committing or altering the images.

| Partition | Archive SHA-256 | Compared to user upload |
|---|---|---|
| `vendor_boot.img` | `d9724f2712fb81745c26519e430375bbc9c759ac6df056496a404ef8ee456950` | **MATCH** |
| `vendor_dlkm.img` | `41f4c4b443bbf10cb6522874738df8c3e3351ade8f2e20a06da71d171da83ce0` | **MATCH** |
| `odm_dlkm.img` | `9de9cd73c9d6274f7aa21662a7a863a330abeeef279650155ce18d58cd6082c0` | **MATCH** |
| `dtbo.img` | `c6df00ecabddebe7d8670c07430b1fceb701aaf7c7b26e4306e473343b3a7255` | Archive only; no separate uploaded reference compared |

These three matches establish that the original uploaded vendor boot and DLKM images are byte-for-byte identical to the corresponding partitions inside `archive.7z`. This earlier snapshot did not contain boot.img; the latest replacement archive now includes it.

## Current verified full archive (2026-10-29)

- [Successful complete archive sync](https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/actions/runs/40896878660) uses the newer `1h83n6.7z` source.
- SHA-256: `24db429b340660f2d9626e4bed3a4a626841bcb2dc638b854b1a21da1508ad53`.
- Size: 148,181,775 bytes.
- The 7z archive integrity test passed.
- `boot.img`, `vendor_boot.img`, `vendor_dlkm.img`, `odm_dlkm.img` all **match** the separately uploaded stock MIUI images.
- The prior archive (`70a529a1...`) was reuploaded accidentally via the old workflow; its missing-boot limitation no longer applies.
- The stock boot image uses Android boot header version **4**, contains compressed Linux `5.10.168-android12-9-00001-g81e7418c6466-ab10486262` and an embedded IKCONFIG (6,727 lines, SHA-256 `b8c5311022defe612368ceab314fe41a7b7923432db9e5b2cb5ad1db7da73b5f`).
- Audit script: `scripts/yunluo/inspect_stock_boot.py`; config and JSON report are emitted as GitHub Actions artifacts, **not used as an active kernel defconfig**.
