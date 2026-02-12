#!/bin/bash
# PM2 日志管理脚本
# 功能：清理当前日志、归档旧日志、区分启动日志

set -e

PROJECT_ROOT="/home/user0704/QuantOL"
LOG_DIR="$PROJECT_ROOT/logs"
ARCHIVE_DIR="$LOG_DIR/archive"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# 1. 归档当前日志到带时间戳的文件
archive_logs() {
    local service=$1
    local log_files=("$LOG_DIR/pm2-${service}-error.log" "$LOG_DIR/pm2-${service}-out.log")

    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            local basename=$(basename "$log_file" .log)
            local archive_file="$ARCHIVE_DIR/${basename}_${TIMESTAMP}.log"
            cp "$log_file" "$archive_file"
            log_info "已归档: $log_file -> $archive_file"
        fi
    done
}

# 2. 清空当前日志文件
clear_logs() {
    local service=$1
    echo "" > "$LOG_DIR/pm2-${service}-error.log"
    echo "" > "$LOG_DIR/pm2-${service}-out.log"
    log_info "已清空 $service 的当前日志"
}

# 3. 清理超过 7 天的归档日志
cleanup_old_archives() {
    log_info "清理超过 7 天的归档日志..."
    find "$ARCHIVE_DIR" -name "*.log" -mtime +7 -delete
}

# 4. 显示日志文件大小
show_log_size() {
    local service=$1
    log_info "$service 日志文件大小:"
    ls -lh "$LOG_DIR"/pm2-${service}-*.log 2>/dev/null || echo "  无日志文件"
}

# 主函数
main() {
    local action=${1:-"archive"}
    local service=${2:-"all"}

    case $action in
        archive)
            log_info "=== 归档并清空日志 ==="
            if [ "$service" = "all" ]; then
                for svc in fastapi nextjs streamlit nginx; do
                    archive_logs "$svc"
                    clear_logs "$svc"
                done
            else
                archive_logs "$service"
                clear_logs "$service"
            fi
            cleanup_old_archives
            log_info "完成！"
            ;;
        clear)
            log_info "=== 仅清空当前日志 ==="
            if [ "$service" = "all" ]; then
                for svc in fastapi nextjs streamlit nginx; do
                    clear_logs "$svc"
                done
            else
                clear_logs "$service"
            fi
            log_info "完成！"
            ;;
        status)
            log_info "=== 日志文件状态 ==="
            if [ "$service" = "all" ]; then
                for svc in fastapi nextjs streamlit nginx; do
                    show_log_size "$svc"
                done
            else
                show_log_size "$service"
            fi
            ;;
        clean-old)
            cleanup_old_archives
            log_info "完成！"
            ;;
        *)
            echo "用法: $0 {archive|clear|status|clean-old} [service名称]"
            echo ""
            echo "命令:"
            echo "  archive [service]  - 归档当前日志并清空（默认）"
            echo "  clear [service]    - 仅清空当前日志"
            echo "  status [service]   - 显示日志文件大小"
            echo "  clean-old          - 清理超过7天的归档日志"
            echo ""
            echo "示例:"
            echo "  $0 archive          # 归档并清空所有服务日志"
            echo "  $0 archive nextjs   # 仅处理 nextjs"
            echo "  $0 clear all        # 清空所有日志"
            exit 1
            ;;
    esac
}

main "$@"
