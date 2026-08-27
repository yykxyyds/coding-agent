"""HTML 转 PDF 辅助命令（供 agent 通过 run_bash 调用）。

调用系统 Edge headless 打印成 PDF，零第三方依赖。
用法：
  python html_to_pdf.py <in.html> <out.pdf>
"""
import pathlib
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_edge():
    for p in EDGE_CANDIDATES:
        if pathlib.Path(p).exists():
            return p
    return shutil.which("msedge")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    edge = find_edge()
    if not edge:
        print("[错误] 未找到 Edge，无法转 PDF。")
        return
    src = pathlib.Path(argv[0]).resolve()
    dst = pathlib.Path(argv[1]).resolve()
    if not src.exists():
        print(f"[错误] HTML 文件不存在: {src}")
        return
    try:
        subprocess.run(
            [edge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={dst}", src.as_uri()],
            timeout=90, capture_output=True,
        )
    except subprocess.TimeoutExpired:
        print("[错误] Edge 打印超时。")
        return
    if dst.exists():
        print(f"[OK] 已生成 PDF: {dst}（{dst.stat().st_size} 字节）")
    else:
        print("[错误] PDF 未生成，请检查 Edge 是否可用。")


if __name__ == "__main__":
    main(sys.argv[1:])
