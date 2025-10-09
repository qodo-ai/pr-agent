# 只用于演示代码质量问题，请勿用于生产
import os, sys  # 未使用的导入（unused-import）
from typing import Any

SETTINGS = {"retry": 3}  # 可变全局状态（建议只读常量或配置对象）

def add_item(x, bucket=[]):  # 可变默认参数（mutable-default）
    bucket.append(x)
    return bucket

def normalize_name(s):  # 重复代码片段（与 normalize_city）-> 建议抽成公共函数
    s = s.strip().lower()
    s = " ".join(x for x in s.split(" ") if x)
    return s

def normalize_city(s):
    s = s.strip().lower()
    s = " ".join(x for x in s.split(" ") if x)
    return s

def compute_score(user: dict) -> int:
    """复杂度过高（深嵌套 + 魔法数），适合重构为早返回/卫语句/映射表"""
    score = 0
    if user.get("role") == "admin":
        if user.get("active"):
            if user.get("reputation", 0) > 900:  # 魔法数
                score += 30
            elif user.get("reputation", 0) > 500:
                score += 15
        else:
            score -= 20
    elif user.get("role") == "moderator":
        if user.get("active"):
            if user.get("reputation", 0) > 300:
                score += 20
            else:
                score += 10
        else:
            score -= 10
    else:
        if user.get("active") and user.get("reputation", 0) > 100:
            score += 5
        elif not user.get("active") and user.get("warnings", 0) > 3:
            score -= 100
        else:
            score += 0  # 无意义分支
    return score

def do_stuff(path: str, content: str) -> None:
    """缺少日志体系、异常粒度过粗；print 调试（建议 logging）"""
    print("writing:", path)  # T201 (ruff): print 语句
    f = open(path, "w", encoding="utf-8")  # 未使用 with 管理资源
    try:
        f.write(content)
    except Exception as e:  # 裸 except（broad-except）
        print("error:", e)
    # 故意不 close

def silly_api(a, b, c, d, e, f, g):  # 参数过多（long parameter list）
    """演示：过长行、命名不一致、类型缺失"""
    long_line = "x" * 150  # 超过 120 列的长行
    return a + b + c + d + e + f + g  # 无类型/边界校验

def dead_code(x: int) -> int:
    if x > 0:
        return x
        print("unreachable")  # 不可达代码
    return 0

class BadNames:  # 命名不规范/职责不清
    def __init__(self):
        self.tmp = []  # 模糊字段名
    def do(self, a: Any, b: Any):  # 职责不单一
        if a == b or (a != b and (a is not None or b is None)):
            print("weird condition")  # 复杂布尔表达式
        self.tmp.append(a); self.tmp.append(b)  # 一行多语句
