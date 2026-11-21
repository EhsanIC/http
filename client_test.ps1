# 0. prepare a directory for the /files tests (inside the project)
$dir = Join-Path $PWD "test_files_dir"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

# start with a fresh combined-results file (each suite appends to it)
Remove-Item "test_results.txt" -ErrorAction SilentlyContinue

# 1. start the server in the background, logging to files
Write-Host ">> Starting server..."
$server = Start-Process -FilePath "uv" `
    -ArgumentList "run", "python", "-u", "-m", "app.main", "--directory", "`"$dir`"" `
    -RedirectStandardOutput "server.log" `
    -RedirectStandardError "server.err.log" `
    -NoNewWindow -PassThru

$result = 0

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
    uv run python ./test/test_client.py
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    Write-Host "`n>> Running concurrency test..."
    uv run python ./test/test_concurrent.py
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    Write-Host "`n>> Running files test..."
    uv run python ./test/test_files.py "$dir"
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    Write-Host "`n>> Running POST files test..."
    uv run python ./test/test_post_files.py "$dir"
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    Write-Host "`n>> Running persistent connection test..."
    uv run python ./test/test_persistent.py
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    Write-Host "`n>> Running connection close test..."
    uv run python ./test/test_connection_close.py
    if ($LASTEXITCODE -ne 0) { $result = 1 }

    # 4. big combined summary of every suite, right before the server log
    if (Test-Path "test_results.txt") {
        $lines = Get-Content "test_results.txt"
        $passedCount = @($lines | Where-Object { $_ -like "PASS*" }).Count
        $failedCount = @($lines | Where-Object { $_ -like "FAIL*" }).Count
        $totalCount = $passedCount + $failedCount

        Write-Host ""
        Write-Host "==================================================" -ForegroundColor Cyan
        Write-Host "  ALL TESTS SUMMARY" -ForegroundColor Cyan
        Write-Host "==================================================" -ForegroundColor Cyan
        foreach ($line in $lines) {
            $text = $line -replace "`t", "  "
            if ($line -like "PASS*") {
                Write-Host "  $text" -ForegroundColor Green
            } elseif ($line -like "FAIL*") {
                Write-Host "  $text" -ForegroundColor Red
            }
        }
        Write-Host "==================================================" -ForegroundColor Cyan
        $totalColor = if ($failedCount -gt 0) { "Red" } else { "Green" }
        Write-Host "  TOTAL: $passedCount/$totalCount passed" -ForegroundColor $totalColor
        Write-Host "==================================================" -ForegroundColor Cyan
    }

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
