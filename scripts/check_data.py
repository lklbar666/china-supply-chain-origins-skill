# -*- coding: utf-8 -*-
"""
check_data.py —— 数据完整性断言（打包前、改数据后都跑一遍）

只读，不改任何文件。检查：
  1. 条数 = 100，序号 1..100 连续无重
  2. verdict / level 都是合法枚举
  3. 所有字段非空；fix/doubt 必须有 note
  4. ok 的条目 product/place 与原文字段不能完全一样（否则等于没核）
  5. JSON 与 CSV 的条数与序号一致
  6. 重复条目必须指向已存在的序号
"""

import os
import re
import csv
import json
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JSON_PATH = os.path.join(ROOT, "assets", "origins.json")
CSV_PATH = os.path.join(ROOT, "assets", "corrections.csv")

VERDICTS = {"ok", "fix", "doubt", "dup"}
LEVELS = {"A", "B", "C"}
REQUIRED = ["no", "product_raw", "places_raw", "verdict", "verdict_cn",
            "product", "place", "note", "level", "level_cn"]


def main():
    problems = []

    with open(JSON_PATH, encoding="utf-8") as f:
        d = json.load(f)
    items = d["items"]

    if len(items) != 100:
        problems.append("条数不是 100：%d" % len(items))

    nos = [i["no"] for i in items]
    if nos != list(range(1, 101)):
        problems.append("序号不连续或重复")
    if len(set(nos)) != len(nos):
        problems.append("存在重复序号")

    for i in items:
        miss = [k for k in REQUIRED if k not in i]
        if miss:
            problems.append("#%s 缺字段 %s" % (i.get("no"), miss))
            continue
        if i["verdict"] not in VERDICTS:
            problems.append("#%d verdict 非法：%s" % (i["no"], i["verdict"]))
        if i["level"] not in LEVELS:
            problems.append("#%d level 非法：%s" % (i["no"], i["level"]))
        if i["verdict"] in ("fix", "doubt") and len(i["note"]) < 6:
            problems.append("#%d %s 的 note 过短" % (i["no"], i["verdict"]))
        if i["verdict"] != "dup":
            if not i["product"].strip() or not i["place"].strip():
                problems.append("#%d product/place 为空" % i["no"])
        if i["verdict"] == "ok":
            if i["product"] == i["product_raw"] and i["place"] == i["places_raw"]:
                problems.append("#%d 判 ok 但核定值与原文完全一致，等于没核" % i["no"])
        # 地名里出现两个“区”连写，提醒复查行政区划
        # 先剔掉“社区/园区/小区/开发区/景区/城区”这类词，避免误报
        probe = i["places_raw"]
        for w in ("社区", "园区", "小区", "开发区", "景区", "城区", "辖区", "地区"):
            probe = probe.replace(w, "")
        if re.search(r"区[^、，]{0,6}区", probe) and i["verdict"] != "fix":
            problems.append("#%d 原文含两个“区”连写却未判 fix：%s" % (i["no"], i["places_raw"]))

    # dup 必须指向别的条目
    for i in items:
        if i["verdict"] == "dup":
            m = re.search(r"第\s*(\d+)", i["note"])
            if not m:
                problems.append("#%d 是 dup 但 note 里没写指向" % i["no"])
            elif int(m.group(1)) not in nos:
                problems.append("#%d dup 指向不存在的 #%s" % (i["no"], m.group(1)))

    # CSV 一致性
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) - 1 != len(items):
        problems.append("CSV 数据行 %d 与 JSON 条数 %d 不一致"
                        % (len(rows) - 1, len(items)))
    csv_nos = [r[0] for r in rows[1:]]
    if csv_nos != [str(n) for n in nos]:
        problems.append("CSV 序号与 JSON 不一致")

    # 统计
    from collections import Counter
    cv = Counter(i["verdict"] for i in items)
    cl = Counter(i["level"] for i in items)
    print("== 数据完整性 ==")
    print("  条数        : %d" % len(items))
    print("  判定分布    : ok=%d fix=%d doubt=%d dup=%d"
          % (cv["ok"], cv["fix"], cv["doubt"], cv["dup"]))
    print("  证据等级    : A=%d B=%d C=%d" % (cl["A"], cl["B"], cl["C"]))
    print("  JSON / CSV  : %d / %d 行" % (len(items), len(rows) - 1))

    if problems:
        print("  结论        : 失败，%d 个问题" % len(problems))
        for p in problems:
            print("    ! %s" % p)
        return 1
    print("  结论        : 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
