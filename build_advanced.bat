@echo off
chcp 65001 >nul
echo ========================================
echo 明日方舟·终末地 抽卡模拟器 - 高级打包
echo ========================================
echo.
echo 此版本会生成文件夹形式的可执行程序
echo 优点: 启动更快，体积更小
echo 缺点: 需要分发整个文件夹
echo.

echo [1/4] 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)
echo.

echo [2/4] 清理旧文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo.

echo [3/4] 打包中...
pyinstaller --name="明日方舟终末地抽卡模拟器" ^
    --windowed ^
    --clean ^
    --noconfirm ^
    ui_main.py

if %errorlevel% neq 0 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo [4/4] 完成！
echo.
echo 程序位置: dist\明日方舟终末地抽卡模拟器\明日方舟终末地抽卡模拟器.exe
echo.
echo 分发时请将整个"明日方舟终末地抽卡模拟器"文件夹打包
echo.
pause
explorer "dist"
