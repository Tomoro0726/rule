# コントリビューションガイド

このリポジトリへの貢献に興味を持っていただきありがとうございます。  
変更・修正を行う際は、以下のガイドラインをお読みください。

## 編集するファイルについて

**`README.md` は直接編集しないでください。**

このリポジトリでは `main.typ`（Typstソース）が唯一の正文です。  
`README.md` は `main.typ` から自動生成されるファイルであるため、直接編集しても次のビルド時に上書きされます。

```
main.typ  ←  ここを編集する
    ↓  自動変換（convert.py）
README.md  ←  直接編集しない
    ↓  自動ビルド（Typst）
main.pdf  ←  直接編集しない
```

## `main.typ` を編集する

テキストエディタまたは [Typst Web App](https://typst.app) で `main.typ` を編集してください。

**条文を追加する場合：**

```typst
#article[
  新しい条文の内容をここに記述する。
]
```

**箇条書きを含む条文の場合：**

```typst
#article[
  次の事項を定める。
  #bullets(
    [項目1],
    [項目2],
    [項目3],
  )
]
```

**章を追加する場合：**

```typst
#chapter("8", "新しい章のタイトル")
```

> 条文番号（第X条）は自動採番されます。番号を手動で書く必要はありません。

## ローカルで動作確認する（任意）

Typst がインストールされている場合、ローカルでPDFを確認できます。

```bash
# Typst のインストール（未インストールの場合）
brew install typst          # macOS
winget install typst.typst  # Windows
snap install typst          # Linux

# PDF生成
typst compile main.typ main.pdf

# README生成
python convert.py main.typ README.md
```

## プルリクエストを作成する

変更を push し、`main` ブランチへのプルリクエストを作成してください。

```bash
git add main.typ
git commit -m "fix: 第12条の誤字を修正"
git push origin fix/第12条-誤字修正
```

プルリクエストのタイトルには変更内容を簡潔に記載してください。  
マージ後、GitHub Actions が自動的に以下を実行します。

1. `README.md` を最新の `main.typ` から再生成
2. `main.pdf` をビルド
3. 新しいリリースとしてPDFを公開

---

## ファイル構成

| ファイル                      | 説明                            | 編集           |
| ----------------------------- | ------------------------------- | -------------- |
| `main.typ`                    | 規約・細則の本文（Typstソース） | 編集する       |
| `convert.py`                  | Typst → Markdown 変換スクリプト | 必要に応じて   |
| `.github/workflows/build.yml` | CI/CDワークフロー               | 必要に応じて   |
| `README.md`                   | 自動生成されるMarkdown版        | 直接編集しない |
| `main.pdf`                    | 自動生成されるPDF版             | 直接編集しない |

---

## コミットメッセージの規則

| プレフィックス | 用途                           |
| -------------- | ------------------------------ |
| `fix:`         | 誤字・脱字・内容の修正         |
| `feat:`        | 条文・章の新規追加             |
| `refactor:`    | 表現の整理（意味は変えない）   |
| `chore:`       | スクリプトやワークフローの変更 |

---

## 質問・提案

条文の内容に関する質問や提案は、GitHub の **Issues** からお知らせください。
