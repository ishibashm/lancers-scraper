import os
import logging
from src.utils.csv_handler import CSVHandler

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    output_dir = "data/output"
    handler = CSVHandler(output_dir)
    
    # 出力ディレクトリ内のすべてのCSVファイルを処理
    for filename in os.listdir(output_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(output_dir, filename)
            logging.info(f"処理中のファイル: {filepath}")
            
            # CSVファイルを読み込む
            data = handler.read_csv(filepath)
            if not data:
                logging.warning(f"データが空です: {filepath}")
                continue
            
            # データをクリーニング
            cleaned_data = handler.clean_data(data)
            
            # クリーニングしたデータを新しいファイルに保存
            cleaned_filename = filename.replace('.csv', '_cleaned.csv')
            cleaned_filepath = handler.save_to_csv(cleaned_data, cleaned_filename)
            logging.info(f"クリーニング済みのファイルを保存しました: {cleaned_filepath}")

if __name__ == "__main__":
    main()
