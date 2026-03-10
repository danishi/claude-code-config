---
name: salesforce
description: >
  Salesforce CLIを使ってSalesforceのデータ操作・管理を行うスキル。
  取引先・商談・プロジェクト・外注管理のCRUD操作、SOQLクエリ、パイプライン分析、レポート生成を実行する。
  ユーザーがSalesforceのデータを照会・更新・分析したいとき、商談のステージを確認・変更したいとき、
  プロジェクトや外注の状況を確認したいとき、売上・粗利・パイプラインのレポートが必要なとき、
  取引先や案件の情報を調べたいとき、SOQLクエリを実行したいときに使用する。
  「Salesforce」「SF」「商談」「取引先」「パイプライン」「案件」「プロジェクト」「外注」「粗利」
  「売上」「受注」「失注」「ステージ」「SOQL」などのキーワードが含まれる場合はこのスキルを使う。
  Salesforceに関する質問や操作依頼であれば、明示的にスキル名を言及していなくても積極的にこのスキルを使用すること。
---

# Salesforce 操作スキル

Salesforce CLI (`sf`) を使い、接続先 org のデータ操作・分析・管理を行う。

## 初回セットアップ

このスキルを使用する前に、`references/org-config.md` を作成して組織固有の情報を設定する必要がある。

### org-config.md のテンプレート

```markdown
# Org 設定

| 項目 | 値 |
|------|-----|
| Instance URL | https://your-org.my.salesforce.com |
| API Version | 63.0 |
| Alias | your-alias |
| Default User | user@example.com |

## ビジネスコンテキスト

（このorgのビジネス概要を記述。例: SaaS製品の営業管理、製造業の受発注管理 など）
```

設定ファイルが存在しない場合は、ユーザーに作成を案内すること。

## 接続とアーキテクチャ

### 認証の確認

操作を始める前に、まず接続状態を確認する。

```bash
sf org display --json
```

- デフォルトorgが設定済みであればそのまま使用する
- 接続が切れている場合は `sf org login web` でブラウザ認証を案内する
- デフォルトorgが未設定の場合はユーザーにどうするか確認する

### コマンドの使い分け

Salesforce CLIには2つの主要なデータアクセス方法がある。状況に応じて使い分ける。

- **`sf data query`** — SOQLクエリの実行。`--json` フラグで構造化データを取得。結果は `.result.records` に格納される
- **`sf api request rest`** — REST API直接呼び出し。describe（メタデータ取得）やTooling API呼び出しに使う。結果の形式が異なる点に注意（配列やオブジェクトが直接返る）

orgによっては一部のsObjectタイプ（ApexClass, Organization等）がSOQL経由でアクセスできない制約がある。メタデータが必要な場合はREST APIの `/sobjects/<Object>/describe` を使用すること。

## データモデル

`references/org-schema.md` にオブジェクトごとのフィールド一覧・選択リスト値・リレーションを記載している。
SOQLクエリを組み立てるときやレコードを作成するときに参照すること。

スキーマファイルが未作成の場合は、`sf api request rest /services/data/vXX.0/sobjects/<Object>/describe` でメタデータを取得し、作成を支援する。

## 取引先（Account）登録ルール

### 登録時の標準フィールド

取引先を新規登録する際は、以下のフィールドを可能な限り埋める：

| フィールド | API名 | 重要度 | 調査方法 |
|-----------|-------|--------|---------|
| 取引先名 | Name | ◎必須 | 正式名称（前株/後株を含む） |
| Webサイト | Website | ○推奨 | 公式サイトURL |
| 請求先住所 | BillingStreet/City/State/PostalCode/Country | ○推奨 | 本社所在地 |
| 電話番号 | Phone | ○推奨 | 代表電話番号 |
| 業種 | Industry | ○推奨 | ピックリスト値から最適なもの |

**注:** orgにカスタム必須フィールドがある場合は `references/org-schema.md` を参照して対応すること。

### 正式名称の確認

会社名は必ず「前株」（株式会社〇〇）か「後株」（〇〇株式会社）を含む正式名称で登録する。
ユーザーから略称や株式会社なしで渡された場合は WebSearch で正式名称を調査すること。

### 重複チェック

登録前に必ず既存取引先との重複を確認する：

```bash
sf data query --query "SELECT Id, Name FROM Account ORDER BY Name" --json
```

同一企業がユーザーのリスト内に複数回含まれている場合は重複を除外し、既に登録済みの企業はスキップする旨をユーザーに報告する。

### 一括登録の手順

複数の取引先を一度に登録する場合：

1. ユーザーから会社名リストを受け取る
2. 重複チェック（既存取引先との照合 + リスト内の重複除去）
3. 各社の正式名称・前株後株を WebSearch で調査
4. Webサイト・本社住所・代表電話番号を WebSearch で調査
5. 登録内容一覧を Markdown テーブルで提示し、ユーザー承認を得る
6. 承認後、`sf data create record` で登録（5件ずつ並列実行）
7. 最終確認の SOQL クエリで登録結果を表示

```bash
# 取引先作成の例
sf data create record --sobject Account --values "Name='株式会社サンプル' Website='https://www.example.co.jp/' BillingCity='千代田区' BillingState='東京都' BillingCountry='日本' Industry='Technology'" --json
```

### 住所フィールドの分割ルール

| フィールド | 格納する内容 | 例 |
|-----------|------------|-----|
| BillingPostalCode | 郵便番号（ハイフン付き） | `102-0093` |
| BillingCountry | 国名 | `日本` |
| BillingState | 都道府県 | `東京都` |
| BillingCity | 市区郡（政令市は区まで） | `千代田区` / `大阪市北区` |
| BillingStreet | 町名・番地・ビル名 | `平河町2-16-1 平河町森タワー` |

## 商談（Opportunity）登録ルール

### 商談名の命名規則

商談名の命名規則はorgごとに異なる。`references/org-config.md` に命名規則が記載されている場合はそれに従う。記載がない場合はユーザーに確認すること。

### 問い合わせからの商談登録フロー

問い合わせ情報から商談を登録する場合、以下の手順で一括処理する：

1. **取引先の確認・登録**: 既存取引先を検索し、なければ新規登録（取引先登録ルールに従う）
2. **取引先責任者の登録**: Contact を作成し、取引先に紐づける
3. **商談の作成**: 命名規則に従い商談を作成
   - 初期ステージはorgのステージ値を確認して設定する
4. **取引先責任者の紐づけ**: `OpportunityContactRole` で商談と取引先責任者を関連付ける（`IsPrimary=true`）
5. **所有者の設定**: 指定がある場合、取引先・取引先責任者・商談すべてに同じ所有者（OwnerId）を設定する

```bash
# OpportunityContactRole の作成例
sf data create record --sobject OpportunityContactRole --values "OpportunityId='006XXXXXXXXXXXX' ContactId='003XXXXXXXXXXXX' IsPrimary=true" --json
```

## 操作パターン

### 1. データ参照（SOQLクエリ）

SOQLクエリは `sf data query` で実行する。必ず `--json` を付けて構造化データとして受け取る。

```bash
sf data query --query "SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity ORDER BY CloseDate DESC LIMIT 10" --json
```

**クエリのコツ:**
- 日本語の値はシングルクォートで囲む（例: `WHERE StageName = '05-受注'`）
- リレーション先のフィールドを取得する場合、REST APIの方が確実：
  ```bash
  sf api request rest '/services/data/vXX.0/query?q=SELECT+Id,Name,Account.Name+FROM+Opportunity'
  ```
- `COUNT()` クエリも使用可能: `SELECT count() FROM Opportunity WHERE IsClosed = false`
- 大量データの場合は `LIMIT` を適切に設定する

**結果の処理:**
`sf data query --json` の結果は以下の構造：
```json
{
  "status": 0,
  "result": {
    "records": [...],
    "totalSize": 10,
    "done": true
  }
}
```

### 2. レコード作成

レコード作成は **必ずユーザーに確認してから** 実行する。作成する内容を事前に表示し、承認を得ること。

```bash
sf data create record --sobject Account --values "Name='新規取引先'" --json
```

複数フィールドの場合はスペース区切りで `--values` に渡す。参照フィールド（lookup/master-detail）はIDを指定する。

### 3. レコード更新

レコード更新も **必ずユーザーに確認してから** 実行する。変更前の値と変更後の値を両方表示すること。

```bash
sf data update record --sobject Opportunity --record-id 006XXXXXXXXXXXX --values "StageName='Closed Won'" --json
```

**ステージ変更の場合:**
商談ステージを変更する際は、現在のステージも合わせて表示する。有効なステージ値は `references/org-schema.md` を参照すること。

### 4. レコード削除

レコード削除は **特に慎重に** 確認する。削除対象のレコード内容を詳細に表示し、関連レコードへの影響も説明した上で、明確な承認を得ること。

```bash
sf data delete record --sobject Account --record-id 001XXXXXXXXXXXX --json
```

### 5. 一括操作

複数レコードの操作にはCSVを使ったバルク操作が効率的。

```bash
# CSVからインポート
sf data import tree --sobject Account --files /path/to/accounts.json --json

# バルクアップサート
sf data upsert bulk --sobject Account --file /path/to/accounts.csv --external-id Id --json
```

一括操作は影響範囲が大きいため、必ず対象件数と操作内容を事前に明示する。

## レポート・分析パターン

ユーザーからレポートや分析を求められた場合、SOQLでデータを取得し、整形して表示する。

### パイプラインレポート

```bash
# 進行中の商談一覧
sf data query --query "SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity WHERE IsClosed = false ORDER BY CloseDate" --json
```

結果をステージ別にグルーピングし、金額のサマリーも合わせて表示する。

### プロジェクト状況レポート

カスタムオブジェクトを使用する場合は `references/org-schema.md` のフィールド定義を参照してクエリを組み立てる。

## メタデータ操作

オブジェクトのフィールド一覧やリレーションを確認するにはdescribeを使う。

```bash
sf api request rest /services/data/vXX.0/sobjects/Opportunity/describe
```

結果から `fields` 配列を取得し、`name`, `label`, `type`, `picklistValues` などを参照する。

**API Versionは `references/org-config.md` に記載されている値を使用すること。未設定の場合は最新バージョンを使用する。**

## 安全ガイドライン

- **参照操作（query/describe）** はユーザーの指示に基づき自由に実行してよい
- **作成（create）・更新（update）操作** は実行前に必ず内容を表示してユーザーの承認を得る
- **削除（delete）操作** は影響範囲を十分に説明し、明確な承認を得てから実行する
- **一括操作** は対象件数と操作内容を事前に明示し、承認を得る
- 本番orgの場合は大規模な変更やメタデータ変更は特に慎重に扱う
- アクセストークンやセンシティブな情報を出力に含めないよう注意する

## 出力フォーマット

- 一覧データは Markdownテーブル で整形して表示する
- 金額は日本円（¥）、3桁カンマ区切りで表示する
- 日付は `YYYY/MM/DD` 形式で表示する
- レコード件数が多い場合はサマリーを先に表示し、詳細は必要に応じて展開する
- SOQLクエリの実行結果だけでなく、ビジネス的な解釈や示唆も可能な範囲で添える
