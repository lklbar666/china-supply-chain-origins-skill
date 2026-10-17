# -*- coding: utf-8 -*-
"""
lookup.py —— 在 100 条核实结果里查

用法：
  python lookup.py --list                      # 全部 100 条
  python lookup.py --product 汉服               # 按产品（模糊匹配，含原文名）
  python lookup.py --place 曹县                 # 按地点（模糊匹配，含原地点）
  python lookup.py --province 山东              # 按省
  python lookup.py --verdict fix               # ok / fix / doubt / dup
  python lookup.py --level A                   # A / B / C
  python lookup.py --keyword 吉他               # 全文模糊
  python lookup.py --json                      # 机读
  python lookup.py --selftest                  # 内置断言

多个条件同时给，取交集。
退出码：0 有结果；1 无结果；2 数据缺失或参数错
"""

import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "assets", "origins.json")

PROVINCES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门",
]

MARK = {"ok": "OK ", "fix": "FIX", "doubt": "?? ", "dup": "DUP"}


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def match(it, args):
    if args.verdict and it["verdict"] != args.verdict:
        return False
    if args.level and it["level"] != args.level:
        return False
    if args.product:
        hay = it["product_raw"] + " " + it["product"]
        if args.product not in hay:
            return False
    if args.place:
        hay = it["places_raw"] + " " + it["place"]
        if args.place not in hay:
            return False
    if args.province:
        hay = it["places_raw"] + " " + it["place"]
        if args.province not in hay:
            return False
    if args.keyword:
        hay = " ".join(str(it[k]) for k in
                       ("product_raw", "places_raw", "product", "place", "note"))
        if args.keyword not in hay:
            return False
    return True


def render(items):
    out = []
    w = 4
    for it in items:
        head = "%s #%03d %s → %s" % (MARK[it["verdict"]], it["no"],
                                     it["product_raw"], it["places_raw"])
        out.append(head)
        if it["verdict"] == "dup":
            out.append("       └ %s" % it["note"])
        elif it["verdict"] == "ok":
            out.append("       └ 核定：%s ｜ %s  [%s]" % (it["product"], it["place"], it["level"]))
        else:
            out.append("       └ 应为：%s ｜ %s  [%s]" % (it["product"], it["place"], it["level"]))
            out.append("       └ 说明：%s" % it["note"])
    return "\n".join(out)


def selftest():
    d = load()
    items = d["items"]
    ok = fail = 0

    def check(label, got, want):
        nonlocal ok, fail
        if got == want:
            ok += 1
        else:
            fail += 1
            print("  FAIL %-40s got=%r want=%r" % (label, got, want))

    check("总条数", len(items), 100)
    check("序号连续", [i["no"] for i in items], list(range(1, 101)))

    ns = type("A", (), {"verdict": "fix", "level": None, "product": None,
                        "place": None, "province": None, "keyword": None})()
    check("fix 计数", len([i for i in items if match(i, ns)]), 25)

    ns = type("A", (), {"verdict": None, "level": "A", "product": None,
                        "place": None, "province": None, "keyword": None})()
    check("A 级计数", len([i for i in items if match(i, ns)]), 42)

    ns = type("A", (), {"verdict": None, "level": None, "product": "汉服",
                        "place": None, "province": None, "keyword": None})()
    hits = [i for i in items if match(i, ns)]
    check("查 汉服 命中数", len(hits), 1)
    check("汉服 判定", hits[0]["verdict"], "fix")

    ns = type("A", (), {"verdict": None, "level": None, "product": None,
                        "place": "曹县", "province": None, "keyword": None})()
    check("查 曹县 命中", len([i for i in items if match(i, ns)]), 1)

    ns = type("A", (), {"verdict": None, "level": None, "product": None,
                        "place": None, "province": "山东", "keyword": None})()
    sd = [i for i in items if match(i, ns)]
    check("山东省份命中数 >= 8", len(sd) >= 8, True)

    ns = type("A", (), {"verdict": None, "level": None, "product": None,
                        "place": None, "province": None, "keyword": "鄌郚"})()
    hits = [i for i in items if match(i, ns)]
    check("关键词 鄌郚 命中", len(hits), 2)  # 第32、40条

    ns = type("A", (), {"verdict": "dup", "level": None, "product": None,
                        "place": None, "province": None, "keyword": None})()
    check("dup 计数", len([i for i in items if match(i, ns)]), 2)

    # 渲染不能炸
    try:
        render(items[:3])
        ok += 1
    except Exception as e:
        fail += 1
        print("  FAIL render: %s" % e)

    print("lookup selftest: %d passed, %d failed" % (ok, fail))
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="中国供应链源头产地 100 条核实结果查询")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--product")
    ap.add_argument("--place")
    ap.add_argument("--province", choices=PROVINCES)
    ap.add_argument("--verdict", choices=["ok", "fix", "doubt", "dup"])
    ap.add_argument("--level", choices=["A", "B", "C"])
    ap.add_argument("--keyword")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not os.path.isfile(DATA):
        print("找不到数据文件：%s" % DATA)
        return 2

    d = load()
    items = [i for i in d["items"] if match(i, a)]
    if a.json:
        print(json.dumps({"meta": d["meta"], "count": len(items), "items": items},
                         ensure_ascii=False, indent=2))
        return 0 if items else 1
    if not items:
        print("没有匹配的条目。试试 --list 看全部，或换个关键词。")
        return 1

    print("共 %d 条（数据：%s 核实，源：%s）"
          % (len(items), d["meta"]["verified_on"], d["meta"]["source"]))
    print()
    print(render(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
