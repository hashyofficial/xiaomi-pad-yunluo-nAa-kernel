#!/usr/bin/env python3
"""Verify the exact userfaultfd backport exists in the kernel source.

This static check cannot establish build success, module ABI or boot safety.
"""
from pathlib import Path

source = Path("fs/userfaultfd.c").read_text(encoding="utf-8")
cases = (
    ("userfaultfd_copy", "user_uffdio_copy->copy"),
    ("userfaultfd_zeropage", "user_uffdio_zeropage->zeropage"),
    ("userfaultfd_continue", "user_uffdio_continue->mapped"),
)
for function, field in cases:
    start = source.index(f"static int {function}(")
    finish = source.find("\nstatic ", start + 1)
    body = source[start:finish if finish != -1 else len(source)]
    expected = (
        "ret = -EAGAIN;\n"
        "\tif (unlikely(READ_ONCE(ctx->mmap_changing))) {\n"
        f"\t\tif (unlikely(put_user(ret, &{field})))\n"
        "\t\t\treturn -EFAULT;\n"
        "\t\tgoto out;\n"
        "\t}"
    )
    if body.count(expected) != 1:
        raise SystemExit(f"FAIL: missing or duplicated upstream fix in {function}")
    print(f"PASS: {function} writes -EAGAIN to {field} before returning")

vsock = Path("net/vmw_vsock/af_vsock.c").read_text(encoding="utf-8")
if vsock.count("if (port == VMADDR_PORT_ANY ||") != 1:
    raise SystemExit("FAIL: vsock wildcard port guard is missing or duplicated")
if "port <= LAST_RESERVED_PORT)" not in vsock:
    raise SystemExit("FAIL: vsock reserved port guard is missing")
print("PASS: vsock autobind checks wildcard and reserved port range")

fifo = Path("net/sched/sch_fifo.c").read_text(encoding="utf-8")
fifo_start = fifo.index("static int pfifo_tail_enqueue(")
fifo_end = fifo.index("static void fifo_offload_init", fifo_start)
fifo_body = fifo[fifo_start:fifo_end]
if fifo_body.count("if (unlikely(sch->limit == 0))") != 1:
    raise SystemExit("FAIL: pfifo_tail zero-limit guard missing")
if fifo_body.index("if (unlikely(sch->limit == 0))") > fifo_body.index("if (likely(sch->q.qlen < sch->limit))"):
    raise SystemExit("FAIL: pfifo_tail guard must precede queue access")
if "return qdisc_drop(skb, sch, to_free);" not in fifo_body:
    raise SystemExit("FAIL: pfifo_tail zero-limit guard must drop")
print("PASS: pfifo_tail zero-limit drop guard")

uvc = Path("drivers/media/usb/uvc/uvc_driver.c").read_text(encoding="utf-8")
uvc_start = uvc.index("static int uvc_parse_format(")
uvc_body = uvc[uvc_start:uvc.index("switch (buffer[2])", uvc_start)]
if uvc_body.count("if (buflen < 4)") != 1:
    raise SystemExit("FAIL: UVC descriptor minimum length guard missing")
if uvc_body.index("if (buflen < 4)") > uvc_body.index("format->type = buffer[2]"):
    raise SystemExit("FAIL: UVC bounds check must precede buffer[2] access")
if "return -EINVAL;" not in uvc_body:
    raise SystemExit("FAIL: UVC short format descriptor must return -EINVAL")
print("PASS: UVC format descriptor minimum length guard")

# Core printk signed-overflow hardening (upstream dfb7b179741e).
printk = Path("kernel/printk/printk.c").read_text(encoding="utf-8")
if printk.count("#define LOG_BUF_LEN_MAX ((u32)1 << 31)") != 1:
    raise SystemExit("FAIL: printk LOG_BUF_LEN_MAX unsigned left-shift missing")
print("PASS: printk LOG_BUF_LEN_MAX uses unsigned left-shift")

# IPVS allocation-size arithmetic must not wrap a signed int.
ipvs = Path("net/netfilter/ipvs/ip_vs_ctl.c").read_text(encoding="utf-8")
for label in ("services", "dests"):
    match = f"get = (struct ip_vs_get_{label} *)arg;"
    index = ipvs.index(match)
    if "size_t size;" not in ipvs[index-50:index]:
        raise SystemExit(f"FAIL: IPVS {label} size calculation still uses int")
if ipvs.count('pr_err("length: %u != %zu') != 2:
    raise SystemExit("FAIL: IPVS size_t printf format missing")
print("PASS: IPVS service and destination sizes use size_t")

# BATMAN-adv XOR must validate both payload buffers + protocol headers.
batman = Path("net/batman-adv/network-coding.c").read_text(encoding="utf-8")
start = batman.index("coding_len = ntohs(coded_packet_tmp.coded_len);")
end = batman.index("batadv_nc_memxor(", start)
body = batman[start:end]
for check in ("coding_len + h_size > skb->len",
              "coding_len + h_size > nc_packet->skb->len"):
    if body.count(check) != 1:
        raise SystemExit(f"FAIL: BATMAN-adv payload guard missing: {check}")
print("PASS: BATMAN-adv both XOR source and destination length checked")

makefile = Path("Makefile").read_text(encoding="utf-8")
parts = []
for field in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
    parts.append(next(line.split("=", 1)[1].strip() for line in makefile.splitlines() if line.startswith(field + " =")))
print("Kernel source release:", ".".join(parts))
print("PASS: static patch verification only; no build or boot guarantee")
