import csv
import os
import glob

# 最新のCSVファイルを探す
csv_files = glob.glob('data/output/*.csv')
if not csv_files:
    print("CSVファイルが見つかりません。")
    exit(1)

# ファイルの更新日時でソートして最新のファイルを取得
latest_csv = max(csv_files, key=os.path.getmtime)

print(f"最新のCSVファイル: {latest_csv}")
print(f"ファイルは存在しますか？: {os.path.exists(latest_csv)}")

if os.path.exists(latest_csv):
    print(f"ファイルサイズ: {os.path.getsize(latest_csv)} バイト")
    
    with open(latest_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
        print(f"全行数: {len(rows)}")
        
        if rows:
            print("\nヘッダー行:")
            print(rows[0])
            
            print("\n最初の5行のデータ:")
            for i, row in enumerate(rows[1:6]):
                print(f"行 {i+1}: {row}")
else:
    print("ファイルが見つかりません。") 