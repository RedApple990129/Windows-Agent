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

# 3. copy ./__files__/ folder to ./dist/
Copy-Item -Path "./__files__" -Destination "./dist/" -Recurse -Force

# 4. copy ./tasks.json and ./README.md to ./dist/
Copy-Item -Path "./tasks.json" -Destination "./dist/" -Force
Copy-Item -Path "./README.md" -Destination "./dist/" -Force

# 4+. copy ./task_cnt.json to ./dist/
Copy-Item -Path "./task_cnt.json" -Destination "./dist/" -Force

# 5. set ./dist/tasks.json to hidden
$taskJsonPath = "./dist/tasks.json"
if (Test-Path $taskJsonPath)
{
    # set hidden attribute
    Set-ItemProperty -Path $taskJsonPath -Name Attributes -Value ([System.IO.FileAttributes]::Hidden)
    Write-Output "tasks.json is now hidden."
}
else
{
    Write-Output "Error: tasks.json not found in ./dist/."
    exit 1
}

# 5+. set ./dist/task_cnt.json to hidden
$taskJsonPath = "./dist/task_cnt.json"
if (Test-Path $taskJsonPath)
{
    # set hidden attribute
    Set-ItemProperty -Path $taskJsonPath -Name Attributes -Value ([System.IO.FileAttributes]::Hidden)
    Write-Output "task_cnt.json is now hidden."
}
else
{
    Write-Output "Error: task_cnt.json not found in ./dist/."
    exit 1
}

# 6. set ./dist/__files__/ folder to hidden
$filesPath = "./dist/__files__"
if (Test-Path $filesPath)
{
    # set hidden attribute
    Set-ItemProperty -Path $filesPath -Name Attributes -Value ([System.IO.FileAttributes]::Hidden)
    Write-Output "__files__ is now hidden and read-only."
}
else
{
    Write-Output "Error: __files__ not found in ./dist/."
    exit 1
}

# 7. check if ./files folder exists, if so, copy it to ./dist/
$optionalFilesPath = "./files"
if (Test-Path $optionalFilesPath)
{
    Copy-Item -Path $optionalFilesPath -Destination "./dist/" -Recurse -Force
    Write-Output "files directory copied to ./dist/."
}
else
{
    Write-Output "files directory not found, skipping."
}

Write-Output "./dist/ successfully prepared, ready for zip."
