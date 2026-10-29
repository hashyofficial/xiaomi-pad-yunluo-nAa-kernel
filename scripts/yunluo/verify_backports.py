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

makefile = Path("Makefile").read_text(encoding="utf-8")
parts = []
for field in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
    parts.append(next(line.split("=", 1)[1].strip() for line in makefile.splitlines() if line.startswith(field + " =")))
print("Kernel source release:", ".".join(parts))
print("PASS: static patch verification only; no build or boot guarantee")
