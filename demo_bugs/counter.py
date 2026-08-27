# counter.py - 统计文本中每个单词出现次数
import sys


def count_words(text):
    words = text.lower().split()
    word_counts = {}
    for w in words:
        w = w.strip(".,;:!?\"'()")
        if not w:
            continue
        if w not in word_counts:
            word_counts[w] = 0
        word_counts[w] += 1
    return word_counts


def main():
    if len(sys.argv) < 2:
        print("用法: python counter.py <文件名>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    counts = count_words(text)
    for w in sorted(counts, key=lambda x: (-counts[x], x)):
        print(f"{w}: {counts[w]}")


if __name__ == "__main__":
    main()
