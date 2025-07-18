@echo off
REM フラクタルエディタ統合テスト実行バッチファイル
REM Windows環境での統合テスト実行を簡単にするためのスクリプト

echo ========================================
echo フラクタルエディタ統合テストスイート
echo ========================================
echo.

REM Python環境の確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonが見つかりません。
    echo Pythonをインストールしてから再実行してください。
    pause
    exit /b 1
)

echo Python環境を確認しました。
echo.

REM 必要な依存関係の確認
echo 依存関係を確認中...
python -c "import numpy, PyQt6, psutil" >nul 2>&1
if errorlevel 1 (
    echo 警告: 一部の依存関係が不足している可能性があります。
    echo 以下のコマンドで依存関係をインストールしてください:
    echo pip install numpy PyQt6 psutil Pillow
    echo.
    echo 続行しますか？ ^(Y/N^)
    set /p continue=
    if /i not "%continue%"=="Y" (
        echo テストを中止しました。
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo テスト実行オプション
echo ========================================
echo 1. 統合テスト検証のみ実行 ^(推奨・高速^)
echo 2. 基本統合テスト実行
echo 3. UI応答性テスト実行
echo 4. 全統合テスト実行 ^(時間がかかります^)
echo 5. テスト結果分析
echo.
set /p choice=選択してください ^(1-5^): 

if "%choice%"=="1" goto verify_tests
if "%choice%"=="2" goto basic_tests
if "%choice%"=="3" goto ui_tests
if "%choice%"=="4" goto full_tests
if "%choice%"=="5" goto analyze_results
echo 無効な選択です。
pause
exit /b 1

:verify_tests
echo.
echo ========================================
echo 統合テスト検証を実行中...
echo ========================================
python test_integration_verification.py
if errorlevel 1 (
    echo.
    echo テスト検証に失敗しました。
    echo 詳細なエラー情報を確認してください。
) else (
    echo.
    echo テスト検証が成功しました！
)
goto end

:basic_tests
echo.
echo ========================================
echo 基本統合テストを実行中...
echo ========================================
python test_integration_comprehensive.py
if errorlevel 1 (
    echo.
    echo 基本統合テストに失敗しました。
) else (
    echo.
    echo 基本統合テストが成功しました！
)
goto end

:ui_tests
echo.
echo ========================================
echo UI応答性テストを実行中...
echo ========================================
python test_ui_responsiveness_integration.py
if errorlevel 1 (
    echo.
    echo UI応答性テストに失敗しました。
) else (
    echo.
    echo UI応答性テストが成功しました！
)
goto end

:full_tests
echo.
echo ========================================
echo 全統合テストを実行中...
echo ========================================
echo 注意: この処理には数分かかる場合があります。
echo.
python run_integration_tests.py
if errorlevel 1 (
    echo.
    echo 統合テストに失敗しました。
    echo 詳細はintegration_test_report_*.jsonファイルを確認してください。
) else (
    echo.
    echo 全統合テストが成功しました！
)
goto end

:analyze_results
echo.
echo ========================================
echo テスト結果を分析中...
echo ========================================
python analyze_test_results.py
if errorlevel 1 (
    echo.
    echo テスト結果の分析に失敗しました。
    echo テストレポートファイルが存在することを確認してください。
) else (
    echo.
    echo テスト結果の分析が完了しました！
)
goto end

:end
echo.
echo ========================================
echo 処理が完了しました
echo ========================================
echo.
echo 生成されたファイル:
if exist integration_test_report_*.json (
    echo   - 統合テストレポート: integration_test_report_*.json
)
if exist test_analysis_report_*.txt (
    echo   - 分析レポート: test_analysis_report_*.txt
)
if exist test_analysis_data_*.json (
    echo   - 分析データ: test_analysis_data_*.json
)
echo.
echo 詳細な情報については、INTEGRATION_TEST_GUIDE.mdを参照してください。
echo.
pause