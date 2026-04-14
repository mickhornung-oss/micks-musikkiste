const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
    testDir: "./tests",
    timeout: 60_000,
    expect: {
        timeout: 20_000,
    },
    reporter: "line",
    use: {
        baseURL: "http://127.0.0.1:8011",
        headless: true,
    },
    webServer: {
        command: 'powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:ENGINE_MODE=\'mock\'; $env:SERVER_PORT=\'8011\'; ..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011"',
        cwd: "../backend",
        url: "http://127.0.0.1:8011/health",
        timeout: 120_000,
        reuseExistingServer: false,
    },
});
