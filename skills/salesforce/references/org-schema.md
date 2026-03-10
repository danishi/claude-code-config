# Org スキーマリファレンス

このファイルには接続先orgのオブジェクト定義を記載する。
各オブジェクトのフィールド一覧・選択リスト値・リレーションを管理し、SOQLクエリの組み立てやレコード作成時に参照する。

## スキーマの取得方法

以下のコマンドでオブジェクトのメタデータを取得し、このファイルに追記する：

```bash
# オブジェクト一覧の取得
sf api request rest /services/data/vXX.0/sobjects

# 特定オブジェクトのフィールド定義を取得
sf api request rest /services/data/vXX.0/sobjects/Account/describe
sf api request rest /services/data/vXX.0/sobjects/Opportunity/describe
```

## テンプレート

以下のフォーマットで各オブジェクトの情報を記載する：

---

### ObjectName (ラベル)

#### 標準フィールド（よく使うもの）

| API名 | ラベル | 型 | 備考 |
|--------|--------|------|------|
| Name | 名前 | string | |
| ... | ... | ... | ... |

#### カスタムフィールド

| API名 | ラベル | 型 | 備考 |
|--------|--------|------|------|
| CustomField__c | カスタム | string | |
| ... | ... | ... | ... |

#### ピックリスト値

**FieldName__c:**
`値1`, `値2`, `値3`

#### よく使うクエリ

```sql
SELECT Id, Name FROM ObjectName ORDER BY Name
```

---

## オブジェクト定義

（ここに `sf api request rest` の結果を元にオブジェクト定義を追記していく）

---

## リレーション図

（オブジェクト間のリレーションをテキストで記載する）

```
Account (取引先)
 ├── Opportunity (商談) [AccountId → Account]
 └── Contact (取引先責任者) [AccountId → Account]
```
