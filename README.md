# Lancers Scraper

Lancersの案件情報を自動的にスクレイピングし、CSVファイルとしてローカルに保存、およびGoogle Driveへアップロードするツールです。市場分析、案件追跡、データ収集を効率化します。

## プロジェクト概要

Pythonベースのウェブスクレイピングツールで、以下の主要機能を提供します：

- キーワードや特定のデータカテゴリに基づいた案件検索。
- 検索キーワードは外部ファイル (`keywords.txt`) で柔軟に管理可能。
- 対話的なバッチファイル (`run_scraper.bat`) による簡単操作 (Windows環境)。
- 個別の案件詳細情報の抽出。
- 抽出データの処理とクリーニング。
- 抽出データをCSVファイルとしてローカルにエクスポート。
- 生成されたCSVファイルをGoogle Driveの指定フォルダへ自動アップロード（オプション）。
- GitHub Actionsによる定期的な自動実行とアップロード。
- ヘッドレスブラウジング、ログイン機能など、カスタマイズ可能なオプション。

## 機能

- **柔軟な案件検索:**
    - `run_scraper.bat` (Windows): `keywords.txt` からキーワードを読み込み、対話形式で検索・処理を実行。各入力段階でキャンセルして前のメニューに戻る機能付き。
    - `src/main.py` (コマンドライン):
        - `--search-query`: 指定キーワードで検索。
        - `--data-search`: データ検索URL（タスク案件）で検索。
        - `--data-search-project`: データ検索URL（プロジェクト案件）で検索。
- **情報収集:**
    - 基本情報: 案件タイトル, URL, ID, 報酬, 種別, 募集状態, 締切 (リストページ)。
    - 詳細情報 (`--scrape-urls` 時): 締切(raw), 希望納期(raw), 募集人数。
- **データ処理と保存:**
    - タイトル列の自動クリーニング。
    - CSV形式で `data/output/` ディレクトリにローカル保存。
    - **Google Drive連携:**
        - 生成されたCSVファイルを指定のGoogle Driveフォルダへ自動アップロード (オプション `--upload-gdrive`)。
- **自動実行 (GitHub Actions):**
    - `.github/workflows/daily_scrape.yml` により、毎日日本時間午前9時に `keywords.txt` 内の全キーワードで検索処理とGoogle Driveへのアップロードを自動実行。
- **その他:**
    - ログイン機能 (環境変数 `LANCERS_EMAIL`, `LANCERS_PASSWORD`)。
    - 最大取得件数指定 (`--max-items`)。
    - チャンク処理と続行確認 (`--scrape-urls` 時)。
    - ヘッドレスモード対応 (`--no-headless` で無効化)。
    - 詳細なログ出力 (`scraping.log`)。ログレベルは `src/main.py` 内で `DEBUG` に設定済み。

## 必要要件

- Python 3.8以上
- Google Chrome（Playwrightが自動的にインストールされるが、CI環境では明示的なインストールが必要）
- Google Cloud Platformアカウント (Google Driveアップロード機能を利用する場合)
- Git (バージョン管理とGitHub連携のため)

## インストールと事前準備

1.  **リポジトリのクローン:**
    ```bash
    git clone https://github.com/ishibashm/lancers-scraper.git # あなたのリポジトリURL
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

4.  **Playwrightのブラウザインストール (ローカル環境):**
    ```bash
    playwright install
    ```
    (GitHub Actions環境ではワークフロー内で自動インストールされます)

5.  **環境変数ファイルの設定 (`.env`):**
    ```bash
    cp .env.example .env
    ```
    `.env` ファイルを開き、以下を設定します。
    - `LANCERS_EMAIL`: ランサーズのログイン用メールアドレス (必須)
    - `LANCERS_PASSWORD`: ランサーズのログイン用パスワード (必須)
    - `GDRIVE_FOLDER_ID`: (任意) Google Driveのアップロード先フォルダID。コマンドライン引数やGitHub Secretsでも設定可。
    - `GDRIVE_CREDENTIALS_PATH`: (任意) Google Drive API認証情報ファイルへのパス。デフォルトは `service_account.json`。コマンドライン引数やGitHub Secretsでも設定可。

6.  **検索キーワードファイルの設定 (`keywords.txt`):**
    プロジェクトのルートディレクトリに `keywords.txt` を作成（または編集）し、検索したいキーワードを1行に1つずつ記述します。
    - **ローカルで `run_scraper.bat` を使用する場合:** ファイルの文字コードは **Shift_JIS (ANSI)**、改行コードは **CRLF (Windows形式)** にしてください。
    - **GitHub Actionsで自動実行する場合:** ファイルの文字コードは **UTF-8**、改行コードは **LF (Linux形式)** でリポジトリに保存してください。

7.  **Google Drive連携のための設定 (アップロード機能を利用する場合):**
    a.  Google Cloudプロジェクトで「Google Drive API」を有効化。
    b.  サービスアカウントを作成し、キー(JSON)をダウンロード。ファイル名を `service_account.json` (または指定名)としてプロジェクトルートに配置。
        **【重要】このJSONファイルは機密情報です。`.gitignore` に追加し、Gitリポジトリにコミットしないでください。** (`.gitignore` には `service_account.json` がデフォルトで追加済)
    c.  Google Driveでアップロード先フォルダを作成し、サービスアカウントのメールアドレスに「編集者」権限で共有。フォルダIDを控える。

## 使用方法

### 1. バッチファイル (`run_scraper.bat`) による対話的実行 (Windows推奨)

プロジェクトルートの `run_scraper.bat` を実行 (PowerShellでは `.\run_scraper.bat`)。
1.  **メインメニュー:** 「キーワード選択」「既存CSVから詳細取得」「終了」を選択。
2.  **キーワード選択時:** `keywords.txt` からキーワードを選択。
3.  **操作選択:** 検索、詳細取得などの操作を選択。
4.  **Google Driveアップロード確認:** CSV生成後、アップロードするか選択。
各入力画面では「0」を入力することで前のメニューに戻れます。

### 2. コマンドライン (`src/main.py`) による直接実行
(詳細は以前のREADMEセクションを参照。Google Drive関連オプションが追加されています)
- **`--upload-gdrive`**: 生成CSVをGoogle Driveにアップロード。
- **`--gdrive-folder-id TEXT`**: アップロード先フォルダID。
- **`--gdrive-credentials TEXT`**: 認証情報ファイルパス (デフォルト: `service_account.json`)。

### 3. GitHub Actionsによる自動実行 (スケジュール実行)

`.github/workflows/daily_scrape.yml` により、毎日日本時間午前9時に `keywords.txt` の全キーワードで検索処理とGoogle Driveへのアップロードが自動実行されます。
これを有効にするには：
1.  ワークフローファイルを含む全ての変更をGitHubリポジトリのデフォルトブランチにプッシュします。
2.  GitHubリポジトリの `Settings > Secrets and variables > Actions` で以下の**Repository secrets**を登録します。
    - `LANCERS_EMAIL`: ランサーズのメールアドレス。
    - `LANCERS_PASSWORD`: ランサーズのパスワード。
    - `GDRIVE_FOLDER_ID`: Google Driveのアップロード先フォルダID。
    - `GDRIVE_SA_KEY_JSON`: `service_account.json` ファイルの**内容全体**。

## トラブルシューティング（よくある問題と対処法）

- **文字化け:**
    - **ローカルバッチ実行時:** `run_scraper.bat` と `keywords.txt` の文字コードを **Shift_JIS (ANSI)** に、改行コードを **CRLF** にしてください。
    - **GitHub Actions実行時:** `keywords.txt` をリポジトリに保存する際は、文字コードを **UTF-8**、改行コードを **LF** にしてください。ワークフローログの文字化けは、`PYTHONIOENCODING=utf-8` 設定で概ね解消されます。
- **Google Driveアップロードエラー (`Expecting value: line 1 column 1 (char 0)`など):**
    - `service_account.json` (または指定した認証ファイル) の内容が正しいJSON形式であるか、ファイルが空でないか、破損していないか確認してください。Google Cloud Consoleからキーを再ダウンロードして置き換えるのが最も確実です。
    - サービスアカウントに、対象のGoogle Driveフォルダへの「編集者」権限が付与されているか確認してください。
- **Playwrightブラウザエラー (GitHub Actions時 - `Executable doesn't exist ...`):**
    - `.github/workflows/daily_scrape.yml` に `playwright install --with-deps chromium` (または必要なブラウザ) のステップが含まれているか確認してください。
- **バッチファイルのエラー (`指定されたバッチ ラベルが見つかりません`など):**
    - `run_scraper.bat` ファイルが最新版であるか確認してください。

## ログ
(変更なしのため省略)

## プロジェクト構造
(主要なファイルとして `.github/workflows/daily_scrape.yml` を追記)
- **`.github/workflows/daily_scrape.yml`**: GitHub Actions用ワークフローファイル。
(その他は以前のREADMEセクションを参照)

## ライセンス
MITライセンス
