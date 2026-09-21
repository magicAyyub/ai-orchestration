module.exports = {
  apps: [
    {
      name: 'jumbo-ai-orchestration',
      script: 'uv',
      args: 'run uvicorn --app-dir src ai_orchestration.server:app --host 127.0.0.1 --port 8000',
      cwd: './',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        LOG_LEVEL: 'INFO',
      },
    },
  ],
};
