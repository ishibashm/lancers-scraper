@echo off
setlocal enabledelayedexpansion

REM --- �ݒ荀�� ---
set SCRIPT_PATH=src\main.py
set BASE_OUTPUT_DIR=data\output
set KEYWORDS_FILE=keywords.txt
set GDRIVE_FOLDER_ID=1NwEcsid0OiqJYS1tRs6_EWe6BBV1dPOj
set GDRIVE_CREDENTIALS_PATH=service_account.json
REM --- �ݒ荀�ڂ����܂� ---

goto select_keyword

:select_keyword
cls
echo ===================================
echo  �����L�[���[�h�I��
echo ===================================

if not exist "%KEYWORDS_FILE%" (
    echo ERROR: %KEYWORDS_FILE% ��������܂���B
    echo %KEYWORDS_FILE% ���쐬���A1�s��1�L�[���[�h���L�q���Ă��������B
    pause
    goto end
)

set KEYWORD_COUNT=0
for /F "usebackq delims=" %%k in ("%KEYWORDS_FILE%") do (
    set /A KEYWORD_COUNT+=1
    set "KEYWORD_!KEYWORD_COUNT!=%%k"
)

if %KEYWORD_COUNT% equ 0 (
    echo ERROR: %KEYWORDS_FILE% �ɃL�[���[�h���L�q����Ă��܂���B
    pause
    goto end
)

for /L %%i in (1,1,%KEYWORD_COUNT%) do (
    echo %%i. !KEYWORD_%%i!
)
set /A EXIT_OPTION_NUM=%KEYWORD_COUNT%+1
echo !EXIT_OPTION_NUM!. �I��
echo.
set /p keyword_choice="��������L�[���[�h�̔ԍ���I�����Ă�������: "

REM ���͒l�����l�ł��邩�A����є͈͓��ł��邩���m�F
set /A test_num=0
set /A test_num=%keyword_choice% 2>nul
if errorlevel 1 (
    echo �����ȓ��͂ł��B���l����͂��Ă��������B
    pause
    goto select_keyword
)
REM ���͂��ꂽ���̂������Ȑ��l�� (��: "1a" �Ȃǂ� "1" �Ƃ��ĕ]�������̂�h��)
if not "!test_num!"=="!keyword_choice!" (
    echo �����ȓ��͂ł��B�����Ȑ��l����͂��Ă��������B
    pause
    goto select_keyword
)

if %keyword_choice% GTR 0 if %keyword_choice% LEQ %KEYWORD_COUNT% (
    set SELECTED_KEYWORD=!KEYWORD_%keyword_choice%!
    goto main_menu
) else if %keyword_choice% EQU !EXIT_OPTION_NUM! (
    goto end
) else (
    echo �����ȑI���ł��B������x���͂��Ă��������B
    pause
    goto select_keyword
)

:main_menu
cls
echo ===================================
echo  Lancers Scraper ���s���j���[
echo ===================================
echo �I�𒆂̃L�[���[�h: %SELECTED_KEYWORD%
echo.
echo 1. �������ďڍ׏����擾����
echo 2. �����̂ݎ��s����
echo 3. �ڍ׏��̂ݎ擾���� (CSV�t�@�C���w��)
echo 4. �ʂ̃L�[���[�h��I������
echo 5. �I��
echo.
set /p choice="�ԍ���I�����Ă������� (1-5): "

if "%choice%"=="1" goto search_and_details
if "%choice%"=="2" goto search_only
if "%choice%"=="3" goto details_only
if "%choice%"=="4" goto select_keyword
if "%choice%"=="5" goto end
echo �����ȑI���ł��B������x���͂��Ă��������B
pause
goto main_menu

:search_and_details
cls
echo --- �����Əڍ׏��擾���J�n���܂� ---
echo �����L�[���[�h: %SELECTED_KEYWORD%
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set SEARCH_OUTPUT_FILE=%BASE_OUTPUT_DIR%\search_results_%SELECTED_KEYWORD%_%TIMESTAMP%.csv
echo �o�̓t�@�C�� (����): %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_SEARCH=
set /p upload_gdrive_choice_search="�u%SEARCH_OUTPUT_FILE%�v(��������)��Google Drive�ɃA�b�v���[�h���܂����H (y/n): "
if /I "%upload_gdrive_choice_search%"=="y" (
    set UPLOAD_ARGS_SEARCH=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_SEARCH=python %SCRIPT_PATH% --search-query %SELECTED_KEYWORD% --output "%SEARCH_OUTPUT_FILE%" %UPLOAD_ARGS_SEARCH%
echo %PYTHON_EXEC_SEARCH%
%PYTHON_EXEC_SEARCH%
if errorlevel 1 (
    echo ���������ŃG���[���������܂����B
    goto end_pause
)

echo.
echo --- �ڍ׏��擾���J�n���܂� ---
echo ���̓t�@�C�� (�ڍ�): %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_DETAILS=
set /p upload_gdrive_choice_details="�u%SEARCH_OUTPUT_FILE%�v����擾����ڍ׏�񌋉ʂ�Google Drive�ɃA�b�v���[�h���܂����H (y/n): "
if /I "%upload_gdrive_choice_details%"=="y" (
    set UPLOAD_ARGS_DETAILS=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_DETAILS=python %SCRIPT_PATH% --scrape-urls "%SEARCH_OUTPUT_FILE%" --skip-confirm %UPLOAD_ARGS_DETAILS%
echo %PYTHON_EXEC_DETAILS%
%PYTHON_EXEC_DETAILS%
if errorlevel 1 (
    echo �ڍ׏��擾�����ŃG���[���������܂����B
)
goto end_pause

:search_only
cls
echo --- �����̂ݎ��s���܂� ---
echo �����L�[���[�h: %SELECTED_KEYWORD%
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set SEARCH_OUTPUT_FILE=%BASE_OUTPUT_DIR%\search_results_%SELECTED_KEYWORD%_%TIMESTAMP%.csv
echo �o�̓t�@�C��: %SEARCH_OUTPUT_FILE%
set UPLOAD_ARGS_SEARCH_ONLY=
set /p upload_gdrive_choice_search_only="�u%SEARCH_OUTPUT_FILE%�v��Google Drive�ɃA�b�v���[�h���܂����H (y/n): "
if /I "%upload_gdrive_choice_search_only%"=="y" (
    set UPLOAD_ARGS_SEARCH_ONLY=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_SEARCH_ONLY=python %SCRIPT_PATH% --search-query %SELECTED_KEYWORD% --output "%SEARCH_OUTPUT_FILE%" %UPLOAD_ARGS_SEARCH_ONLY%
echo %PYTHON_EXEC_SEARCH_ONLY%
%PYTHON_EXEC_SEARCH_ONLY%
if errorlevel 1 (
    echo ���������ŃG���[���������܂����B
)
goto end_pause

:details_only
cls
echo --- �ڍ׏��̂ݎ擾���܂� ---
set /p INPUT_CSV_FILE="�ڍ׏����擾����CSV�t�@�C���̃p�X����͂��Ă������� (��: data\output\your_file.csv): "
if not exist "%INPUT_CSV_FILE%" (
    echo �w�肳�ꂽ�t�@�C����������܂���: %INPUT_CSV_FILE%
    goto details_only
)
echo ���̓t�@�C��: %INPUT_CSV_FILE%
set UPLOAD_ARGS_DETAILS_ONLY=
set /p upload_gdrive_choice_details_only="�u%INPUT_CSV_FILE%�v����擾����ڍ׏�񌋉ʂ�Google Drive�ɃA�b�v���[�h���܂����H (y/n): "
if /I "%upload_gdrive_choice_details_only%"=="y" (
    set UPLOAD_ARGS_DETAILS_ONLY=--upload-gdrive --gdrive-folder-id "%GDRIVE_FOLDER_ID%" --gdrive-credentials "%GDRIVE_CREDENTIALS_PATH%"
)
set PYTHON_EXEC_DETAILS_ONLY=python %SCRIPT_PATH% --scrape-urls "%INPUT_CSV_FILE%" --skip-confirm %UPLOAD_ARGS_DETAILS_ONLY%
echo %PYTHON_EXEC_DETAILS_ONLY%
%PYTHON_EXEC_DETAILS_ONLY%
if errorlevel 1 (
    echo �ڍ׏��擾�����ŃG���[���������܂����B
)
goto end_pause

:end_pause
echo.
echo �������������܂����B
pause
:end
endlocal
