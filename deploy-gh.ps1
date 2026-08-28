# deploy-gh.ps1 — 一键部署 index.html 到 GitHub Pages（永久公网链接）
# 用法：在「语料库」文件夹里用 PowerShell 运行  .\deploy-gh.ps1
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot; if (-not $base) { $base = (Get-Location).Path }

function Header($t){ Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function OK($t){ Write-Host $t -ForegroundColor Green }

Header "1/5 检查 GitHub CLI"
$needInstall = $false
try { gh --version | Out-Null } catch { $needInstall = $true }
if ($LASTEXITCODE -ne 0) { $needInstall = $true }
if ($needInstall) {
    Write-Host "未检测到 gh，正在用 winget 安装（约 30 秒）..." -ForegroundColor Yellow
    winget install --id GitHub.cli --silent --accept-source-agreements --accept-package-agreements | Out-Null
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    try { gh --version | Out-Null } catch { Write-Host "安装后仍找不到 gh，请手动从 https://cli.github.com 安装后重跑本脚本。" -ForegroundColor Red; exit 1 }
}
OK "GitHub CLI 就绪"

Header "2/5 登录 GitHub"
$me = $null
try { $me = gh api user --jq .login 2>$null } catch {}
if (-not $me -or $LASTEXITCODE -ne 0) {
    Write-Host "需要在浏览器完成一次登录。接下来会显示一个 8 位验证码，并自动打开 github.com/login/device" -ForegroundColor Yellow
    Write-Host "请在浏览器粘贴验证码并授权，然后回到这里。" -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web
    $me = gh api user --jq .login
}
OK "已登录：$me"

Header "3/5 准备仓库"
$repo = Read-Host "仓库名（回车默认 zhongfa-yuliao）"
if (-not $repo) { $repo = 'zhongfa-yuliao' }
OK "仓库名：$repo"

Header "4/5 创建仓库并推送 index.html"
$staging = Join-Path $env:TEMP "gh_deploy_$repo"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging -Force | Out-Null
Copy-Item (Join-Path $base 'index.html') $staging -Force
Set-Location $staging
git init -b main 2>&1 | Out-Null
if (-not (git config user.name)) { git config user.name $me }
if (-not (git config user.email)) { git config user.email "$me@users.noreply.github.com" }
git add index.html
git commit -m "deploy: 中法对照古典语料库 · 五经 · 2700 条中法对照" 2>&1 | Out-Null
$remote = "https://github.com/$me/$repo.git"
$created = $false
try {
    gh repo create $repo --public --source=. --remote=origin --push 2>&1 | Out-Null
    $created = $true
} catch {}
if (-not $created) {
    Write-Host "仓库可能已存在，直接推送..." -ForegroundColor Yellow
    git remote remove origin 2>$null | Out-Null
    git remote add origin $remote
    git pull --rebase origin main 2>&1 | Out-Null
    git push -u origin main 2>&1 | Out-Null
}
OK "已推送到 $remote"

Header "5/5 开启 GitHub Pages"
try {
    gh api --method POST "/repos/$me/$repo/pages" -f "source[branch]=main" -f "source[path]=/" 2>&1 | Out-Null
} catch {}
Start-Sleep 4
$url = $null
try { $url = gh api "/repos/$me/$repo/pages" --jq .html_url 2>$null } catch {}
if (-not $url) { $url = "https://$me.github.io/$repo/" }
Write-Host ""
Write-Host "永久公网链接（GitHub 首次构建约需 30-90 秒生效）：" -ForegroundColor Green
Write-Host "    $url" -ForegroundColor White
Write-Host ""
Write-Host "各典籍直达：" -ForegroundColor DarkGray
Write-Host "    门户：  $url" -ForegroundColor DarkGray
Write-Host "    诗经：  ${url}index.html#shijing" -ForegroundColor DarkGray
Write-Host "    尚书：  ${url}index.html#shangshu" -ForegroundColor DarkGray
Write-Host "    礼记：  ${url}index.html#liji" -ForegroundColor DarkGray
Write-Host "    易经：  ${url}index.html#yijing" -ForegroundColor DarkGray
Write-Host "    春秋：  ${url}index.html#chunqiu" -ForegroundColor DarkGray
Write-Host ""
Write-Host "部署完成。请把上面这个永久链接发给我，我来验证是否可访问。" -ForegroundColor Green
Set-Location $base
