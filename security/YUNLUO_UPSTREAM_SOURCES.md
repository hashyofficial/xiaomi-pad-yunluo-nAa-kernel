# Redmi Pad (yunluo) source provenance — pinned references

This project targets **stock MIUI 14 on the Wi-Fi-only Redmi Pad**. Work goes directly to `main` on [the user's repository](https://github.com/hashyofficial/xiaomi-pad-yunluo-nAa-kernel); there are no extra branches and no force pushes.

## Xiaomi original source — preserve stock functionality

| Component | Repository and branch | Verified commit |
|---|---|---|
| Published Xiaomi kernel | [MiCode/Xiaomi_Kernel_OpenSource — `yunluo-s-oss`](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/tree/yunluo-s-oss) | `d26d588883468251678619757cc9f0f6a5f37cb8` |
| Published MediaTek modules | [MiCode/MTK_kernel_modules — `yunluo-s-oss`](https://github.com/MiCode/MTK_kernel_modules/tree/yunluo-s-oss) | `9d544781673359d4096ea4e2c18fc34a9a2c578e` |

Xiaomi's kernel release identifies MediaTek source tag `t-alps-release-s0.mp1.tc8sp2-cs1-xm-V1` and `yunluo_defconfig`. Its published source Makefile is Linux **5.10.101**, whereas the supplied MIUI 14 `boot.img` contains Linux **5.10.168 Android 12 GKI**. Do not assume that the older Xiaomi source reproduces the shipped binary.

## Lineage development references — not drop-in stock modules

- Kernel: [xiaomi-mt6789-devs/kernel_xiaomi-yunluo](https://github.com/xiaomi-mt6789-devs/kernel_xiaomi-yunluo), historical Linux **5.10.168 version-bump commit** `707c48210a5384a72c82655a37895b7e822755f2`, later `vic` commit `d92da041e3ad824c273877abeeeb07c145c37d02` (Linux **5.10.243**).
- [Official device kernel manifest — `vic`](https://github.com/xiaomi-mt6789-devs/kernel_manifest-yunluo/blob/vic/default.xml), pinned snapshot below.

| External MediaTek component | `xiaomi-mt6789-devs` repository | Pinned `vic` commit |
|---|---|---|
| GPU | `kernel_mediatek-modules_gpu` | `10d3b7ab4a38635e367960e19ecf6c8cdffe9358` |
| Connectivity common | `kernel_mediatek-modules_connectivity_common` | `33ce60bbeef3c047fcd581279142160f8833d289` |
| CONNFEM | `kernel_mediatek-modules_connectivity_connfem` | `ffba24fb5ea95ca229aeae2ac1f1653e9cb18112` |
| Bluetooth MT66xx | `kernel_mediatek-modules_connectivity_bt_mt66xx` | `3779febdf2d9b6da8007589c014ab714ed200513` |
| FM radio | `kernel_mediatek-modules_connectivity_fmradio` | `00b4fc249465dfb7ad2a42ec7039250bf7d6fbbf` |
| WLAN adaptor | `kernel_mediatek-modules_connectivity_wlan_adaptor` | `9d6687e226868a6e4fdf5aea396b240ddbaf572a` |
| WLAN gen4m | `kernel_mediatek-modules_connectivity_wlan_core_gen4m` | `d9ebd8015bffce87b345dc1c4858ab25c79178c0` |

All commit IDs are fixed reference snapshots, not invitations to track changing branch tips. The Lineage `vic` manifest also needs separate AOSP kernel build tools and Android Clang. **Do not replace any stock MIUI external module** with a Lineage binary just because the module name matches; compare exported symbol CRCs, dependencies, config, and actual device ABI.

## Integration policy

1. Confirm source ancestry/patch prerequisites between the Xiaomi release and the Lineage historical 5.10.168 snapshot.
2. Apply verified kernel source patches to the real `main` tree; record upstream SHA and compile-test affected objects.
3. **Do not merge** Lineage-only configuration/device patches into MIUI automatically.
4. Only update kernel `SUBLEVEL` after the full corresponding source patches have landed and a kernel builds.
5. Before any flashable build, compare the candidate `Module.symvers` against stock modules' 3,675 distinct imported symbols across 358 modules and retain the rollback firmware.

`archive.7z` is the separately verified stock firmware input, not an output to repack or overwrite during source integration.
