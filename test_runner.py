#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令 Trie 匹配器的自动测试运行器。

它评估：
1) 精确匹配
2) Trie.match_fuzzy_sub1 实现的模糊匹配（单字符替换）

输入数据集格式 (TSV, UTF-8)：
<asr_文本>\t<期望_命令>

示例：
关闭空调啊\t关闭空调
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from tool import load_commands_from_file, normalize_asr, strip_tail_particle
from voice_trie import Trie


@dataclass
class CaseResult:
    raw: str
    expected: str
    normalized: str
    predicted: Optional[str]
    mode: str
    latency_ms: float
    ok: bool


def build_trie(commands_file: str, enable_length_check: bool = True) -> Tuple[Trie, Dict[str, str]]:
    """
    关键修复：构建 Trie 时也对命令词典做同样的 normalize_asr，保证“输入侧”和“词典侧”处在同一空间。
    同时返回 norm2raw 映射，用于把匹配到的归一化命令还原成原始命令（与测试集 expected 对齐）。
    """
    commands = load_commands_from_file(commands_file)

    trie = Trie()
    norm2raw: Dict[str, str] = {}
    norm_cmds: List[str] = []

    for cmd in commands:
        key = normalize_asr(cmd)
        norm_cmds.append(key)

        try:
            trie.insert(key, cmd)
        except TypeError:
            trie.insert(key)

        # 若多个原始命令归一化后冲突，默认保留第一个（你也可以改成打印 warning）
        norm2raw.setdefault(key, cmd)

    # 长度剪枝也要用归一化后的长度集合，否则会误剪掉（如 “关闭空调”(4) -> “关空调”(3)）
    trie.set_vaild_lens(norm_cmds)
    trie.set_length_check(enable_length_check)
    return trie, norm2raw


def predict(trie: Trie, norm2raw: Dict[str, str], raw: str) -> Tuple[str, Optional[str], float, str]:
    """返回 (模式, 预测结果, 延迟_ms, 归一化后的文本)。"""
    s = strip_tail_particle(raw.strip())
    s = normalize_asr(s)

    start = time.perf_counter()
    ans = trie.match_exact(s)
    mode = "exact"
    if not ans:
        ans = trie.match_fuzzy_sub1(s)
        mode = "fuzzy_sub1" if ans else "unrecognized"
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    # 把归一化的匹配结果映射回原始命令（与 TSV 中 expected 保持一致）
    pred = norm2raw.get(ans, ans) if ans else None
    return mode, pred, elapsed_ms, s


def iter_dataset(dataset_path: str) -> Iterable[Tuple[str, str]]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(
                    f"{dataset_path}:{line_no}: 预期有 2 列 TSV 数据 (输入\\t期望值)，但得到 {len(parts)} 列: {line!r}"
                )
            yield parts[0], parts[1]


def evaluate(trie: Trie, norm2raw: Dict[str, str], dataset_path: str) -> List[CaseResult]:
    results: List[CaseResult] = []
    for raw, expected in iter_dataset(dataset_path):
        mode, pred, latency_ms, normalized = predict(trie, norm2raw, raw)
        ok = (pred == expected)
        results.append(
            CaseResult(
                raw=raw,
                expected=expected,
                normalized=normalized,
                predicted=pred,
                mode=mode,
                latency_ms=latency_ms,
                ok=ok,
            )
        )
    return results


def summarize(results: List[CaseResult], title: str, show_failures: int = 20) -> None:
    total = len(results)
    correct = sum(1 for r in results if r.ok)
    acc = (correct / total * 100.0) if total else 0.0

    latencies = [r.latency_ms for r in results]
    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0)
    mx = max(latencies) if latencies else 0.0

    mode_counts = {}
    for r in results:
        mode_counts[r.mode] = mode_counts.get(r.mode, 0) + 1

    print(f"\n=== {title} ===")
    print(f"用例总数: {total}")
    print(f"匹配正确: {correct}")
    print(f"准确率: {acc:.2f}%")
    print(f"耗时 (ms): p50={p50:.3f}, p95={p95:.3f}, 最大值={mx:.3f}")
    print("匹配模式统计:", ", ".join(f"{k}={v}" for k, v in sorted(mode_counts.items())))

    failures = [r for r in results if not r.ok]
    if failures:
        print(f"\n前 {min(show_failures, len(failures))} 个失败用例:")
        for r in failures[:show_failures]:
            print(
                f"- 原始={r.raw!r} -> 归一化={r.normalized!r} | 期望={r.expected!r} | 预测={r.predicted!r} | 模式={r.mode} | {r.latency_ms:.3f}ms"
            )
    else:
        print("\n无失败用例 🎉")


def main() -> None:
    ap = argparse.ArgumentParser(description="语音命令 Trie 匹配器自动测试程序。")
    ap.add_argument(
        "--commands",
        default="commands.txt",
        help="命令词典文本文件路径（每行一个命令）。默认值：commands.txt",
    )
    ap.add_argument(
        "--datasets",
        nargs="+",
        default=[
            "test_dataset/dataset_extra_char.tsv",
            "test_dataset/dataset_extra_particle.tsv",
            "test_dataset/dataset_extra_char_and_particle.tsv",
        ],
        help="一个或多个 TSV 数据集。默认值：内置的 3 个数据集。",
    )
    ap.add_argument(
        "--no-length-check",
        action="store_true",
        help="禁用 Trie 长度剪枝 (Trie.set_length_check(False))。",
    )
    ap.add_argument(
        "--show-failures",
        type=int,
        default=20,
        help="每个数据集打印多少个失败用例。默认值：20",
    )
    args = ap.parse_args()

    trie, norm2raw = build_trie(args.commands, enable_length_check=(not args.no_length_check))

    all_results: List[CaseResult] = []
    for ds in args.datasets:
        res = evaluate(trie, norm2raw, ds)
        summarize(res, title=ds, show_failures=args.show_failures)
        all_results.extend(res)

    # Overall summary (across all datasets)
    if len(args.datasets) > 1:
        summarize(all_results, title="总计", show_failures=args.show_failures)


if __name__ == "__main__":
    main()
    input("\nDone. Press Enter to exit...")