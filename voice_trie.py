import time

from tool import *

# 字典树节点
class TrieNode:
    def __init__(self):
        # children: 字符 -> 子节点
        self.children = {}
        # is_end: 是否是一条指令的结尾
        self.is_end = False
        # 存储完整指令（仅在结尾节点有值）
        self.word = None


# 字典树
class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.valid_lens = []
        self.enable_length_check = True

    def insert(self, word: str, value: str = None):
        """把一条指令插入 Trie
        word: 用于匹配的key（建议放归一化后的指令）
        value: 命中后返回的原始指令（默认=word）
        """
        if value is None:
            value = word

        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.word = value
        
    def set_vaild_lens(self, len_sets):
        """设置指令长度集"""
        self.valid_lens = set(len(length) for length in len_sets)
        
    def set_length_check(self, status: bool):
        """设置是否启用长度检查(默认开启)"""
        self.enable_length_check = status
        
    def match_exact(self, text: str) -> bool:
        """精确匹配：完全一致才返回 True"""
        
        if self.enable_length_check == True:
            if len(text) not in self.valid_lens:
                return None
        
        node = self.root
        for ch in text:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node.word if node.is_end else None
    
    def match_fuzzy_sub1(self, text: str):
        """
        DFS递归实现模糊搜索
        - 允许 1 次编辑
          1) 多一个字符 -> 跳过该字符(删除一次)
          2) 或者做一次替换
        - 返回匹配到的指令文本，否则 None
        """
        
        if self.enable_length_check == True:
            # 允许比指令多一个字
            if (len(text) not in self.valid_lens) and (len(text) -1 not in self.valid_lens):
                return None
        
        def dfs(node: TrieNode, i: int, used_error: int):
            # used_error: 已经使用的错误次数（0 或 1）

            # 剪枝：超过 1 次错误直接失败
            if used_error > 1:
                return None
            
            # 如果输入字符走完了
            if i == len(text):
                return node.word if node.is_end else None
            
            cur = text[i]
            
            # 1) 优先走“正常匹配分支”（不增加错误次数）
            if cur in node.children:
                res = dfs(node.children[cur], i + 1, used_error)
                if res:
                    return res
                
            # 2) 如果还没增加过错误次数，尝试“跳过当前字符”（相当于删除一次）
            if used_error == 0:
                res = dfs(node, i + 1, 1)
                if res:
                    return res
                
                for ch, child in node.children.items():
                    if ch == cur:
                        continue  # 相同的分支已经试过了
                    res = dfs(child, i + 1, 1)
                    if res:
                        return res
            
            return None
            
        return dfs(self.root, 0, 0)
            

def main():    
    commands = load_commands_from_file("commands.txt")
    
    print(f"已从文件加载 {len(commands)} 条指令：")
    for c in commands:
        print(" -", c)
        
    trie = Trie()

    norm_cmds = []
    for cmd in commands:
        norm = normalize_asr(cmd)
        norm_cmds.append(norm)
        trie.insert(norm, cmd)   # key=归一化后的指令，value=原始指令

    trie.set_vaild_lens(norm_cmds)

    print("=== Step：精确 + 模糊(替换≤1) ===")
    print("提示：先精确匹配，失败再模糊匹配。输入 exit 退出。")

    while True:
        raw = input(">>> ").strip()
        if raw == "exit":
            break
        
        s = strip_tail_particle(raw)
        s = normalize_asr(s)

        # 开始计时
        start_time = time.perf_counter()

        # 先精确匹配
        ans = trie.match_exact(s)
        mode = "精确匹配"

        # 精确失败再模糊匹配
        if not ans:
            ans = trie.match_fuzzy_sub1(s)
            mode = "模糊匹配" if ans else "未识别"

        # 结束计时
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 输出结果 + 延迟
        if ans:
            print(f"识别结果：{ans}")
            print(f"匹配方式：{mode}")
            print(f"识别延迟：{elapsed_ms:.2f} ms")
        else:
            print("识别结果：未识别")
            print(f"识别延迟：{elapsed_ms:.2f} ms")


if __name__ == "__main__":
    main()
