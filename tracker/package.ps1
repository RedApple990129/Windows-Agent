# 0. clean ./dist/ folder (if exists)
$distPath = "./dist"
if (Test-Path $distPath)
{
    Remove-Item -Path $distPath -Recurse -Force
    Write-Output "dist folder cleared."
}
else
{
    Write-Output "dist folder does not exist, skipping clearing."
}

# 1. run pyinstaller
pyinstaller main.spec

# 2. check if ./dist/tracker.exe is generated
if (Test-Path "./dist/tracker.exe")
{
    Write-Output "tracker.exe successfully created."
}
else
{
    Write-Output "Error: tracker.exe not created."
    exit 1
}

# 3. copy ./tasks.json and ./README.md to ./dist/
Copy-Item -Path "./tasks.json" -Destination "./dist/" -Force
Copy-Item -Path "./README.md" -Destination "./dist/" -Force

# 4. copy ./task_cnt.json to ./dist/
Copy-Item -Path "./task_cnt.json" -Destination "./dist/" -Force

Write-Output "./dist/ successfully prepared, ready for zip."
