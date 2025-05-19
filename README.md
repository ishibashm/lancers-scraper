# Lancers Scraper

Lancersの案件情報を自動的にスクレイピングし、CSVファイルとしてローカルに保存、およびGoogle Driveへアップロードするツールです。市場分析、案件追跡、データ収集を効率化します。

## プロジェクト概要

Pythonベースのウェブスクレイピングツールで、以下の主要機能を提供します：

- キーワードや特定のデータカテゴリに基づいた案件検索。
- 検索キーワードは外部ファイル (`keywords.txt`) で柔軟に管理可能。
- 対話的なバッチファイル (`run_scraper.bat`) による簡単操作。
- 個別の案件詳細情報の抽出。
- 抽出データの処理とクリーニング。
- 抽出データをCSVファイルとしてローカルにエクスポート。
- 生成されたCSVファイルをGoogle Driveの指定フォルダへ自動アップロード（オプション）。
- ヘッドレスブラウジング、ログイン機能など、カスタマイズ可能なオプション。

## 機能

- **柔軟な案件検索:**
    - `run_scraper.bat`: `keywords.txt` からキーワードを読み込み、対話形式で検索・処理を実行。
    - `src/main.py` (コマンドライン):
        - `--search-query`: 指定キーワードで検索。
        - `--data-search`: データ検索URL（タスク案件）で検索。
        - `--data-search-project`: データ検索URL（プロジェクト案件）で検索。
- **情報収集:**
    - 基本情報: 案件タイトル, URL, ID, 報酬, 種別, 募集状態, 締切 (リストページ)。
    - 詳細情報 (`--scrape-urls` 時): 締切(raw), 希望納期(raw), 募集人数。
- **データ処理と保存:**
    - タイトル列の自動クリーニング。
    - CSV形式で `data/output/` ディレクトリに保存。
    - **Google Drive連携:**
        - 生成されたCSVファイルを指定のGoogle Driveフォルダへ自動アップロード (オプション `--upload-gdrive`)。
- **その他:**
    - ログイン機能 (環境変数 `LANCERS_EMAIL`, `LANCERS_PASSWORD`)。
    - 最大取得件数指定 (`--max-items`)。
    - チャンク処理と続行確認 (`--scrape-urls` 時)。
    - ヘッドレスモード対応 (`--no-headless` で無効化)。
    - 詳細なログ出力 (`scraping.log`)。ログレベルは `src/main.py` 内で `DEBUG` に設定変更済み。

## 必要要件

- Python 3.8以上
- Google Chrome（Playwrightが自動的にインストール）
- Google Cloud Platformアカウント (Google Driveアップロード機能を利用する場合)

## インストールと事前準備

1.  **リポジトリのクローン:**
    ```bash
    git clone https://github.com/yourusername/lancers-scraper.git # リポジトリURLは適宜変更してください
    cd lancers-scraper
    ```

2.  **仮想環境の作成と有効化:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **依存パッケージのインストール:**
    `requirements.txt` にはGoogle Drive APIライブラリも含まれています。
    ```bash
    pip install -r requirements.txt
    ```

4.  **Playwrightのブラウザインストール:**
    ```bash
    playwright install
    ```

5.  **環境変数ファイルの設定 (`.env`):**
    ```bash
    cp .env.example .env
    ```
    `.env` ファイルを開き、以下を設定します。
    - `LANCERS_EMAIL`: ランサーズのログイン用メールアドレス (必須)
    - `LANCERS_PASSWORD`: ランサーズのログイン用パスワード (必須)
    - `GDRIVE_FOLDER_ID`: (任意) Google Driveのアップロード先フォルダID。コマンドライン引数でも指定可能。
    - `GDRIVE_CREDENTIALS_PATH`: (任意) Google Drive API認証情報ファイルへのパス。デフォルトは `service_account.json`。コマンドライン引数でも指定可能。
    (その他の設定項目は任意で調整してください)

6.  **検索キーワードファイルの設定 (`keywords.txt`):**
    プロジェクトのルートディレクトリに `keywords.txt` という名前のファイルを作成（または既存のファイルを編集）し、検索したいキーワードを1行に1つずつ記述します。例:
    ```
    ショート
    リール
    SNS運用代行
    ```
    このファイルは `run_scraper.bat` から読み込まれます。ファイルの文字コードは **Shift_JIS (ANSI)** にしてください。

7.  **Google Drive連携のための設定 (アップロード機能を利用する場合):**
    a.  **Google Cloudプロジェクトの準備とAPI有効化:**
        - Google Cloud Consoleでプロジェクトを選択または作成し、「Google Drive API」を有効にします。
    b.  **サービスアカウントの作成とキーの取得:**
        - プロジェクトでサービスアカウントを作成します。
        - 作成したサービスアカウントのキー（JSON形式）をダウンロードし、ファイル名を `service_account.json` (または `.env` や引数で指定したパスのファイル名) としてプロジェクトのルートディレクトリに配置します。
        - **【重要】このJSONファイルは機密情報です。`.gitignore` にファイル名を追加し、Gitリポジトリにコミットしないでください。** (`.gitignore` には `service_account.json` がデフォルトで追加されています。)
    c.  **Google Driveフォルダの共有設定:**
        - Google Driveでアップロード先のフォルダを作成します。
        - 作成したフォルダを、上記bで作成したサービスアカウントのメールアドレスに対して「編集者」権限で共有します。
        - このフォルダのIDを控えておき、`.env` ファイルの `GDRIVE_FOLDER_ID` やコマンドライン引数 `--gdrive-folder-id` で指定します。

## 使用方法

### 1. バッチファイル (`run_scraper.bat`) による対話的実行 (推奨)

プロジェクトのルートディレクトリにある `run_scraper.bat` を実行します (PowerShellの場合は `.\run_scraper.bat`)。
文字化けする場合は、`run_scraper.bat` と `keywords.txt` の文字コードを **Shift_JIS (ANSI)** にしてください。

1.  **キーワード選択:** `keywords.txt` に記述されたキーワードのリストが表示されるので、番号で選択します。
2.  **操作選択:** 選択したキーワードに対して行う操作を番号で選択します。
    - 検索して詳細情報を取得する
    - 検索のみ実行する
    - 詳細情報のみ取得する (既存CSVファイルを指定)
3.  **Google Driveへのアップロード確認:** 各処理でCSVファイルが生成された後、そのファイルをGoogle Driveにアップロードするかどうか確認メッセージが表示されます。「y」を入力するとアップロードが試行されます。

### 2. コマンドライン (`src/main.py`) による直接実行

より詳細なオプションを指定して実行したい場合は、コマンドラインから `python src/main.py` を使用します。

**基本的な検索と情報取得:**
```bash
# キーワード「Python開発」で検索し、結果をCSVに保存 (Google Driveアップロードなし)
python src/main.py --search-query "Python開発"

# キーワード「Web開発」で検索し、結果をCSVに保存し、Google Driveにもアップロード
python src/main.py --search-query "Web開発" --output "web_dev_jobs.csv" --upload-gdrive --gdrive-folder-id "YOUR_FOLDER_ID"
```

**既存CSVから詳細情報を取得・追記し、Google Driveにもアップロード:**
```bash
python src/main.py --scrape-urls data/output/your_input_file.csv --upload-gdrive --gdrive-folder-id "YOUR_FOLDER_ID"
```

### コマンドラインオプション (`src/main.py`)

- `-q`, `--search-query TEXT`: 検索クエリ。
- `-o`, `--output TEXT`: 基本検索時の出力ファイル名。
- `--no-headless`: ブラウザを表示して実行。
- `--data-search`: データ検索URL（タスク案件）でスクレイピング。
- `--data-search-project`: データ検索URL（プロジェクト案件）でスクレイピング。
- `--extract-urls TEXT`: CSVファイルからURLを抽出（CSVファイルのパスを指定）。
- `--url-output TEXT`: 抽出したURLの出力ファイル名。
- `--scrape-urls TEXT`: CSVファイルからURLを読み込み詳細情報を取得（CSVファイルのパスを指定）。
- `--chunk-size INTEGER`: `--scrape-urls` 時のチャンクサイズ (デフォルト: 10)。
- `--max-items INTEGER`: 取得する最大案件数 (検索モード時)。
- `--skip-confirm`: チャンクごとの確認をスキップ。
- **`--upload-gdrive`**: 生成されたCSVファイルをGoogle Driveにアップロード。
- **`--gdrive-folder-id TEXT`**: Google Driveのアップロード先フォルダID。環境変数 `GDRIVE_FOLDER_ID` でも設定可。
- **`--gdrive-credentials TEXT`**: Google Drive API認証情報ファイル(JSON)へのパス。環境変数 `GDRIVE_CREDENTIALS_PATH` でも設定可 (デフォルト: `service_account.json`)。

(旧 `--with-details` オプションは非推奨です。)

## 設定 (環境変数 `.env` ファイル)

### ログイン情報 (必須)
- `LANCERS_EMAIL`: ランサーズのログインメールアドレス
- `LANCERS_PASSWORD`: ランサーズのパスワード

### Google Drive連携 (任意)
- `GDRIVE_FOLDER_ID`: Google Driveのアップロード先フォルダID。
- `GDRIVE_CREDENTIALS_PATH`: Google Drive API認証情報ファイルへのパス (デフォルト: `service_account.json`)。

### ブラウザ設定 (任意)
- `HEADLESS`: ヘッドレスモードの有効/無効（true/false）
- `BROWSER_TIMEOUT`: ブラウザのタイムアウト時間（ミリ秒）
- `RETRY_COUNT`: リトライ回数
- `WAIT_TIME`: ページ読み込み待機時間（秒）

### スクレイピング設定 (任意)
- `MAX_PAGES`: 検索結果リストを取得する最大ページ数

## 出力データ
(変更なしのため省略。必要であれば以前の内容をここに記述)

## 注意事項
(変更なしのため省略。必要であれば以前の内容をここに記述)

## ログ
- 実行ログはプロジェクトルートの`scraping.log`に出力されます。
- ログレベルは `src/main.py` 内の `setup_logging` 関数で `DEBUG` に設定されています。詳細な情報が必要な場合に役立ちます。
- Google Driveへのアップロード試行に関するログもここに出力されます。

## プロジェクト構造

### 主要ファイルとディレクトリ
- **`run_scraper.bat`**: Windows用バッチファイル。対話形式でスクリプトを実行。
- **`keywords.txt`**: `run_scraper.bat` が参照する検索キーワードリスト。
- **`service_account.json`**: (ユーザーが配置) Google Drive API認証用のサービスアカウントキーファイル。`.gitignore` で保護。
- **`src/main.py`**: アプリケーションのエントリーポイント。引数解析と処理の振り分け。
- **`src/scraper/browser.py`**: ブラウザ自動化 (`LancersBrowser`クラス)。
- **`src/scraper/parser.py`**: データ解析 (`LancersParser`クラス)。
- **`src/utils/csv_handler.py`**: CSV操作 (`CSVHandler`クラス)。
- **`src/utils/gdrive_uploader.py`**: Google Driveアップロード処理 (`upload_to_gdrive`関数)。
- **`src/utils/config.py`**: (もしあれば) 設定管理クラス。現在は主に `.env` と `os.getenv` を使用。
- **`data/output/`**: 生成されたCSVファイルが保存されるディレクトリ。
- **`tests/`**: ユニットテスト。

(その他、`retry_handler.py` なども `src/utils/` に存在)

## 開発者向け情報
(変更なしのため省略。必要であれば以前の内容をここに記述)

## ライセンス
MITライセンス
