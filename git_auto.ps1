#!/usr/bin/env pwsh

# 检查是否提供了提交信息
if ($args.Count -eq 0) {
    Write-Host "请提供提交信息。用法: ./git_auto.ps1 '提交信息'"
    exit 1
}

# 添加所有更改
git add .

# 提交更改，使用用户提供的提交信息
git commit -m $args[0]

# 推送到远程仓库
git push