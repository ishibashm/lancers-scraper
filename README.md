# Lancers Scraper

Lancersの案件情報を自動的にスクレイピングし、CSVファイルとして保存するツールです。

## 機能

- Lancersの案件検索と情報取得 (`--search-query` など)。
- 以下の基本情報を収集：
  - 案件タイトル
  - 案件URL
  - 案件ID
  - 報酬
  - 案件種別
  - 募集状態
  - 締切情報 (リストページ表示)
- **ログイン機能:** 環境変数に設定された認証情報でLancersにログインし、詳細情報を取得。
- **最大取得件数指定 (`--max-items`)**: 検索モード時に取得する最大案件数を指定可能。
- **詳細情報取得モード (`--scrape-urls`)**:
    - 既存のCSVファイルを読み込み、各案件のURLにアクセス。
    - 詳細ページから「締切(raw)」「希望納期(raw)」「募集人数」を取得。
    - 取得した情報を元のCSVデータとマージし、**新しいCSVファイル (`元のファイル名_details.csv`)** に保存。
    - **チャンク処理:** `--chunk-size` で指定された件数ごとに処理を実行 (デフォルト10件)。
    - **続行確認:** 各チャンク完了時にユーザーに処理を続けるか確認 (`y`/`n`)。
- CSV形式でのデータ保存。
- タイトル列の余計な空白や改行を自動的にクリーニング。
- 環境変数による柔軟な設定。
- ヘッドレスモードでの実行対応。
- 詳細なログ出力 (`scraping.log`)。

## 必要要件

- Python 3.8以上
- Google Chrome（Playwrightが自動的にインストール）

## インストール手順

1.  **リポジトリのクローン**
    ```bash
    git clone https://github.com/yourusername/lancers-scraper.git
    cd lancers-scraper
    ```

2.  **仮想環境の作成と有効化**
    ```bash
    # 仮想環境の作成
    python -m venv venv

    # 仮想環境の有効化
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **依存パッケージのインストール**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Playwrightのブラウザインストール**
    ```bash
    playwright install
    ```

5.  **環境変数の設定**
    ```bash
    # .env.exampleをコピーして.envを作成
    cp .env.example .env
    ```
    `.env` ファイルを開き、以下の情報を設定してください。
    - `LANCERS_EMAIL`: ランサーズのログイン用メールアドレス
    - `LANCERS_PASSWORD`: ランサーズのログイン用パスワード
    (その他の設定項目は任意で調整してください)

## 使用方法

### 基本的な検索と情報取得

```bash
# キーワードで検索し、基本情報をCSVに保存（ヘッドレスモード）
python src/main.py --search-query "Python開発"

# 出力ファイル名を指定して検索
python src/main.py --search-query "Web開発" --output "web_dev_jobs.csv"

# ブラウザを表示して実行（デバッグ用）
python src/main.py --search-query "データ分析" --no-headless

# データ検索URLを使用してタスク案件をスクレイピング
python src/main.py --data-search

# データ検索URLを使用してプロジェクト案件をスクレイピング
python src/main.py --data-search-project
```

### 既存CSVから詳細情報を取得・追記

```bash
# CSVファイルからURLを読み込み、詳細情報を取得して新しいCSV (元のファイル名_details.csv) に保存
# デフォルトのチャンクサイズ (10件) で実行
python src/main.py --scrape-urls data/output/your_input_file.csv

# チャンクサイズを3件に指定して実行
python src/main.py --scrape-urls data/output/your_input_file.csv --chunk-size 3
```
実行中、各チャンク完了後に続行するか確認メッセージが表示されます (`y`/`n`)。

### その他

```bash
# CSVファイルからURL列を抽出してコンソールに表示
python src/main.py --extract-urls "path/to/your/csvfile.csv"

# 抽出したURLをファイルに保存
python src/main.py --extract-urls "path/to/your/csvfile.csv" --url-output "extracted_urls.txt"

# 既存のCSVファイルをクリーニング（現在は main.py に統合）
# python clean_existing_csv.py # (現在は不要)
```

### コマンドラインオプション

- `-q`, `--search-query`: 検索クエリ（オプション）
- `-o`, `--output`: 基本検索時の出力ファイル名（オプション、指定しない場合は自動生成）
- `--no-headless`: ブラウザを表示して実行（デフォルト：非表示）
- `--with-details`: 基本検索時に詳細情報も取得（**非推奨:** `--scrape-urls` を使用してください）
- `--data-search`: データ検索URLを使用してタスク案件をスクレイピング
- `--data-search-project`: データ検索URLを使用してプロジェクト案件をスクレイピング
- `--extract-urls`: CSVファイルからURLを抽出する（CSVファイルのパスを指定）
- `--url-output`: 抽出したURLの出力ファイル名（`--extract-urls` と併用）
- `--scrape-urls`: CSVファイルからURLを読み込み、ログインして詳細情報を取得・別ファイルに保存する（CSVファイルのパスを指定）
- `--chunk-size`: `--scrape-urls` 実行時のチャンクサイズ (デフォルト: 10)
- `--max-items`: 取得する最大案件数 (検索モード時)

## 設定

環境変数（`.env`ファイル）で以下の設定が可能です：

### ログイン情報 (必須)
- `LANCERS_EMAIL`: ランサーズのログインメールアドレス
- `LANCERS_PASSWORD`: ランサーズのパスワード

### ブラウザ設定 (任意)
- `HEADLESS`: ヘッドレスモードの有効/無効（true/false）
- `BROWSER_TIMEOUT`: ブラウザのタイムアウト時間（ミリ秒）
- `RETRY_COUNT`: リトライ回数
- `WAIT_TIME`: ページ読み込み待機時間（秒）

### スクレイピング設定 (任意)
- `MAX_PAGES`: 検索結果リストを取得する最大ページ数
- `ITEMS_PER_PAGE`: 1ページあたりの取得件数 (現在は未使用)

## 出力データ

### 基本検索 (`--search-query`, `--data-search`, `--data-search-project`)

`data/output` ディレクトリにCSVファイルが生成されます。列構成は以下の通りです（`main.py` 内の `basic_fieldnames` に基づく）。

- `scraped_at`: スクレイピング実行日時
- `title`: 案件タイトル
- `url`: 案件のURL
- `work_id`: 案件ID
- (その他、リストページから取得可能な情報。`price`, `type`, `deadline`, `status` などが含まれる場合がありますが、基本出力では上記4列が保証されます)

### 詳細情報取得 (`--scrape-urls`)

`data/output` ディレクトリに `元のファイル名_details.csv` という名前で新しいCSVファイルが生成されます。列構成は以下の通りです (`main.py` 内の `final_fieldnames` 構築ロジックに基づく)。

- `scraped_at`: スクレイピング実行日時
- `title`: 案件タイトル
- `url`: 案件のURL
- `deadline_raw`: 締切 (詳細ページ表示の生データ)
- `delivery_date_raw`: 希望納期 (詳細ページ表示の生データ)
- `people`: 募集人数 (詳細ページ表示の生データ)
- (元のCSVに含まれていた他の列: ただし、`deadline`, `price`, `type`, `status`, `work_id`, `period` など、不要と判断された列は除外される可能性があります)

## 注意事項

1.  **利用規約の遵守**
    - Lancersの利用規約を必ず確認し、遵守してください。
    - サーバーに負荷をかけないよう、過度なリクエストは避けてください。
2.  **エラー処理**
    - ログイン失敗時や詳細情報取得失敗時はログが出力されます。
    - 長時間実行する場合は、ログやコンソールの出力を確認してください。
3.  **データの保存**
    - スクレイピングしたデータは`data/output`ディレクトリに保存されます。
    - 古いデータは自動的には削除されないため、定期的な整理を推奨します。

## ログ

- 実行ログはプロジェクトルートの`scraping.log`に出力されます。
- ログレベルは`INFO`がデフォルトです。
- エラー発生時は詳細な情報が記録されます。
- `--scrape-urls` 実行時にログインに失敗した場合、`error_screenshot_*.png` という名前のスクリーンショットが保存されることがあります。

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
