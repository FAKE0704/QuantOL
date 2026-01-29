module.exports = {
  apps: [
    {
      name: 'quantol-nextjs',
      script: 'npm',
      args: 'run dev',
      cwd: '/home/user0704/QuantOL/landing-page',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'development',
        PORT: 3000
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: './logs/pm2-nextjs-error.log',
      out_file: './logs/pm2-nextjs-out.log',
      log_file: './logs/pm2-nextjs.log',
      time: true,
      merge_logs: true
    }
  ],
  deploy: {
    production: {
      user: 'user0704',
      host: '113.45.40.20',
      ref: 'origin/main',
      repo: 'git@github.com:user0704/QuantOL.git',
      path: '/home/user0704/QuantOL/landing-page',
      'pre-deploy-local': '',
      'post-deploy': 'cd /home/user0704/QuantOL/landing-page && npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
};
