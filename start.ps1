# MapTools 轨迹匹配系统启动脚本
# 使用方法: 在项目根目录运行 .\start.ps1

Write-Host "==================================================" -ForegroundColor Green
Write-Host "MapTools 轨迹匹配系统启动脚本" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# 检查环境
Write-Host "[1/5] 检查环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到Python环境" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到Node.js环境" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

try {
    $javaVersion = java -version 2>&1
    Write-Host "✓ Java: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到Java环境" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

try {
    $mvnVersion = mvn -version 2>&1
    Write-Host "✓ Maven: $mvnVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到Maven环境" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 启动MongoDB服务
Write-Host ""
Write-Host "[2/5] 启动MongoDB服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "mongod --config mongod.conf" -WindowStyle Minimized
Write-Host "✓ MongoDB服务启动中..." -ForegroundColor Green

# 等待MongoDB启动
Write-Host ""
Write-Host "[3/5] 等待MongoDB服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 启动后端服务
Write-Host ""
Write-Host "[4/5] 启动后端服务..." -ForegroundColor Yellow
Set-Location "BackendService"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uv run python main.py" -WindowStyle Normal
Write-Host "✓ 后端服务启动中..." -ForegroundColor Green

# 等待后端启动
Write-Host ""
Write-Host "[5/5] 等待后端服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# 启动前端服务
Write-Host ""
Write-Host "启动前端服务..." -ForegroundColor Yellow
Set-Location "..\FrontendApp"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm start" -WindowStyle Normal
Write-Host "✓ 前端服务启动中..." -ForegroundColor Green

# 启动Java工具（在新窗口中）
Write-Host ""
Write-Host "启动Java数据处理工具..." -ForegroundColor Yellow
Set-Location "..\JavaToolScripts"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "mvn clean package" -WindowStyle Normal
Write-Host "✓ Java工具编译中..." -ForegroundColor Green

# 返回根目录
Set-Location ".."

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "服务启动完成！" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "MongoDB服务: mongodb://localhost:27017" -ForegroundColor Cyan
Write-Host "后端服务: http://localhost:8000" -ForegroundColor Cyan
Write-Host "前端服务: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# 等待用户确认
Read-Host "按回车键关闭此窗口"