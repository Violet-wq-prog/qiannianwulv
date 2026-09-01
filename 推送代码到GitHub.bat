@echo off
chcp 65001 >nul
title 千年晤旅 - 推送代码到 GitHub
cd /d "C:\Users\34392\千年晤旅"
echo.
echo  正在推送代码到 GitHub（26MB，约 1-2 分钟）...
echo  如果弹出浏览器登录窗口，登录 Violet-wq-prog 并授权即可。
echo.
git push -u origin main
if %errorlevel%==0 (
    echo.
    echo  ==========================================
    echo    推送成功！代码已上传到 GitHub
    echo  ==========================================
) else (
    echo.
    echo  推送失败，请把上面红字截图发给我。
)
echo.
pause
