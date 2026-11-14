# 1. start the server in the background, logging to files
Write-Host ">> Starting server..."
$server = Start-Process -FilePath "uv" `
    -ArgumentList "run", "python", "-u", "-m", "app.main" `
    -RedirectStandardOutput "server.log" `
    -RedirectStandardError "server.err.log" `
    -NoNewWindow -PassThru

try {
    # 2. wait until the port accepts connections (max ~10 s)
    $ready = $false
    for ($i = 0; $i -lt 100; $i++) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $c.Connect("localhost", 4221)
            $c.Close()
            $ready = $true
            break
        } catch {
            Start-Sleep -Milliseconds 100
        }
    }

    if (-not $ready) {
        Write-Host ">> Server did not start. Log:"
        Get-Content server.log, server.err.log
        exit 1
    }

    # 3. run the client tests
    Write-Host ">> Running tests..."
    uv run python ./app/test_client.py
    $result = $LASTEXITCODE

    # 4. show the server logs
    Write-Host "`n>> Server log:"
    Get-Content server.log, server.err.log
}
finally {
    # 5. stop the server and its child processes (uv spawns nested children,
    #    so walk the tree via taskkill but silence its error output too)
    cmd /c "taskkill /PID $($server.Id) /T /F >nul 2>&1"
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
}

exit $result
