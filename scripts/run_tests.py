# -*- coding: utf-8 -*-
"""run_tests.py —— 一次跑完技能包自检

  python scripts/run_tests.py

三组：
  1. check_data.py   数据完整性（100 条、枚举、JSON/CSV 一致）
  2. lookup.py --selftest   查询逻辑 11 条断言
  3. 引用一致性：SKILL.md / references 里引用的条数与实际数据一致
"""

import os
import re
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable


def run(name, args):
    p = subprocess.run([PY, os.path.join(HERE, name)] + args,
                       capture_output=True, text=True, timeout=180, cwd=ROOT)
    out = (p.stdout or "").strip()
    tail = out.splitlines()[-1] if out else "(无输出)"
    if p.returncode == 0:
        print("[PASS] %-16s %s" % (name, tail))
        return True
    print("[FAIL] %-16s %s" % (name, tail))
    if p.stderr:
        print("       %s" % p.stderr.strip().splitlines()[-1])
    return False


def main():
    print("== 中国供应链源头产地 技能包自检 ==")
    print("解释器：%s" % PY)
    print()

    ok = True
    ok &= run("check_data.py", [])
    ok &= run("lookup.py", ["--selftest"])

    print()
    print("== 文档与数据一致性 ==")
    d = json.load(open(os.path.join(ROOT, "assets", "origins.json"), encoding="utf-8"))
    items = d["items"]
    from collections import Counter
    cv = Counter(i["verdict"] for i in items)
    cl = Counter(i["level"] for i in items)

    skill = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
    ref01 = open(os.path.join(ROOT, "references",
                              "01-方法论：怎么判断一条产业带说法是真是假.md"), encoding="utf-8").read()
    ref06 = open(os.path.join(ROOT, "references", "06-事实核查日志与边界.md"), encoding="utf-8").read()

    checks = [
        ("SKILL.md 提到 100", "100" in skill),
        ("SKILL.md 提到 59 属实", "59" in skill),
        ("SKILL.md 提到 25 需修正", "25" in skill),
        ("01 提到 25 条错误", "25 条" in ref01 or "25 条错的" in ref01),
        ("06 的占比 59%", "59%" in ref06),
        ("数据 ok=59", cv["ok"] == 59),
        ("数据 fix=25", cv["fix"] == 25),
        ("数据 doubt=14", cv["doubt"] == 14),
        ("数据 dup=2", cv["dup"] == 2),
        ("数据 A=42", cl["A"] == 42),
        ("C 级与存疑数相等", cl["C"] == cv["doubt"]),
    ]
    for label, cond in checks:
        print(("  [OK] " if cond else "  [FAIL] ") + label)
        ok &= bool(cond)

    print()
    print("== 汇总 ==")
    if ok:
        print("全部通过。")
        return 0
    print("存在未通过项。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
