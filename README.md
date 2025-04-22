# Lancers Scraper

Lancersの案件情報を自動的にスクレイピングし、CSVファイルとして保存するツールです。

## 機能

- Lancersの案件検索と情報取得
- 以下の情報を収集：
  - 案件タイトル
  - 案件URL（https://www.lancers.jp/work/detail/[数字]）
  - 案件ID
  - 報酬
  - 案件種別（プロジェクト、コンペ、タスクなど）
  - 募集状態
  - 締切情報
- CSV形式でのデータ保存
- 環境変数による柔軟な設定
- ヘッドレスモードでの実行対応
- 詳細なログ出力

## 必要要件

- Python 3.8以上
- Google Chrome（Playwrightが自動的にインストール）

## インストール手順

1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/lancers-scraper.git
cd lancers-scraper
```

2. 仮想環境の作成と有効化
```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

4. Playwrightのブラウザインストール
```bash
playwright install
```

5. 環境変数の設定
```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env
# 必要に応じて.envの内容を編集
```

## 使用方法

### 基本的な使用方法

```bash
# 基本的な検索（ヘッドレスモードで実行）
python src/main.py --search-query "Python開発"

# 出力ファイル名を指定して検索
python src/main.py --search-query "Web開発" --output "web_dev_jobs.csv"

# ブラウザを表示して実行（デバッグ用）
python src/main.py --search-query "データ分析" --no-headless

# 案件詳細情報も取得
python src/main.py --search-query "動画編集" --with-details

# データ検索URLを使用してスクレイピング
python src/main.py --data-search

# プロジェクトデータ検索URLを使用してスクレイピング
python src/main.py --data-search-project
```

### コマンドラインオプション

- `-q`, `--search-query`: 検索クエリ（オプション）
- `-o`, `--output`: 出力ファイル名（オプション、指定しない場合は自動生成）
- `--no-headless`: ブラウザを表示して実行（デフォルト：非表示）
- `--with-details`: 案件詳細情報も取得（デフォルト：取得しない）
- `--data-search`: データ検索URLを使用してスクレイピングを行う（デフォルト：無効）
- `--data-search-project`: プロジェクトデータ検索URLを使用してスクレイピングを行う（デフォルト：無効）

## 設定

環境変数（.envファイル）で以下の設定が可能です：

### ブラウザ設定
- `HEADLESS`: ヘッドレスモードの有効/無効（true/false）
- `BROWSER_TIMEOUT`: ブラウザのタイムアウト時間（ミリ秒）
- `RETRY_COUNT`: リトライ回数
- `WAIT_TIME`: ページ読み込み待機時間（秒）

### スクレイピング設定
- `MAX_PAGES`: 取得する最大ページ数
- `ITEMS_PER_PAGE`: 1ページあたりの取得件数

## 出力データ

CSVファイルには以下の情報が含まれます：

- `title`: 案件タイトル
- `url`: 案件のURL
- `work_id`: 案件ID
- `price`: 報酬
- `type`: 案件種別
- `deadline`: 締切情報
- `status`: 募集状態
- `scraped_at`: スクレイピング実行日時

## 注意事項

1. 利用規約の遵守
   - Lancersの利用規約を必ず確認し、遵守してください
   - 過度なリクエストは避けてください

2. エラー処理
   - ネットワークエラーが発生した場合は自動的にリトライします
   - 長時間の実行時は`--headless=false`オプションで動作を確認することをお勧めします

3. データの保存
   - スクレイピングしたデータは`data/output`ディレクトリに保存されます
   - 古いデータは自動的には削除されないため、定期的な整理を推奨します

## ログ

- 実行ログは`scraping.log`に出力されます
- ログレベルは`INFO`がデフォルトです
- エラー発生時は詳細な情報が記録されます

## 開発者向け情報

### コードフォーマット
```bash
# コードフォーマット
black src tests

# import文の整理
isort src tests

# 型チェック
mypy src

# リンター実行
flake8 src tests
```

### テスト実行
```bash
# 全テストの実行
pytest

# 特定のテストファイルの実行
pytest tests/test_browser.py
```

## ライセンス

MITライセンス
