---
name: office-doc-converter
description: Excel/Word/PPTなどのOfficeドキュメントをLLMに適した形式に変換するためのスキル。Word/PPTはレイアウトを保持したPDFへ、Excelはシート構造や表を意識したMarkdownへ変換し、埋め込み画像の抽出と内容のテキスト化を支援する。
---

# Officeドキュメント変換スキル

## 目的
- Word/PPT: レイアウト崩れを避けるためPDFへ変換する
- Excel: シートごとにMarkdownへ変換し、表情報やExcel方眼紙のレイアウト情報を残す
- 画像: 埋め込み画像をファイルとして分離し、Markdownからリンク。画像内容をClaudeで要約して補足する

## 推奨ツール/依存
- LibreOffice (`soffice`) でのPDF変換
- Python 3.11+、`pandas`、`openpyxl` でExcel→Markdown変換
- `python scripts/extract_office_images.py` で画像抽出 (docx/pptx/xlsx対応)
- `python scripts/excel_to_markdown.py` でMarkdown生成

## 変換ワークフロー
1) **入力確認**
   - 拡張子で判定: `.docx/.doc`、`.pptx/.ppt`、`.xlsx/.xls` など
   - 画像抽出用の出力ディレクトリを決める（例: `./output/media`）

2) **画像抽出** (必要に応じて最初に実施)
   - `python scripts/extract_office_images.py <input_file> <output_dir>`
   - 抽出結果は `<output_dir>/<basename>/` 以下に拡張子付きで保存される
   - Markdownからは `![説明](media/xxx.png)` として参照する
   - Claudeで各画像の内容を要約し、図版の意味や重要箇所をテキスト化する

3) **Word/PPT → PDF**
   - コマンド例: `soffice --headless --convert-to pdf --outdir <outdir> <input_file>`
   - 可能ならPDFをプレビューし、ページ抜けやレイアウト崩れがないか確認
   - 画像リンクはPDF内のままでOK。抽出済み画像がある場合は別途Markdownで補足する

4) **Excel → Markdown**
   - `python scripts/excel_to_markdown.py <input_excel> <output_md> [--media-dir <dir>]`
   - シートを見出しレベル2で分割し、テーブルをMarkdownで整形
   - Excel方眼紙らしさを残すため、以下をコメントとして追記:
     - 列数/行数が多い場合は「グリッド配置（Excel方眼紙）」を明記
     - セル結合があれば位置とサイズを記録
   - 画像を `--media-dir` で指定した場所へ抽出してリンクする

5) **最終Markdownの整形**
   - セクション順序: 概要 → 画像一覧 → シート別コンテンツ
   - 画像は `![title](path)` 形式で貼り、直後に内容要約を箇条書きで追加
   - 大きな表はコードブロック内に収めて改行や列幅を保持
   - シート間で情報が分離している場合は、関係性や参照元を脚注として追記

## スクリプトの使い方
### 画像抽出
```bash
python scripts/extract_office_images.py input.docx ./output/media
python scripts/extract_office_images.py slide deck.pptx ./output/media
python scripts/extract_office_images.py workbook.xlsx ./output/media
```
- 画像は `<media_dir>/<input_basename>/` にまとめて保存される

### Excel→Markdown
```bash
python scripts/excel_to_markdown.py workbook.xlsx workbook.md --media-dir ./output/media
```
- 生成Markdownではシート名を見出し化し、表をMarkdownテーブルで出力
- セル結合やExcel方眼紙の可能性をメタ情報としてコメント出力する
- 抽出した画像は `![SheetName-ImageN](relative/path.png)` としてリンク

## Claudeへのフィード時の注意
- PDFはそのまま添付、Markdownはテキストで貼付
- 画像は必ずリンク付きで添付し、テキスト要約を併記
- 数式や複雑な表はスクリーンショットを併用し、誤読防止のため原文抜粋を残す
- シート間参照や計算ロジックがある場合、依存関係を箇条書きで説明

## 品質チェックリスト
- [ ] すべてのシートがMarkdownに含まれている
- [ ] 抽出した画像が参照されている（リンク切れなし）
- [ ] Excel方眼紙/セル結合の存在を記載
- [ ] PDF出力後にページ欠落がない
- [ ] 重要なグラフや図版はテキストで補足されている
