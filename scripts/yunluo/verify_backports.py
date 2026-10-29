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
fifo_expected = "if (unlikely(sch->limit == 0))\\n\\t\\treturn qdisc_drop(skb, sch, to_free);"
if fifo_expected.replace("\\\\n", "\\n").replace("\\\\t", "\\t") not in fifo:
    raise SystemExit("FAIL: pfifo_tail limit zero must drop without dereference")
print("PASS: pfifo_tail zero-limit drop guard")

uvc = Path("drivers/media/usb/uvc/uvc_driver.c").read_text(encoding="utf-8")
start = uvc.index("static int uvc_parse_format(")
body = uvc[start:uvc.index("switch (buffer[2])", start)]
if body.count("if (buflen < 4)\\n\\t\\treturn -EINVAL;".replace("\\\\n", "\\n").replace("\\\\t", "\\t")) != 1:
    raise SystemExit("FAIL: UVC descriptor min length validation absent")
if body.index("if (buflen < 4)") > body.index("format->type = buffer[2]"):
    raise SystemExit("FAIL: UVC bounds check must be before buffer[2] access")
print("PASS: UVC format descriptor length checked before access")

makefile = Path("Makefile").read_text(encoding="utf-8")
parts = []
for field in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
    parts.append(next(line.split("=", 1)[1].strip() for line in makefile.splitlines() if line.startswith(field + " =")))
print("Kernel source release:", ".".join(parts))
print("PASS: static patch verification only; no build or boot guarantee")
