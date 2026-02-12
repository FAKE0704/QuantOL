/**
 * QuantOL PM2 Ecosystem Configuration
 *
 * 开发环境: pm2 start quantol-backend-dev quantol-nextjs-dev
 * 生产环境: pm2 start quantol-backend-prod quantol-nextjs-prod
 *
 * 部署: pm2 restart <app-name> --env <environment>
 */
module.exports = {
  apps: [
    // ==================== 后端 Backend ====================
    {
      // === 生产环境（默认） ===
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
      env_production: {
        NODE_ENV: 'production',
        PORT: 8000,
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
      // === 开发环境 ===
      name: 'quantol-backend-dev',
      script: 'uv',
      args: 'run uvicorn src.api.server:app --host 0.0.0.0 --port 8000',
      cwd: '/home/user0704/QuantOL',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'development',
        PORT: 8000,
      },
      // 日志配置：开发环境日志
      error_file: './logs/pm2-backend-dev-error.log',
      out_file: './logs/pm2-backend-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== 前端 Frontend (Next.js) ====================
    {
      // === 生产环境（默认） ===
      name: 'quantol-nextjs',
      script: 'node_modules/.bin/next',
      args: 'start',
      cwd: '/home/user0704/QuantOL-frontend',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      ignore_watch: ['node_modules', '.next', 'logs'],
      max_memory_restart: '500M',
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
      // === 开发环境 ===
      name: 'quantol-nextjs-dev',
      script: 'node_modules/.bin/next',
      args: 'dev',
      cwd: '/home/user0704/QuantOL-frontend',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      ignore_watch: ['node_modules', '.next', 'logs'],
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
      // 日志配置：开发环境日志
      error_file: './logs/pm2-nextjs-dev-error.log',
      out_file: './logs/pm2-nextjs-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== Streamlit ====================
    {
      // === 生产环境（默认） ===
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
      env_production: {
        NODE_ENV: 'production',
      STREAMLIT_SERVER_PORT: 8501,
        STREAMLIT_SERVER_URL: 'http://localhost:8501',
      },
      env: {
        NODE_ENV: 'development',
        STREAMLIT_SERVER_PORT: 8501,
        STREAMLIT_SERVER_URL: 'http://localhost:8501',
      },
      // 日志配置
      error_file: './logs/pm2-streamlit-error.log',
      out_file: './logs/pm2-streamlit-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== Nginx ====================
    {
      name: 'quantol-nginx',
      script: 'nginx',
      args: '-c /home/user0704/QuantOL/nginx.conf -p /home/user0704/QuantOL',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      env_production: {
        NODE_ENV: 'production',
      },
      env: {
        NODE_ENV: 'development',
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
