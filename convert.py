#!/usr/bin/env python3
"""
typ2md.py  ―  Typstソース → README.md 変換スクリプト
使い方:
    python typ2md.py junshinhiroo_rules.typ > README.md
    python typ2md.py junshinhiroo_rules.typ README.md   # ファイルに書き出す
"""

import re
import sys


# ── ユーティリティ ─────────────────────────────────────────

def extract_bracket_content(s: str) -> str:
    """最外側の [ ... ] の中身を返す（入れ子対応）"""
    depth = 0
    start = s.find("[")
    if start == -1:
        return s.strip()
    for i, ch in enumerate(s[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return s[start + 1:i]
    return s[start + 1:].strip()


def extract_paren_args(s: str) -> list[str]:
    """
    #bullets([aaa], [bbb], ...) のような引数リストを
    ['aaa', 'bbb', ...] として返す（入れ子対応）
    """
    start = s.find("(")
    if start == -1:
        return []
    depth = 0
    items: list[str] = []
    buf = ""
    for ch in s[start + 1:]:
        if ch == "(" or ch == "[":
            depth += 1
            buf += ch
        elif ch == ")" or ch == "]":
            if depth == 0:
                item = buf.strip().strip("[]").strip()
                if item:
                    items.append(item)
                break
            depth -= 1
            if depth == 0 and ch == "]":
                item = buf.strip()
                if item:
                    items.append(item)
                buf = ""
            else:
                buf += ch
        elif ch == "," and depth == 0:
            pass  # カンマはスキップ（区切りは ] で判断）
        else:
            buf += ch
    return items


# ── メインパーサー ─────────────────────────────────────────

def parse_typst(src: str) -> list[dict]:
    """
    Typstソースを走査し、構造を辞書リストに変換する。
    各要素: {"type": "title"|"chapter"|"section"|"article"|"pagebreak", ...}
    """
    nodes: list[dict] = []

    # コメント行を除去
    src = re.sub(r'//[^\n]*', '', src)

    # ── タイトル (#align + #text)
    for m in re.finditer(
        r'#align\s*\(\s*center\s*\)\s*\[\s*#text\([^)]*\)\s*\[([^\]]+)\]\s*\]',
        src, re.DOTALL
    ):
        nodes.append({"type": "title", "text": m.group(1).strip(), "pos": m.start()})

    # ── ページ区切り
    for m in re.finditer(r'#pagebreak\(\)', src):
        nodes.append({"type": "pagebreak", "pos": m.start()})

    # ── 章 (#chapter("N", "タイトル"))
    for m in re.finditer(r'#chapter\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', src):
        nodes.append({"type": "chapter", "num": m.group(1), "title": m.group(2), "pos": m.start()})

    # ── 節 (#section("タイトル"))
    for m in re.finditer(r'#section\(\s*"([^"]+)"\s*\)', src):
        nodes.append({"type": "section", "title": m.group(1), "pos": m.start()})

    # ── 条文 (#article[ ... ])
    # article ブロックを括弧の深さで正確に切り出す
    for m in re.finditer(r'#article\s*\[', src):
        start = m.end() - 1  # '[' の位置
        depth = 0
        end = start
        for i, ch in enumerate(src[start:], start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body_raw = src[start + 1:end]
        nodes.append({"type": "article", "body": body_raw.strip(), "pos": m.start()})

    # ── カウンターリセット (#article-counter.update(0))
    for m in re.finditer(r'#article-counter\.update\(0\)', src):
        nodes.append({"type": "counter_reset", "pos": m.start()})

    # ── Warningの置換
    for m in re.finditer(r'#warning(?:\([^)]*\))?\s*\[', src):
        start = m.end() - 1  # '[' の位置
        depth = 0
        end = start
        for i, ch in enumerate(src[start:], start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body_raw = src[start + 1:end]
        nodes.append({"type": "warning", "body": body_raw.strip(), "pos": m.start()})

    # 出現順にソート
    nodes.sort(key=lambda n: n["pos"])
    return nodes


def body_to_markdown(body: str) -> str:
    """
    article ボディ内の #bullets(...) を Markdown リストに変換し、
    残りのテキストをそのまま返す。
    """
    # #bullets([...], [...], ...) を検出
    bullets_pattern = re.compile(r'#bullets\s*\(', re.DOTALL)
    result = ""
    last = 0
    for m in bullets_pattern.finditer(body):
        # bullets の前のテキスト
        before = body[last:m.start()].strip()
        if before:
            result += before + "\n"
        # bullets の引数を取り出す
        start = m.end() - 1  # '(' の位置
        depth = 0
        end = start
        items_raw = []
        buf = ""
        i = start
        while i < len(body):
            ch = body[i]
            if ch == '(':
                depth += 1
                if depth > 1:
                    buf += ch
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    item = buf.strip().strip(',').strip()
                    if item:
                        items_raw.append(item)
                    end = i
                    break
                else:
                    buf += ch
            elif ch == '[' and depth == 1:
                # アイテム開始
                buf = ""
                depth_inner = 1
                i += 1
                while i < len(body):
                    c = body[i]
                    if c == '[':
                        depth_inner += 1
                        buf += c
                    elif c == ']':
                        depth_inner -= 1
                        if depth_inner == 0:
                            items_raw.append(buf.strip())
                            buf = ""
                            break
                        else:
                            buf += c
                    else:
                        buf += c
                    i += 1
            i += 1
        last = end + 1
        for item in items_raw:
            if item:
                result += f"- {item}\n"

    # 残りのテキスト
    tail = body[last:].strip()
    if tail:
        result += tail
    return result.strip()


def render_markdown(nodes: list[dict]) -> str:
    """ノードリストを Markdown 文字列に変換する"""
    lines: list[str] = []
    article_counter = 0
    in_bylaws = False  # 細則セクションかどうか

    for node in nodes:
        t = node["type"]

        if t == "title":
            text = node["text"]
            # スペース区切りのタイトルを詰める（例: "順 心 広 尾" → "順心広尾"）
            compact = text.replace(" ", "")
            if "細則" in compact:
                in_bylaws = True
                lines.append(f"\n---\n\n# {compact}\n")
            else:
                lines.append(f"# {compact}\n")

        elif t == "pagebreak":
            pass  # ページ区切りは Markdown では不要

        elif t == "counter_reset":
            article_counter = 0

        elif t == "chapter":
            num = node["num"]
            title = node["title"]
            lines.append(f"\n## 第{num}章　{title}\n")

        elif t == "section":
            title = node["title"]
            lines.append(f"\n### {title}\n")

        elif t == "article":
            article_counter += 1
            body_md = body_to_markdown(node["body"])
            lines.append(f"**第{article_counter}条**　{body_md}\n")
        
        elif t == "warning":
            content = body_to_markdown(node["body"])
            alert_box = (
                "> [!WARNING]\n"
                f"> {content}\n"
            )
            lines.append(alert_box)

    return "\n".join(lines)


# ── エントリポイント ──────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("使い方: python typ2md.py <input.typ> [output.md]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else None

    with open(input_path, encoding="utf-8") as f:
        src = f.read()

    nodes = parse_typst(src)
    md = render_markdown(nodes)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✓ {output_path} に書き出しました。", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()