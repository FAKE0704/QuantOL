/**
 * QuantOL PM2 Ecosystem Configuration
 *
 * 日志管理策略：
 * 1. merge_logs: false - 每次重启不追加旧日志
 * 2. pm2-logrotate - 自动按日期/大小轮转，保留7天
 * 3. 使用 pm2 flush 清空当前日志
 *
 * 重启前清空日志：pm2 flush <app-name> && pm2 restart <app-name>
 */
module.exports = {
  apps: [
    {
      name: 'quantol-backend',
      script: 'uv',
      args: 'run uvicorn src.api.server:app --host 0.0.0.0 --port 8000',
      cwd: '/home/user0704/QuantOL',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env_development: {
        NODE_ENV: 'development',
      },
      env_production: {
        NODE_ENV: 'production',
      },
      // 日志配置：不合并旧日志，带时间戳
      error_file: './logs/pm2-backend-error.log',
      out_file: './logs/pm2-backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
      wait_ready: true,
      kill_timeout: 5000,
      listen_timeout: 10000,
    },
    {
      name: 'quantol-nextjs',
      script: 'node_modules/.bin/next',
      args: 'start',
      cwd: '/home/user0704/QuantOL/landing-page',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      ignore_watch: ['node_modules', '.next', 'logs'],
      max_memory_restart: '500M',
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000,
        args: 'dev',
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      // 日志配置：不合并旧日志
      error_file: './logs/pm2-nextjs-error.log',
      out_file: './logs/pm2-nextjs-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
      post_update: ['npm run build'],
      kill_timeout: 5000,
    },
    {
      name: 'quantol-streamlit',
      script: 'uv',
      args: 'run streamlit run main.py --server.port 8501',
      cwd: '/home/user0704/QuantOL',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env_development: {
        NODE_ENV: 'development',
      },
      env_production: {
        NODE_ENV: 'production',
      },
      // 日志配置
      error_file: './logs/pm2-streamlit-error.log',
      out_file: './logs/pm2-streamlit-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
      kill_timeout: 5000,
    },
    {
      name: 'quantol-nginx',
      script: 'nginx',
      args: '-c /home/user0704/QuantOL/nginx.conf -p /home/user0704/QuantOL',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      env_development: {
        NODE_ENV: 'development',
      },
      env_production: {
        NODE_ENV: 'production',
      },
      // 日志配置
      error_file: './logs/pm2-nginx-error.log',
      out_file: './logs/pm2-nginx-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
      kill_timeout: 3000,
      stop_signal: 'SIGQUIT',
    },
  ],
};
