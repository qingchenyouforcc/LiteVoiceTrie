import random

def load_commands(path="commands.txt"):
    cmds = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            c = line.strip()
            if c:
                cmds.append(c)
    return cmds

EXTRA_WORDS = ["请", "帮", "给", "先", "快", "把", "下", "个", "点", "来"]
PARTICLES = ["啊", "呀", "吧", "呢", "哦", "哈", "嘛", "哇"]

def insert_one_char(cmd: str, extra: str) -> str:
    """在 cmd 中随机位置插入一个字（尽量不插在末尾，避免太奇怪）"""
    if len(cmd) == 1:
        return cmd + extra
    pos = random.randint(0, max(0, len(cmd)-1))
    return cmd[:pos] + extra + cmd[pos:]

def gen_extra_char_dataset(commands, k=20, seed=1):
    random.seed(seed)
    data = []
    for _ in range(k):
        cmd = random.choice(commands)
        extra = random.choice(EXTRA_WORDS)
        inp = insert_one_char(cmd, extra)
        data.append((inp, cmd))
    return data

def gen_particle_dataset(commands, k=20, seed=2):
    random.seed(seed)
    data = []
    for _ in range(k):
        cmd = random.choice(commands)
        p = random.choice(PARTICLES)
        inp = cmd + p
        data.append((inp, cmd))
    return data

def gen_char_and_particle_dataset(commands, k=20, seed=3):
    random.seed(seed)
    data = []
    for _ in range(k):
        cmd = random.choice(commands)
        extra = random.choice(EXTRA_WORDS)
        p = random.choice(PARTICLES)
        inp = insert_one_char(cmd, extra) + p
        data.append((inp, cmd))
    return data

def save_dataset(data, path):
    # 每行：input<TAB>expected
    with open(path, "w", encoding="utf-8") as f:
        for inp, exp in data:
            f.write(f"{inp}\t{exp}\n")

def print_dataset(name, data, n=10):
    print(f"\n=== {name} (show {min(n,len(data))}/{len(data)}) ===")
    for inp, exp in data[:n]:
        print(f"{inp} -> {exp}")

def main():
    commands = load_commands("commands.txt")  # 你用自己的指令文件即可
    d1 = gen_extra_char_dataset(commands, k=30)
    d2 = gen_particle_dataset(commands, k=30)
    d3 = gen_char_and_particle_dataset(commands, k=30)

    print_dataset("Dataset1: extra_char", d1)
    print_dataset("Dataset2: extra_particle", d2)
    print_dataset("Dataset3: extra_char_and_particle", d3)

    save_dataset(d1, "dataset_extra_char.tsv")
    save_dataset(d2, "dataset_extra_particle.tsv")
    save_dataset(d3, "dataset_extra_char_and_particle.tsv")
    print("\nSaved to:")
    print("- dataset_extra_char.tsv")
    print("- dataset_extra_particle.tsv")
    print("- dataset_extra_char_and_particle.tsv")

if __name__ == "__main__":
    main()
