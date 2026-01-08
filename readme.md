# LiteVoiceTrie

**本Markdown由AI生成**

一个轻量级的中文语音指令匹配器，可在嵌入式硬件上运行：

* 支持**精确匹配**
* 支持**一次编辑容错**的模糊匹配（允许“多一个字”被跳过，或“替换一个字”）
* 提供**归一化**（ASR 同义表达/拆字合并等）与**末尾语气词**剥离
* 附带测试数据生成与自动化评测脚本

> 适用于：智能家居/车机/语音助手等，将 ASR 文本映射到“合法指令词典”。

该项目主要作为该方向的一个模板使用，可以在此项目的基础上进行功能强化

---

## Features

* **Command dictionary**：每行一条合法指令（示例包含：开灯、关灯、停止、调高/调低音量、打开/关闭空调等）。
* **ASR normalization**：去空格、拆字合并、同义短语替换（如 “打开X→开X”，“关闭X→关X” 等，可扩展）。
* **Tail particle stripping**：去掉末尾一个语气词（啊/呀/吧/呢/哦/哈/嘛/哇）。
* **Trie exact match + fuzzy match (sub1)**：精确失败后再做一次编辑容错搜索（跳过一个字或替换一个字）。
* **Length pruning**：可选“长度剪枝”加速（默认开启，也可关闭）。 
* **Auto tests**：提供评测器统计准确率、延迟（p50/p95/max）并打印失败样例。
* **Synthetic datasets**：生成三类常见噪声数据集（插入一个多余字、末尾加语气词、两者叠加）。

---

## File Layout

* `commands.txt`：指令词典（每行一条）
* `tool.py`：通用工具（指令加载、归一化、去语气词）
* `voice_trie.py`：Trie 实现 + 交互式演示入口（精确/模糊匹配）
* `gen_testdata.py`：生成测试数据集（TSV）
* `test_runner.py`：自动化评测脚本（统计准确率/延迟/失败样例）
* `dataset_extra_char.tsv` / `dataset_extra_particle.tsv` / `dataset_extra_char_and_particle.tsv`：示例数据集（TSV）

---

## Requirements

* Python 3.13+（仅标准库）

---

## Quick Start

### 1) 运行交互式匹配器

```bash
python voice_trie.py
```

按提示输入 ASR 文本，程序会：

1. 去末尾语气词
2. 归一化
3. 先精确匹配，失败再做模糊匹配
   输入 `exit` 退出。 

示例（你的词典里包含“关闭空调”）：

* 输入：`关闭空调啊` → 输出：`关闭空调`（去掉语气词）
* 输入：`关闭空个调` → 输出：`关闭空调`（多一个字，模糊匹配跳过）

---

### 2) 生成测试数据集

进入test_dataset文件夹

```bash
python gen_testdata.py
```

将从 `commands.txt` 随机采样并生成 3 份 TSV：

* `dataset_extra_char.tsv`：在命令中随机插入一个“多余字”（如“请/帮/给/先/快/把/下/个/点/来”）
* `dataset_extra_particle.tsv`：命令末尾追加一个语气词（啊/呀/吧/呢/哦/哈/嘛/哇）
* `dataset_extra_char_and_particle.tsv`：插入多余字 + 追加语气词

TSV 每行格式：
`input<TAB>expected`（UTF-8）

---

### 3) 运行自动化评测

#### 使用自带的数据集

```
python test_runner.py
```



> 注意：`test_runner.py` 的默认数据集路径是 `test_dataset/...`。如果你的 TSV 在当前目录（如本仓库示例），请显式传参 `--datasets`。

#### 使用当前目录下的数据集

```bash
python test_runner.py \
  --commands commands.txt \
  --datasets dataset_extra_char.tsv dataset_extra_particle.tsv dataset_extra_char_and_particle.tsv
```

常用参数：

* `--no-length-check`：禁用长度剪枝
* `--show-failures N`：每个数据集最多打印 N 条失败样例

评测输出包含：用例数、正确数、准确率、延迟（p50/p95/max）、模式统计（exact / fuzzy_sub1 / unrecognized）等。

---

## How It Works

### Normalization（归一化）

`normalize_asr()` 做了几类常见处理：

* 去空格
* 拆字合并（例如把“打 x 开”合并成“打开”，把“关 x 闭”合并成“关闭”，以适配 ASR 断字情况）
* 同义短语替换（按顺序先长后短），例如：

  * 打开/开启/启动 → 开
  * 关闭/关掉/停用 → 关 

### Tail particle stripping（去末尾语气词）

`strip_tail_particle()` 最多去掉末尾 1 个语气词字符（啊/呀/吧/呢/哦/哈/嘛/哇）。

### Trie matching（匹配）

* **精确匹配**：完全一致才命中。
* **模糊匹配（一次编辑）**：在 DFS 中允许最多一次“错误”：

  1. **删除一次**：输入多了一个字 → 跳过该字继续匹配
  2. **替换一次**：当前字不匹配 → 尝试走其它子分支并记一次错误

### Length check（长度剪枝）

默认开启：

* 精确匹配要求输入长度在“词典长度集合”内
* 模糊匹配允许输入长度等于词典长度或词典长度 + 1（因为允许“多一个字”） 

---

## Customize

1. **扩充指令**：编辑 `commands.txt`，每行一条指令。
2. **扩展归一化规则**：在 `tool.py` 的 `normalize_asr()` 中补充映射/替换规则。
3. **扩展语气词集合**：在 `strip_tail_particle()` 中调整字符集合。
4. **更多噪声类型的测试集**：在 `gen_testdata.py` 中添加新的扰动生成逻辑。

---

## Notes

* `test_runner.py` 在构建 Trie 时会对“词典侧”和“输入侧”做同样的 `normalize_asr()`，并维护 `norm2raw` 映射以保证评测时能对齐原始命令文本。

~~这同时也是我自己的《算法设计与分析实践》课程设计~~

