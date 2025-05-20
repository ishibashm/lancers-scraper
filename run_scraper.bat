@echo off
setlocal enabledelayedexpansion

REM --- 設定項目 ---
set SCRIPT_PATH=src\main.py
set BASE_OUTPUT_DIR=data\output
set KEYWORDS_FILE=keywords.txt
set GDRIVE_FOLDER_ID=1NwEcsid0OiqJYS1tRs6_EWe6BBV1dPOj
set GDRIVE_CREDENTIALS_PATH=service_account.json
REM --- 設定項目ここまで ---

goto top_menu

:top_menu
cls
echo ===================================
echo  Lancers Scraper メインメニュー
echo ===================================
echo 1. キーワードを選択して検索・処理を行う
echo 2. 既存CSVから詳細情報を直接取得する
echo 3. 終了
echo.
set /p top_choice="番号を選択してください (1-3): "

if "%top_choice%"=="1" goto select_keyword_initial
if "%top_choice%"=="2" goto details_direct
if "%top_choice%"=="3" goto end
echo 無効な選択です。もう一度入力してください。
pause
goto top_menu

:select_keyword_initial
REM キーワード選択とそれに続く処理の開始点
goto select_keyword

:select_keyword
cls
echo ===================================
echo  検索キーワード選択
echo ===================================

if not exist "%KEYWORDS_FILE%" (
    echo ERROR: %KEYWORDS_FILE% が見つかりません。
    echo %KEYWORDS_FILE% を作成し、1行に1つキーワードを記述してください。
    pause
    goto end
)

set KEYWORD_COUNT=0
for /F "usebackq delims=" %%k in ("%KEYWORDS_FILE%") do (
    set /A KEYWORD_COUNT+=1
    set "KEYWORD_!KEYWORD_COUNT!=%%k"
)

if %KEYWORD_COUNT% equ 0 (
    echo ERROR: %KEYWORDS_FILE% にキーワードが記述されていません。
    pause
    goto end
)

for /L %%i in (1,1,%KEYWORD_COUNT%) do (
    echo %%i. !KEYWORD_%%i!
)
set /A EXIT_OPTION_NUM=%KEYWORD_COUNT%+1
echo !EXIT_OPTION_NUM!. 終了
echo.
set /p keyword_choice="検索するキーワードの番号を選択してください: "

REM 入力値が数値であるか、および範囲内であるかを確認
set /A test_num=0
set /A test_num=%keyword_choice% 2>nul
if errorlevel 1 (
    echo 無効な入力です。数値を入力してください。
    pause
    goto select_keyword
)
REM 入力されたものが純粋な数値か (例: "1a" などが "1" として評価されるのを防ぐ)
if not "!test_num!"=="!keyword_choice!" (
    echo 無効な入力です。純粋な数値を入力してください。
    pause
    goto select_keyword
)

if %keyword_choice% GTR 0 if %keyword_choice% LEQ %KEYWORD_COUNT% (
    set SELECTED_KEYWORD=!KEYWORD_%keyword_choice%!
    goto operation_menu_after_keyword_selection
) else if %keyword_choice% EQU !EXIT_OPTION_NUM! (
    goto top_menu REM 終了ではなくトップメニューに戻る
) else (
    echo 無効な選択です。もう一度入力してください。
    pause
    goto select_keyword
)

:operation_menu_after_keyword_selection
cls
echo ===================================
echo  操作選択 (キーワード: %SELECTED_KEYWORD%)
echo ===================================
echo 1. 検索して詳細情報を取得する
echo 2. 検索のみ実行する
echo 3. (このキーワードで)詳細情報のみ取得する (CSVファイル指定)
echo 4. 別のキーワードを選択する (キーワード選択へ戻る)
echo 5. メインメニューへ戻る
echo 6. 終了
echo.
set /p choice="番号を選択してください (1-6): "

if "%choice%"=="1" goto search_and_details
if "%choice%"=="2" goto search_only
if "%choice%"=="3" goto details_only_with_keyword
if "%choice%"=="4" goto select_keyword
if "%choice%"=="5" goto top_menu
if "%choice%"=="6" goto end
echo 無効な選択です。もう一度入力してください。
pause
goto operation_menu_after_keyword_selection

:search_and_details
cls
echo --- 検索と詳細情報取得を開始します ---
echo 検索キーワード: %SELECTED_KEYWORD%
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set SEARCH_OUTPUT_FILE=%BASE_OUTPUT_DIR%\search_results_%SELECTED_KEYWORD%_%TIMESTAMP%.csv
echo 出力ファイル (検索): %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_SEARCH=
set /p upload_gdrive_choice_search="「%SEARCH_OUTPUT_FILE%」(検索結果)をGoogle Driveにアップロードしますか？ (y/n/0でキャンセル): "
if "%upload_gdrive_choice_search%"=="0" goto top_menu
if /I "%upload_gdrive_choice_search%"=="y" (
    set UPLOAD_ARGS_SEARCH=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_SEARCH=python %SCRIPT_PATH% --search-query %SELECTED_KEYWORD% --output "%SEARCH_OUTPUT_FILE%" %UPLOAD_ARGS_SEARCH%
echo %PYTHON_EXEC_SEARCH%
%PYTHON_EXEC_SEARCH%
if errorlevel 1 (
    echo 検索処理でエラーが発生しました。
    goto end_pause
)

echo.
echo --- 詳細情報取得を開始します ---
echo 入力ファイル (詳細): %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_DETAILS=
set /p upload_gdrive_choice_details="「%SEARCH_OUTPUT_FILE%」から取得する詳細情報結果をGoogle Driveにアップロードしますか？ (y/n/0でキャンセル): "
if "%upload_gdrive_choice_details%"=="0" goto top_menu
if /I "%upload_gdrive_choice_details%"=="y" (
    set UPLOAD_ARGS_DETAILS=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_DETAILS=python %SCRIPT_PATH% --scrape-urls "%SEARCH_OUTPUT_FILE%" --skip-confirm %UPLOAD_ARGS_DETAILS%
echo %PYTHON_EXEC_DETAILS%
%PYTHON_EXEC_DETAILS%
if errorlevel 1 (
    echo 詳細情報取得処理でエラーが発生しました。
)
goto end_pause_and_return

:search_only
cls
echo --- 検索のみ実行します ---
echo 検索キーワード: %SELECTED_KEYWORD%
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set SEARCH_OUTPUT_FILE=%BASE_OUTPUT_DIR%\search_results_%SELECTED_KEYWORD%_%TIMESTAMP%.csv
echo 出力ファイル: %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_SEARCH_ONLY=
set /p upload_gdrive_choice_search_only="「%SEARCH_OUTPUT_FILE%」をGoogle Driveにアップロードしますか？ (y/n/0でキャンセル): "
if "%upload_gdrive_choice_search_only%"=="0" goto top_menu
if /I "%upload_gdrive_choice_search_only%"=="y" (
    set UPLOAD_ARGS_SEARCH_ONLY=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_SEARCH_ONLY=python %SCRIPT_PATH% --search-query %SELECTED_KEYWORD% --output "%SEARCH_OUTPUT_FILE%" %UPLOAD_ARGS_SEARCH_ONLY%
echo %PYTHON_EXEC_SEARCH_ONLY%
%PYTHON_EXEC_SEARCH_ONLY%
if errorlevel 1 (
    echo 検索処理でエラーが発生しました。
)
goto end_pause_and_return

:details_direct
cls
echo --- 既存CSVから詳細情報を直接取得します ---
set /p INPUT_CSV_FILE="詳細情報を取得するCSVファイルのパスを入力してください (例: data\output\your_file.csv) (キャンセル:0を入力): "
if "%INPUT_CSV_FILE%"=="0" goto top_menu
if not exist "%INPUT_CSV_FILE%" (
    echo 指定されたファイルが見つかりません: %INPUT_CSV_FILE%
    pause
    goto details_direct
)
echo 入力ファイル: %INPUT_CSV_FILE%
set UPLOAD_ARGS_DETAILS_DIRECT=
set /p upload_gdrive_choice_details_direct="「%INPUT_CSV_FILE%」から取得する詳細情報結果をGoogle Driveにアップロードしますか？ (y/n/0でキャンセル): "
if "%upload_gdrive_choice_details_direct%"=="0" goto top_menu
if /I "%upload_gdrive_choice_details_direct%"=="y" (
    set UPLOAD_ARGS_DETAILS_DIRECT=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_DETAILS_DIRECT=python %SCRIPT_PATH% --scrape-urls "%INPUT_CSV_FILE%" --skip-confirm %UPLOAD_ARGS_DETAILS_DIRECT%
echo %PYTHON_EXEC_DETAILS_DIRECT%
%PYTHON_EXEC_DETAILS_DIRECT%
if errorlevel 1 (
    echo 詳細情報取得処理でエラーが発生しました。
)
goto end_pause_and_return

:details_only_with_keyword
cls
echo --- 詳細情報のみ取得します (キーワード: %SELECTED_KEYWORD% での作業中ですが、CSVは直接指定) ---
set /p INPUT_CSV_FILE="詳細情報を取得するCSVファイルのパスを入力してください (例: data\output\your_file.csv) (キャンセル:0を入力): "
if "%INPUT_CSV_FILE%"=="0" goto operation_menu_after_keyword_selection
if not exist "%INPUT_CSV_FILE%" (
    echo 指定されたファイルが見つかりません: %INPUT_CSV_FILE%
    pause
    goto details_only_with_keyword
)
echo 入力ファイル: %INPUT_CSV_FILE%
set UPLOAD_ARGS_DETAILS_ONLY=
set /p upload_gdrive_choice_details_only="「%INPUT_CSV_FILE%」から取得する詳細情報結果をGoogle Driveにアップロードしますか？ (y/n/0でキャンセル): "
if "%upload_gdrive_choice_details_only%"=="0" goto operation_menu_after_keyword_selection
if /I "%upload_gdrive_choice_details_only%"=="y" (
    set UPLOAD_ARGS_DETAILS_ONLY=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_DETAILS_ONLY=python %SCRIPT_PATH% --scrape-urls "%INPUT_CSV_FILE%" --skip-confirm %UPLOAD_ARGS_DETAILS_ONLY%
echo %PYTHON_EXEC_DETAILS_ONLY%
%PYTHON_EXEC_DETAILS_ONLY%
if errorlevel 1 (
    echo 詳細情報取得処理でエラーが発生しました。
)
goto end_pause_and_return

:end_pause_and_return
echo.
echo 処理が完了しました。
pause
goto top_menu REM 処理完了後はトップメニューに戻る

:end_pause
echo.
echo 処理が完了しました。
pause
goto end REM このend_pauseはエラー時などに使われる想定で、終了する

:end
endlocal
