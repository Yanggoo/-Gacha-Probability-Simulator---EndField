@echo off
chcp 65001 >nul
echo ========================================
echo 明日方舟·终末地 抽卡模拟器 - 打包工具
echo ========================================
echo.

echo [1/4] 检查PyInstaller是否已安装...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 安装失败，请检查网络连接或手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
) else (
    echo PyInstaller已安装
)
echo.

echo [2/4] 清理旧的打包文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo 清理完成
echo.

echo [3/4] 开始打包程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --name="明日方舟终末地抽卡模拟器" ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    ui_main.py

if %errorlevel% neq 0 (
    echo.
    echo 打包失败！请查看上方错误信息
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo ========================================
echo 可执行文件位置: dist\明日方舟终末地抽卡模拟器.exe
echo 文件大小: 
for %%A in ("dist\明日方舟终末地抽卡模拟器.exe") do echo %%~zA 字节 (约 %%~zA / 1048576 MB)
echo ========================================
echo.
echo 提示：
echo 1. 生成的exe文件在 dist 文件夹中
echo 2. 可以在任何Windows电脑上运行，无需安装Python
echo 3. 首次运行可能需要几秒钟解压（如果使用--onefile模式）
echo 4. 程序会在运行目录生成PNG图片文件
echo.
echo 按任意键打开dist文件夹...
pause >nul
explorer "dist"
