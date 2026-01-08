def strip_tail_particle(text: str) -> str:
        """去掉末尾一个常见语气词（最多去 1 个字）"""
        particles = set("啊呀吧呢哦哈嘛哇") 
        if text and text[-1] in particles:
            return text[:-1]
        return text
    
def load_commands_from_file(filename: str):
    """
    从文本文件中逐行读取指令
    每一行表示一条合法指令
    """
    commands = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            cmd = line.strip()  # 去掉换行符和首尾空格
            if cmd:             # 跳过空行
                commands.append(cmd)

    return commands

def normalize_asr(text: str) -> str:
    """
    把 ASR 输出归一化成“更接近指令词典”的形式
    这里先做最常见的同义表达：
    - 打开X -> 开X
    - 关闭X -> 关X
    你可以继续扩展更多规则
    """
    text = "".join(text.split())  # 去空格
    pairs = {("打", "开"): "打开", ("关", "闭"): "关闭"} # (映射表)常见拆字合并
    
    if len(text) >= 3:
        out = []
        i = 0
        while i < len(text):
            if i + 2 < len(text) and (text[i], text[i+2]) in pairs:
                out.append(pairs[(text[i], text[i+2])])
                i += 3
                continue
            out.append(text[i])
            i += 1
        text = "".join(out)

    # 常用同义短语替换（顺序很重要：先替换长的，再替换短的）
    verb_map = [
        ("打开", "开"),
        ("开启", "开"),
        ("启动", "开"),
        ("关闭", "关"),
        ("关掉", "关"),
        ("停用", "关"),
    ]

    for old, new in verb_map:
        text = text.replace(old, new)

    return text
