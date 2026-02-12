/**
 * QuantOL PM2 开发环境配置
 *
 * 启动: pm2 start ecosystem.dev.config.js
 * 或: pm2 start ecosystem.dev.config.js --env development
 */
const path = require('path');

const backendPath = process.env.QUANTOL_BACKEND_PATH || __dirname;
const frontendPath = process.env.QUANTOL_FRONTEND_PATH || path.join(path.dirname(backendPath), 'QuantOL-frontend');

module.exports = {
  apps: [
    // ==================== 后端 Backend ====================
    {
      name: 'quantol-backend',
      script: 'uv',
      args: 'run uvicorn src.api.server:app --host 0.0.0.0 --port 8000',
      cwd: backendPath,
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
      error_file: './logs/pm2-backend-dev-error.log',
      out_file: './logs/pm2-backend-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== 前端 Frontend (Next.js) ====================
    {
      name: 'quantol-nextjs',
      script: 'node_modules/.bin/next',
      args: 'dev',
      cwd: frontendPath,
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
      error_file: './logs/pm2-nextjs-dev-error.log',
      out_file: './logs/pm2-nextjs-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== Streamlit ====================
    {
      name: 'quantol-streamlit',
      script: 'uv',
      args: 'run streamlit run main.py --server.port 8501',
      cwd: backendPath,
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'development',
        STREAMLIT_SERVER_PORT: 8501,
        STREAMLIT_SERVER_URL: 'http://localhost:8501',
      },
      error_file: './logs/pm2-streamlit-dev-error.log',
      out_file: './logs/pm2-streamlit-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
    },

    // ==================== Nginx ====================
    {
      name: 'quantol-nginx',
      script: 'nginx',
      args: `-c ${path.join(backendPath, 'nginx.conf')} -p ${backendPath}`,
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'development',
      },
      error_file: './logs/pm2-nginx-dev-error.log',
      out_file: './logs/pm2-nginx-dev-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      time: true,
      kill_timeout: 3000,
      stop_signal: 'SIGQUIT',
    },
  ],
};
