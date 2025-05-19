import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

logger = logging.getLogger(__name__)

# スコープはDrive API v3のファイル操作に必要なものを指定
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_to_gdrive(file_path, folder_id, credentials_path='service_account.json'):
    """
    指定されたファイルをGoogle Driveの指定フォルダにアップロードする。

    :param file_path: アップロードするファイルのパス
    :param folder_id: アップロード先のGoogle DriveフォルダID
    :param credentials_path: サービスアカウントキーのJSONファイルパス
    :return: アップロードされたファイルのID、またはエラー時はNone
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"指定されたファイルが見つかりません: {file_path}")
            return None

        if not os.path.exists(credentials_path):
            logger.error(f"認証情報ファイルが見つかりません: {credentials_path}")
            logger.error("Google Cloud Consoleからサービスアカウントキーをダウンロードし、")
            logger.error(f"プロジェクトルートに '{os.path.basename(credentials_path)}' (または指定したパス) として配置してください。")
            return None

        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        
        service = build('drive', 'v3', credentials=creds, cache_discovery=False) # cache_discovery=False を追加

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        
        logger.info(f"'{os.path.basename(file_path)}' をGoogle Driveフォルダ '{folder_id}' にアップロードしています...")
        
        # resumable upload
        request = service.files().create(media_body=media, body=file_metadata, fields='id')
        response = None
        uploaded_file = None # file だとPythonの組み込み型と衝突するため変更
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"アップロード進捗: {int(status.progress() * 100)}%")
        
        uploaded_file = response
        uploaded_file_id = uploaded_file.get('id')
        logger.info(f"ファイルが正常にアップロードされました。ファイルID: {uploaded_file_id}")
        # Google Driveのファイルへのリンクを生成 (オプション)
        file_link = f"https://drive.google.com/file/d/{uploaded_file_id}/view?usp=sharing"
        logger.info(f"アップロードされたファイルへのリンク: {file_link}")
        return uploaded_file_id

    except Exception as e:
        logger.error(f"Google Driveへのアップロード中にエラーが発生しました: {e}")
        logger.error("以下の点を確認してください:")
        logger.error(f"  1. 認証情報ファイル '{credentials_path}' が正しいか、またそのパスが正しいか。")
        logger.error(f"  2. サービスアカウントがGoogle Driveフォルダ '{folder_id}' への書き込み権限を持っているか。")
        logger.error("  3. Google Drive APIがGoogle Cloudプロジェクトで有効になっているか。")
        logger.error("  4. 必要なライブラリ (google-api-python-client等) が正しくインストールされているか。")
        return None

if __name__ == '__main__':
    # このスクリプトを直接実行した場合のテストコード (通常は使用しない)
    # 実行前に、プロジェクトルートに 'service_account.json' と
    # アップロードしたいテストファイル 'test_upload.csv' を用意し、
    # 'YOUR_FOLDER_ID_HERE' を実際のフォルダIDに置き換えてください。
    
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # test_file_to_upload = 'test_upload.csv'
    # target_folder_id = 'YOUR_FOLDER_ID_HERE' 
    # credentials_file = 'service_account.json' # プロジェクトルートにあると仮定

    # # ダミーのテストファイルを作成
    # if not os.path.exists(test_file_to_upload):
    #     with open(test_file_to_upload, 'w', encoding='utf-8') as f:
    #         f.write("これはGoogle Driveアップロードテスト用のCSVファイルです。\n")
    #         f.write("ID,Name\n")
    #         f.write("1,テストデータ1\n")
    #         f.write("2,テストデータ2\n")
    #     logger.info(f"テストファイル '{test_file_to_upload}' を作成しました。")

    # if target_folder_id == 'YOUR_FOLDER_ID_HERE':
    #     logger.warning("テストを実行する前に、target_folder_id を実際のGoogle DriveフォルダIDに置き換えてください。")
    # else:
    #     logger.info(f"テストアップロードを開始します: {test_file_to_upload} -> フォルダID {target_folder_id}")
    #     uploaded_id = upload_to_gdrive(test_file_to_upload, target_folder_id, credentials_file)
    #     if uploaded_id:
    #         print(f"テストアップロード成功。ファイルID: {uploaded_id}")
    #     else:
    #         print("テストアップロード失敗。ログを確認してください。")
    pass
