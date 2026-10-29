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

- Repo path: `archive.7z` (LFS; 127,652,831 bytes).
- SHA-256: `70a529a1aa61d8677127fc19c1fa3707908b3fcd09030808fe36489c94444c59`.
- GitHub Actions archive inventory validation: https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel/actions/runs/40894026873 (passed).
- The archive contains `cust.img`, `dpm.img`, `dtbo.img`, `efuse.img`, `gsort.img`, `gz.img`, `lk.img`, `mcupm.img`, `odm_dlkm.img`, `oem_misc1.img`, `pi_img.img`, `rescue.img`, `scp.img`, `spmfw.img`, `sspm.img`, `tee.img`, `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img`, `vendor_boot.img`, and `vendor_dlkm.img`.
- **`boot.img` is absent from `archive.7z`.** The separately supplied `boot(5).img` is the kernel binary reference.
- The archive and standalone uploads are **not assumed byte-for-byte identical** until the extracted archive partition hashes are checked against the values above.

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

These three matches establish that the original uploaded vendor boot and DLKM images are byte-for-byte identical to the corresponding partitions inside `archive.7z`. The separately uploaded `boot(5).img` remains the only supplied stock boot/kernel image and is not present in the archive.
