# Qualify SP completion and adapt only the installed SK executor seam.
param([string]$NativeCommand = "", [string]$Actor = "")
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common-actor-resolution.ps1')
. (Join-Path $PSScriptRoot 'bridge-state.ps1')
function Refuse-Convergence([string]$Reason) {
    [ordered]@{ eligible = $false; reason = $Reason } | ConvertTo-Json -Compress
    exit 1
}
try {
    $root = (Get-Location).Path
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitRoot = & git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $gitRoot) { $root = [string]$gitRoot }
    }
    $root = [IO.Path]::GetFullPath($root).TrimEnd('\', '/')
    $rootPrefix = $root + [IO.Path]::DirectorySeparatorChar
    $Actor = Resolve-BridgeActor -Argument $Actor
    $handoffPath = Join-Path $root '.specify/superpowers-handoff.json'
    if (-not (Test-Path -LiteralPath $handoffPath -PathType Leaf)) { Refuse-Convergence 'Missing completed Superpowers handoff.' }
    $state = Get-Content -LiteralPath $handoffPath -Raw | ConvertFrom-Json
    if ($state.status -ne 'complete' -or $state.executor -ne 'superpowers' -or [string]::IsNullOrWhiteSpace($state.feature_directory)) {
        Refuse-Convergence 'Convergence requires a completed Superpowers handoff with a feature directory.'
    }
    $feature = [string]$state.feature_directory
    if ([IO.Path]::IsPathRooted($feature)) { Refuse-Convergence 'The completed feature must be inside this repository.' }
    $featureFull = [IO.Path]::GetFullPath((Join-Path $root $feature))
    if (-not $featureFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { Refuse-Convergence 'The completed feature must be inside this repository.' }
    if (-not (Test-Path -LiteralPath $featureFull -PathType Container)) { Refuse-Convergence 'The completed feature directory does not exist.' }
    $featurePointer = Join-Path $root '.specify/feature.json'
    if (Test-Path -LiteralPath $featurePointer -PathType Leaf) {
        $current = (Get-Content -LiteralPath $featurePointer -Raw | ConvertFrom-Json).feature_directory
        if (-not [string]::IsNullOrWhiteSpace($current)) {
            $currentFull = if ([IO.Path]::IsPathRooted($current)) { [IO.Path]::GetFullPath($current) } else { [IO.Path]::GetFullPath((Join-Path $root $current)) }
            if (-not $currentFull.Equals($featureFull, [StringComparison]::OrdinalIgnoreCase)) { Refuse-Convergence 'Active feature pointer does not match the completion.' }
        }
    }
    foreach ($artifact in @('spec.md', 'plan.md', 'tasks.md')) {
        $path = Join-Path $featureFull $artifact
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Refuse-Convergence "Missing required Spec Kit artifact: $artifact." }
        $key = [IO.Path]::GetFileNameWithoutExtension($artifact)
        if ($state.source_of_truth.$key -ne "$feature/$artifact") { Refuse-Convergence "Source-of-truth pointer mismatch: $artifact." }
        $stored = $state.artifacts_sha256.$artifact
        if ($stored -notmatch '^[0-9a-f]{64}$') { Refuse-Convergence "Missing completion artifact hash: $artifact." }
        if ($stored -ne (Get-ArtifactSha256 -Path $path)) { Refuse-Convergence "Artifact changed since completion: $artifact." }
    }
    $tasksPath = Join-Path $featureFull 'tasks.md'
    if ((Get-PendingTaskCount -TasksPath $tasksPath).Count -ne 0) { Refuse-Convergence 'Non-deferred tasks remain pending; execute them through the bridge first.' }
    if (-not (Select-String -LiteralPath $tasksPath -Pattern '^- \[[ xX]\] T\d+')) { Refuse-Convergence 'The task contract has no canonical task IDs.' }
    $eventsPath = Join-Path $root '.specify/bridge-events.jsonl'
    if (-not (Test-Path -LiteralPath $eventsPath -PathType Leaf)) { Refuse-Convergence 'Missing Superpowers execution/completion events.' }
    $snapshot = $state.last_snapshot_id
    if ([string]::IsNullOrWhiteSpace($snapshot)) { Refuse-Convergence 'Missing completion snapshot identity.' }
    $events = @(Get-Content -LiteralPath $eventsPath | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.action -eq 'handoff' -and $_.feature_directory -eq $feature })
    if ($events.Count -lt 2 -or $events[-1].status -ne 'complete' -or $events[-1].snapshot_id -ne $snapshot -or -not @($events[0..($events.Count - 2)] | Where-Object { $_.status -eq 'executing' }).Count) {
        Refuse-Convergence 'No matching executing-to-complete event sequence for this snapshot.'
    }
    if ([string]::IsNullOrWhiteSpace($NativeCommand)) {
        if ($Actor -eq 'codex') { $NativeCommand = Join-Path $root '.agents/skills/speckit-converge/SKILL.md' }
        elseif ($Actor -eq 'claude') { $NativeCommand = Join-Path $root '.claude/skills/speckit-converge/SKILL.md' }
        else { Refuse-Convergence 'Select -Actor codex or claude, or provide -NativeCommand.' }
    }
    if (-not (Test-Path -LiteralPath $NativeCommand -PathType Leaf)) { Refuse-Convergence 'Installed native SK converge command not found.' }
    $native = (Get-Content -LiteralPath $NativeCommand -Raw -Encoding UTF8).Replace("`r`n", "`n")
    if ($native.Contains('`$speckit-implement`')) {
        $implement = '`$speckit-implement`'; $tasks = '`$speckit-tasks`'; $bridge = '`$speckit-superpowers-bridge`'
    } elseif ($native.Contains('`/speckit-implement`')) {
        $implement = '`/speckit-implement`'; $tasks = '`/speckit-tasks`'; $bridge = '`/speckit-superpowers-bridge`'
    } else { Refuse-Convergence 'Unrecognized native SK converge executor contract; no adapter created.' }
    $old = 'This command MUST run only after' + "`n" + $implement + ' has run on the current `tasks.md`, and after ' + $tasks + ' has produced a complete `tasks.md`.'
    if (-not $native.Contains($old) -or -not $native.Contains('APPEND-ONLY, NEVER REWRITE') -or -not $native.Contains('### 9. Check for extension hooks')) {
        Refuse-Convergence 'Unrecognized native SK converge procedure; no adapter created.'
    }
    $new = 'This bridge adapter MUST run only after verified Superpowers completion of the current `tasks.md`, and after ' + $tasks + ' has produced a complete `tasks.md`.'
    $adapted = $native.Replace($old, $new).Replace($implement, $bridge)
    $adapter = Join-Path ([IO.Path]::GetTempPath()) ('speckit-bridge-converge-' + [Guid]::NewGuid().ToString('N') + '.md')
    [IO.File]::WriteAllText($adapter, $adapted, (New-Object Text.UTF8Encoding($false)))
    [ordered]@{ eligible = $true; feature_directory = $feature; adapter_path = $adapter; source_sha256 = Get-ArtifactSha256 -Path $NativeCommand } | ConvertTo-Json -Compress
} catch {
    Refuse-Convergence ('Convergence preparation failed: ' + $_.Exception.Message)
}
