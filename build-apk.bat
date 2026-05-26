@echo off
chcp 65001 >nul
echo ===== 远行商人 APK 构建脚本 =====
echo.

REM Check Java
where java >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Java，请先安装 JDK 17+
    echo 下载：https://adoptium.net/temurin/releases/?version=17
    pause
    exit /b 1
)
echo [OK] Java 已安装
java -version

REM Check Android SDK
if not exist "%ANDROID_HOME%" (
    if not exist "%ANDROID_SDK_ROOT%" (
        echo [警告] 未设置 ANDROID_HOME 或 ANDROID_SDK_ROOT
        echo 请设置 Android SDK 路径，例如：
        echo   set ANDROID_HOME=C:\Users\你的用户名\AppData\Local\Android\Sdk
        pause
        exit /b 1
    )
)

echo.
echo ===== 开始构建 Debug APK =====
cd /d %~dp0android
call gradlew.bat assembleDebug

if errorlevel 1 (
    echo.
    echo [失败] 构建出错，请检查上面的错误信息
    pause
    exit /b 1
)

echo.
echo ===== 构建成功！ =====
echo APK 位置：
echo %~dp0android\app\build\outputs\apk\debug\app-debug.apk
echo.
pause
