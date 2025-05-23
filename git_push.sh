#!/bin/bash

# 检查是否提供了提交信息
if [ -z "$1" ]; then
  echo "Usage: ./git_push.sh 'commit message'"
  exit 1
fi

# 添加所有更改到暂存区
git add .

# 提交更改
git commit -m "$1"

# 推送到远程仓库
git push origin main
