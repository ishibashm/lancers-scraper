# Lancers Scraper 実装状況

## ディレクトリ構造
- [x] プロジェクトの基本ディレクトリ構造の作成
- [x] 必要なファイルの作成

## ソースコード実装
### src/scraper/
- [x] browser.py - Playwrightブラウザ管理
  - [x] LancersBrowserクラスの実装
  - [x] ブラウザの起動・終了処理
  - [x] 検索機能の実装
  - [x] エラーハンドリング
  - [x] ページネーション対応

- [x] parser.py - HTMLパース処理
  - [x] LancersParserクラスの実装
  - [x] 案件情報の抽出処理
  - [x] データ整形機能
  - [x] エラーハンドリング

### src/utils/
- [x] csv_handler.py - CSV出力処理
  - [x] CSVHandlerクラスの実装
  - [x] ファイル保存機能
  - [x] データ追記機能
  - [x] ファイル読み込み機能

- [x] config.py - 設定ファイル
  - [x] 環境変数の管理
  - [x] 設定値の定義
  - [x] 設定ファイルの読み込み機能

- [x] backup_handler.py - バックアップ処理
  - [x] BackupHandlerクラスの実装
  - [x] バックアップ作成機能
  - [x] バックアップ復元機能
  - [x] バックアップローテーション

- [x] cleanup_handler.py - クリーンアップ処理
  - [x] CleanupHandlerクラスの実装
  - [x] 古いファイルの削除機能
  - [x] 重複データの削除機能
  - [x] 一時ファイルのクリーンアップ

- [x] retry_handler.py - リトライ機能
  - [x] RetryHandlerクラスの実装
  - [x] 同期・非同期関数のリトライ対応
  - [x] バックオフ遅延機能
  - [x] カスタムパラメータ対応

- [x] progress_handler.py - プログレスバー
  - [x] ProgressHandlerクラスの実装
  - [x] 進捗表示機能
  - [x] 統計情報の計算
  - [x] 非同期対応

### src/
- [x] main.py - メインスクリプト
  - [x] コマンドライン引数の処理
  - [x] メイン処理フローの実装
  - [x] ロギング機能の実装
  - [x] エラーハンドリング

## テスト実装
### tests/
- [x] test_browser.py
  - [x] ブラウザ操作のテスト
  - [x] 検索機能のテスト
  - [x] エラーケースのテスト
  - [x] ページネーションのテスト

- [x] test_parser.py
  - [x] パース処理のテスト
  - [x] データ整形のテスト
  - [x] エラーケースのテスト
  - [x] 日付変換機能のテスト
  - [x] 募集人数抽出機能の拡張テスト

- [x] test_backup.py
  - [x] バックアップ作成のテスト
  - [x] バックアップ復元のテスト
  - [x] バックアップローテーションのテスト
  - [x] エラーケースのテスト

- [x] test_cleanup.py
  - [x] 古いファイルの削除テスト
  - [x] 重複データの削除テスト
  - [x] 一時ファイルのクリーンアップテスト
  - [x] エラーケースのテスト

- [x] test_retry.py
  - [x] 同期・非同期関数のテスト
  - [x] リトライ動作のテスト
  - [x] バックオフ遅延のテスト

- [x] test_progress.py
  - [x] 進捗更新のテスト
  - [x] 表示フォーマットのテスト
  - [x] 非同期処理のテスト

## ドキュメント
- [x] README.md
  - [x] プロジェクトの説明
  - [x] インストール手順
  - [x] 使用方法
  - [x] 設定方法
  - [x] 注意事項

## データ管理
- [x] data/output/ディレクトリの作成
- [x] データバックアップの仕組み
- [x] データクリーンアップスクリプト

## 追加タスク
- [x] ページネーション対応
- [x] 並列処理の実装
- [x] リトライ機能の実装
- [x] プログレスバーの追加
- [ ] 検索条件の拡張
- [ ] データベース連携機能
- [x] 詳細情報抽出機能の強化
  - [x] 案件URLからのIDパース機能改善（/work/detail/[数字]のパターン）
  - [x] CSSセレクタからページテキスト全体の検索方式への移行
  - [x] 募集情報セクションのレイアウト解析と抽出方法の改善
  - [x] 複数の情報抽出方法の実装（セレクタ + 正規表現の組み合わせ）

- [x] get_work_detail関数の拡張
  - [x] ページ全体のテキスト解析による情報抽出実装（document.body.innerText）
  - [x] 募集人数の正規表現パターン改善（「募集人数1人」形式に対応）
  - [x] 実行時エラーのリトライ機能強化
  - [x] ページロード完了検出の強化（networkidle → waitForSelector併用）

- [x] parser.pyの改善
  - [x] 日付フォーマットの標準化機能（YYYY-MM-DD形式への変換）
  - [x] 募集人数の数値抽出強化（数字のみを取り出す）
  - [x] 複数の正規表現パターンによる多様な形式への対応
  - [x] 詳細テキストからの構造化情報抽出機能

- [x] テスト追加
  - [x] 詳細ページの解析テスト（parse_work_detail）
  - [x] 様々な日付形式パターンのユニットテスト
  - [x] 募集人数抽出パターンテスト
  - [x] エラー処理テスト

## 環境設定
- [x] requirements.txt
  - [x] 必要なパッケージの追加
  - [x] バージョン指定
- [ ] 開発環境のセットアップスクリプト
- [ ] CI/CD設定
- [ ] Dockerファイルの作成

## 次のステップ
1. ~~config.pyの作成と実装~~ ✓
2. ~~requirements.txtの内容実装~~ ✓
3. ~~README.mdの作成~~ ✓
4. ~~テストファイルの作成と実装~~ ✓
   - [x] test_browser.py
   - [x] test_parser.py
5. ~~データ管理機能の実装~~ ✓
   - [x] バックアップ機能
   - [x] クリーンアップスクリプト
6. ~~追加機能の実装~~ ✓
   - [x] ページネーション対応
   - [x] 並列処理の実装
   - [x] 詳細情報抽出機能の強化
7. 今後の課題
   - [ ] 詳細ページの情報抽出改善
     - [ ] p.p-work-detail-scheduleクラスを利用した締切日時抽出
     - [ ] p.p-work-detail-scheduleクラスを利用した希望納期抽出
     - [ ] 抽出結果の優先順位付け（セレクタ間の優先順位設定）
     - [ ] 複雑な日付形式への対応強化
     - [ ] 実装方法
       ```python
       # browser.py - get_work_detail関数内に追加
       # p-work-detail-scheduleクラスを利用した抽出を追加
       schedule_elements = await self.page.query_selector_all('.p-work-detail-schedule')
       for element in schedule_elements:
           element_text = await element.text_content()
           if "締切" in element_text:
               deadline_match = re.search(r'締切[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{1,2})', element_text)
               if deadline_match:
                   detail_info['deadline_schedule'] = deadline_match.group(1)
           if "希望納期" in element_text:
               delivery_date_match = re.search(r'希望納期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)', element_text)
               if delivery_date_match:
                   detail_info['delivery_date_schedule'] = delivery_date_match.group(1)
       
       # 結果を統合（優先順位: p-work-detail-schedule > 正規表現 > セレクタ）
       deadline = detail_info.get('deadline_schedule', 
                 detail_info.get('deadline_regex', deadline_selector))
       delivery_date = detail_info.get('delivery_date_schedule', 
                      detail_info.get('delivery_date_regex', delivery_date_selector))
       ```
   - [ ] 締切日時のフォーマット調整
     - [ ] 締切日時から時間部分を除去（日付のみを返す）
     - [ ] 実装方法
       ```python
       # parser.py - format_dateメソッドの修正
       def format_date(self, date_str: str, include_time: bool = False) -> str:
           """
           日本語の日付形式を標準形式（YYYY-MM-DD）に変換
           Args:
               date_str (str): 変換する日付文字列（例：2025年04月21日 18:17）
               include_time (bool): 時間部分を含めるかどうか
           Returns:
               str: 変換後の日付文字列
           """
           try:
               if not date_str:
                   return ""
                   
               # 年月日の抽出
               date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
               if not date_match:
                   return date_str
                   
               year = date_match.group(1)
               month = date_match.group(2).zfill(2)  # 1桁の場合は0埋め
               day = date_match.group(3).zfill(2)    # 1桁の場合は0埋め
               
               # 時刻部分は要求された場合のみ追加
               if include_time:
                   time_match = re.search(r'(\d{1,2}):(\d{1,2})', date_str)
                   if time_match:
                       hour = time_match.group(1).zfill(2)
                       minute = time_match.group(2).zfill(2)
                       return f"{year}-{month}-{day} {hour}:{minute}"
               
               return f"{year}-{month}-{day}"
           except Exception as e:
               self.logger.error(f"日付形式の変換に失敗しました: {str(e)}")
               return date_str
               
       # parse_work_detailメソッド内での使用
       # 締切日時のパース（時間なし）
       deadline_raw = detail.get('deadline', '')
       deadline = self.parse_deadline(deadline_raw)
       deadline_formatted = self.format_date(deadline, include_time=False)
       
       # 希望納期のパース（元々時間なし）
       delivery_date_raw = detail.get('delivery_date', '')
       delivery_date = self.parse_delivery_date(delivery_date_raw)
       delivery_date_formatted = self.format_date(delivery_date)
       ```
   - [ ] 案件タイトルの加工機能
     - [ ] タイトルからカテゴリー部分の削除（例：[芸能・エンターテイメント]）
     - [ ] 実装方法
       ```python
       # parser.py - parse_work_detailメソッド内に追加
       def clean_title(self, title: str) -> str:
           """
           案件タイトルからカテゴリー部分を削除する
           例：'TikTokショートドラマ脚本家募集の仕事 [芸能・エンターテイメント]' 
              → 'TikTokショートドラマ脚本家募集の仕事'
           Args:
               title (str): 元のタイトル
           Returns:
               str: 加工後のタイトル
           """
           try:
               # 角括弧で囲まれたカテゴリー部分を削除
               cleaned_title = re.sub(r'\s*\[.*?\]\s*$', '', title)
               return cleaned_title.strip()
           except Exception as e:
               self.logger.error(f"タイトルの加工に失敗しました: {str(e)}")
               return title
               
       # 使用例
       title = detail.get('title', '')
       cleaned_title = self.clean_title(title)
       
       return {
           'title': cleaned_title,
           'title_raw': title,
           # 他のフィールド...
       }
       ```
   - [ ] 検索条件の拡張機能
   - [ ] データベース連携機能
   - [ ] 開発環境のセットアップスクリプト作成
   - [ ] CI/CD環境の構築
   - [ ] Dockerファイルの作成 