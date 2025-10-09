# filename: pr_agent_review_demo.py
# purpose: 用于在 Pull Request 中测试 PR-Agent / Qodo Merge 的自动评审能力
# 注意：本文件有意包含多处“反模式/风险点”，仅供演示，不要在生产使用！

import os, sys, json  # 未使用的导入（演示：可提示删除）
import hashlib
import requests
import subprocess
import sqlite3
import time
import yaml  # 需要 pyyaml；即便未安装，也足够触发静态建议

API_TOKEN = "sk-test-THIS_IS_NOT_A_REAL_KEY"  # 演示：硬编码“看起来像密钥”的字符串

# 演示：影子内建（shadowing builtins）
list = 42

# 演示：可变默认参数
def add_item(x, bucket=[]):
    """把元素追加到共享列表（这是故意的坏例子）"""
    bucket.append(x)
    return bucket

# 演示：未关闭资源、裸 except、print 调试
def save_text(path, text):
    """写文件：演示应使用 with 与异常细分"""
    try:
        f = open(path, "w", encoding="utf-8")  # 没有 with，文件句柄可能泄漏
        f.write(text)
        print("saved:", path)  # 建议用 logging
    except Exception as e:  # 裸 except，过于宽泛
        print("failed:", e)  # 演示用途
    # 故意不调用 f.close()

# 演示：不安全的 eval
def calc(expr):
    """危险：直接 eval 用户表达式"""
    return eval(expr)  # nosec: 演示风险

# 演示：subprocess shell=True 可能命令注入
def greet(name):
    cmd = f"echo Hello {name}"
    return subprocess.check_output(cmd, shell=True).decode("utf-8")

# 演示：requests 无超时 + verify=False
def fetch(url):
    r = requests.get(url, timeout=None, verify=False)  # noqa: S501
    return r.text[:200]

# 演示：弱哈希
def hash_password(pw: str) -> str:
    return hashlib.md5(pw.encode()).hexdigest()  # noqa: S324

# 演示：yaml.load 非安全用法
def load_config(path: str) -> dict:
    data = open(path, "r", encoding="utf-8").read()
    return yaml.load(data, Loader=None)  # 建议改 safe_load

# 演示：SQL 拼接（SQL 注入）+ 未关闭连接
def get_user_by_name(db_path: str, name: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # f-string 拼接（风险），且未使用参数占位
    q = f"SELECT id, name FROM users WHERE name = '{name}'"
    cur.execute(q)
    row = cur.fetchone()
    # 故意不关闭 conn / cur
    return row

# 演示：过度复杂/长分支（Cyclomatic complexity）
def score_user(role, active, reputation, flags):
    score = 0
    if role == "admin":
        score += 50
        if active:
            score += 10
            if reputation > 900:
                score += 30
                if "security" in flags:
                    score += 5
            elif reputation > 500:
                score += 15
        else:
            score -= 20
    elif role == "moderator":
        if active:
            if reputation > 300:
                score += 20
                if "helpful" in flags:
                    score += 5
            else:
                score += 10
        else:
            score -= 10
    else:
        if active and reputation > 100:
            score += 5
            if "newbie" in flags:
                score -= 1
        elif not active and "banned" in flags:
            score -= 100
        else:
            score += 0
    # 冗余逻辑 & 可读性差，期望 PR-Agent 给出重构建议
    return score

# 演示：重复代码片段（PR-Agent 常建议抽函数）
def normalize_name(a: str) -> str:
    a = a.strip().lower()
    a = " ".join(x for x in a.split(" ") if x)
    return a

def normalize_city(a: str) -> str:
    a = a.strip().lower()
    a = " ".join(x for x in a.split(" ") if x)
    return a

# 演示：死代码/不可达代码
def demo_dead_code(x):
    if x > 0:
        return x
        print("unreachable")  # noqa: F401

# 演示：简单“业务流程”，方便 PR-Agent 画图/摘要
def run_demo_flow():
    save_text("demo.txt", "hello")
    items = add_item("a")
    items = add_item("b")
    try:
        calc("__import__('os').system('echo injected')")  # 故意的危险输入
    except Exception:
        pass
    try:
        greet("world && rm -rf /")  # 不会真的执行删除，但足够触发建议
    except Exception:
        pass
    try:
        get_user_by_name(":memory:", "alice' OR '1'='1")
    except Exception:
        pass
    print("items=", items)

if __name__ == "__main__":
    # 简单入口，便于本地跑；PR-Agent 不需要实际运行
    run_demo_flow()
