#requires -Version 5.1
<#
SET-02: teste local controlado, sem mudar rede/firewall.
Padrao: firewall ativo, cliente 127.0.0.1 e portas livres. -StrictOffline adiciona isolamento rigoroso.
-CheckOnly apenas inspeciona; READY nao significa T01 aprovado.
Exit: 0=PASS/READY, 1=FAIL, 2=BLOCKED. Evidencias em output/set02/t01-local-* ou t01-offline-*.
#>
[CmdletBinding()]
param(
    [string]$CompilerPath = 'C:\msys64\ucrt64\bin\g++.exe',
    [switch]$StrictOffline,
    [switch]$CheckOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RunTimeoutSeconds = 10

function Get-FirewallSnapshot {
    $service = Get-Service -Name MpsSvc -ErrorAction Stop
    $policy = $null
    try {
        # API oficial somente de leitura; nao depende do provedor CIM.
        $policy = New-Object -ComObject HNetCfg.FwPolicy2
        [pscustomobject]@{
            Service = $service.Status.ToString(); ActiveProfiles = [int]$policy.CurrentProfileTypes
            Domain = $policy.FirewallEnabled(1); Private = $policy.FirewallEnabled(2)
            Public = $policy.FirewallEnabled(4)
        }
    }
    finally {
        if ($null -ne $policy) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($policy) }
    }
}

function Test-FirewallSnapshot {
    param($Snapshot)
    return ($Snapshot.Service -eq 'Running' -and $Snapshot.ActiveProfiles -ge 0 -and
        $Snapshot.ActiveProfiles -le 7 -and $Snapshot.Domain -eq $true -and
        $Snapshot.Private -eq $true -and $Snapshot.Public -eq $true)
}

function Test-T01Loopback {
    param([string]$SourceText)
    $calls = [regex]::Matches($SourceText, '\bc_channel\s*\(')
    $channels = [regex]::Matches($SourceText, '\bc_channel\s*\(\s*"127\.0\.0\.1"\s*,\s*(5101|5102)\s*\)')
    return ($calls.Count -eq 2 -and $channels.Count -eq 2 -and
        $channels[0].Groups[1].Value -eq '5101' -and $channels[1].Groups[1].Value -eq '5102')
}

function Assert-TestEnvironment {
    param([string]$Phase)
    $snapshot = Get-FirewallSnapshot
    $enabled = Test-FirewallSnapshot $snapshot
    $script:Evidence.audits += [pscustomobject]@{
        utc = [DateTime]::UtcNow.ToString('o'); phase = $Phase
        firewall_enabled = $enabled; firewall = $snapshot
    }
    if (-not $enabled) { throw 'ENVIRONMENT: firewall deve estar ativo nos tres perfis e MpsSvc em execucao.' }
    if ($StrictOffline) { Assert-Isolated $Phase }
}

function Get-IsolationSnapshot {
    # Falha de qualquer consulta interrompe a verificacao; nao assumir offline.
    $nics = @([System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces())
    $indices = @()
    $loopbackV4 = $false
    $dotnet = @(foreach ($nic in $nics) {
        $isLoopback = $nic.NetworkInterfaceType -eq [System.Net.NetworkInformation.NetworkInterfaceType]::Loopback
        if ($isLoopback) {
            $properties = $nic.GetIPProperties()
            foreach ($address in $properties.UnicastAddresses) {
                if ($address.Address.ToString() -eq '127.0.0.1') { $loopbackV4 = $true }
            }
            $v4 = $properties.GetIPv4Properties()
            $v6 = $properties.GetIPv6Properties()
            if ($null -ne $v4) { $indices += [int]$v4.Index }
            if ($null -ne $v6) { $indices += [int]$v6.Index }
        }
        [pscustomobject]@{ Loopback = $isLoopback; State = $nic.OperationalStatus.ToString() }
    })
    $adapters = @(Get-NetAdapter -IncludeHidden -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{ Index = [int]$_.InterfaceIndex; Admin = [int]$_.InterfaceAdminStatus; Operational = [int]$_.InterfaceOperationalStatus }
    })
    $interfaces = @(Get-NetIPInterface -IncludeAllCompartments -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{ Index = [int]$_.InterfaceIndex; State = $_.ConnectionState.ToString(); Family = $_.AddressFamily.ToString() }
    })
    $routes = @(Get-NetRoute -IncludeAllCompartments -PolicyStore ActiveStore -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{ Index = [int]$_.InterfaceIndex }
    })
    $compartments = @(Get-NetCompartment -ErrorAction Stop)
    [pscustomobject]@{
        DotNet = $dotnet; LoopbackIndices = @($indices | Sort-Object -Unique)
        LoopbackV4 = $loopbackV4; Adapters = $adapters; Interfaces = $interfaces
        Routes = $routes; CompartmentCount = $compartments.Count
    }
}

function Test-IsolationSnapshot {
    param($Snapshot)
    $reasons = @()
    if (@($Snapshot.DotNet).Count -eq 0) { $reasons += 'Inventario .NET vazio.' }
    if (-not $Snapshot.LoopbackV4 -or @($Snapshot.LoopbackIndices).Count -eq 0) {
        $reasons += 'Loopback IPv4 127.0.0.1 nao confirmado pelo tipo de interface.'
    }
    if ($Snapshot.CompartmentCount -ne 1) { $reasons += 'Compartimentos de rede adicionais ou desconhecidos.' }
    foreach ($nic in $Snapshot.DotNet) {
        if (-not $nic.Loopback -and $nic.State -notin @('Down', 'NotPresent')) {
            $reasons += "Interface .NET nao loopback em estado $($nic.State)."
        }
    }
    foreach ($adapter in $Snapshot.Adapters) {
        if ($adapter.Index -in $Snapshot.LoopbackIndices) { continue }
        # RFC 2863: Admin Down=2, Oper Down=2, NotPresent=6.
        # Cabo desconectado com adaptador administrativamente Up nao basta.
        if ($adapter.Operational -ne 6 -and -not ($adapter.Admin -eq 2 -and $adapter.Operational -eq 2)) {
            $reasons += "Adaptador $($adapter.Index) nao desativado/ausente (admin=$($adapter.Admin), oper=$($adapter.Operational))."
        }
    }
    foreach ($interface in $Snapshot.Interfaces) {
        if ($interface.Index -notin $Snapshot.LoopbackIndices -and $interface.State -ne 'Disconnected') {
            $reasons += "Interface IP $($interface.Index) nao loopback em estado $($interface.State)."
        }
    }
    if (@($Snapshot.Interfaces | Where-Object {
        $_.Index -in $Snapshot.LoopbackIndices -and $_.Family -eq 'IPv4' -and $_.State -eq 'Connected'
    }).Count -eq 0) { $reasons += 'Interface IP loopback IPv4 conectada nao confirmada.' }
    if (@($Snapshot.Routes | Where-Object { $_.Index -notin $Snapshot.LoopbackIndices }).Count -gt 0) {
        $reasons += 'Existem rotas ativas fora do loopback, inclusive em outros compartimentos.'
    }
    [pscustomobject]@{ Isolated = ($reasons.Count -eq 0); Reasons = $reasons }
}

function Assert-Isolated {
    param([string]$Phase)
    $snapshot = Get-IsolationSnapshot
    $assessment = Test-IsolationSnapshot $snapshot
    $script:Evidence.audits += [pscustomobject]@{
        utc = [DateTime]::UtcNow.ToString('o'); phase = $Phase
        assessment = $assessment; snapshot = $snapshot
    }
    if (-not $assessment.Isolated) { throw ('ISOLATION: ' + ($assessment.Reasons -join ' ')) }
}

function Stop-TestTree {
    param([System.Diagnostics.Process]$Process)
    if ($null -ne $Process -and -not $Process.HasExited) {
        # O supervisor possui um Job Object KILL_ON_JOB_CLOSE, criado antes dos filhos.
        $Process.Kill()
        if (-not $Process.WaitForExit(5000)) { throw "Supervisor PID $($Process.Id) nao encerrou." }
    }
}

function Invoke-GuardedProcess {
    param([string]$Label, [string[]]$Command, [int]$Timeout, [string]$InputText = '')
    Assert-TestEnvironment "$Label.before"
    $configPath = Join-Path $script:RunDir "$Label.config.json"
    $config = @{ command = $Command; timeout = $Timeout; stdin = $InputText
        cwd = $script:RunDir; compiler = $CompilerPath; label = $Label }
    [IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 8), $script:Utf8)
    # Os dois argumentos sao caminhos Windows controlados; aspas nao sao permitidas em nomes de arquivo.
    if ($script:WorkerPath.Contains('"') -or $configPath.Contains('"')) { throw 'Caminho de controle invalido.' }
    $info = New-Object System.Diagnostics.ProcessStartInfo
    # O python.exe da venv no Windows e um launcher: usar o interpretador real
    # para que o PID supervisionado seja o dono do Job Object. Worker so usa stdlib.
    $info.FileName = $script:SupervisorPythonPath
    $info.Arguments = '-B "' + $script:WorkerPath + '" "' + $configPath + '"'
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $started = $false
    try {
        if (-not $process.Start()) { throw 'Falha ao iniciar supervisor.' }
        $started = $true
        while (-not $process.WaitForExit(250)) {
            if ($watch.Elapsed.TotalSeconds -gt ($Timeout + 15)) { throw 'Supervisor excedeu seu prazo.' }
            Assert-TestEnvironment "$Label.monitor"
        }
        Assert-TestEnvironment "$Label.after"
        $resultPath = Join-Path $script:RunDir "$Label.result.json"
        if (-not (Test-Path -LiteralPath $resultPath)) { throw 'Supervisor nao produziu resultado.' }
        $result = Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($result.worker_pid -ne $process.Id) { throw 'PID do supervisor divergente.' }
        if ($result.job_guard -and $process.HasExited) {
            # O kernel fecha o unico handle do job ao encerrar seu dono, matando os filhos.
            $result.cleanup_ok = $true
            [IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 8), $script:Utf8)
        }
        $script:Evidence.processes += $result
        return $result
    }
    finally {
        if ($started) { Stop-TestTree $process }
        $process.Dispose()
    }
}

function Test-T01Output {
    param([string]$Text)
    $server = [regex]::Matches($Text, '(?m)Servidor recebeu:\s*\+\s+2\s+3\s*$')
    $client = [regex]::Matches($Text, '(?m)Resultado:\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$')
    $number = [decimal]0
    $valid = $client.Count -eq 1 -and [decimal]::TryParse(
        $client[0].Groups[1].Value, [Globalization.NumberStyles]::Float,
        [Globalization.CultureInfo]::InvariantCulture, [ref]$number)
    return ($server.Count -eq 1 -and $valid -and $number -eq 5)
}

function Assert-T01PortsFree {
    # Nao matar participantes preexistentes nem reutilizar suas portas/resultados.
    $ip = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
    $listeners = @($ip.GetActiveTcpListeners() | Where-Object { $_.Port -in @(5101, 5102) })
    $busy = @($ip.GetActiveTcpConnections() | Where-Object {
        ($_.LocalEndPoint.Port -in @(5101, 5102) -or $_.RemoteEndPoint.Port -in @(5101, 5102)) -and $_.State.ToString() -notin @('TimeWait', 'Closed')
    })
    if ($listeners.Count -gt 0 -or $busy.Count -gt 0) { throw 'Portas 5101/5102 em uso; nenhum processo alheio sera encerrado.' }
}

$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$repoRoot = Split-Path -Parent $PSScriptRoot
$script:RunDir = $null
$script:Evidence = [ordered]@{
    test = 'SET-02/T01'; status = 'BLOCKED'; phase = 'initialization'; reason = ''
    utc = [DateTime]::UtcNow.ToString('o'); check_only = [bool]$CheckOnly
    mode = $(if ($StrictOffline) { 'strict-offline' } else { 'local' })
    runtime_timeout_seconds = $RunTimeoutSeconds; handoff = $null
    runtime_requested = $false; audits = @(); processes = @(); hashes = @{}
}
$finalExit = 2
try {
    foreach ($relative in @('output', 'output/set02')) {
        $path = Join-Path $repoRoot $relative
        if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Diretorio de evidencias redirecionado; teste recusado.'
        }
    }
    $prefix = if ($StrictOffline) { 't01-offline-' } else { 't01-local-' }
    $script:RunDir = Join-Path $repoRoot ('output/set02/' + $prefix + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $script:RunDir | Out-Null
    $script:Evidence.phase = 'network_preflight'
    Assert-TestEnvironment 'preflight'
    $source = Join-Path $repoRoot 'tests/teste1_calculadora_cliente_servidor.minipar'
    if (-not (Test-T01Loopback ([IO.File]::ReadAllText($source)))) {
        throw 'ENVIRONMENT: fonte T01 deve usar somente os canais 127.0.0.1:5101/5102.'
    }
    Assert-T01PortsFree
    if ($CheckOnly) {
        $script:Evidence.status = 'READY'
        $script:Evidence.reason = 'Inspecao aprovada (firewall, cliente loopback e portas); nenhum programa compilado/executado.'
        $finalExit = 0
    }
    else {
        $script:PythonPath = Join-Path $repoRoot '.venv/Scripts/python.exe'
        $mainFile = Join-Path $repoRoot 'main.py'
        foreach ($path in @($script:PythonPath, $CompilerPath, $source, $mainFile)) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Recurso ausente: $path" }
        }
        $script:SupervisorPythonPath = & $script:PythonPath -I -c 'import sys; print(sys._base_executable)'
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $script:SupervisorPythonPath -PathType Leaf)) {
            throw 'Interpretador real do supervisor indisponivel.'
        }
        Assert-T01PortsFree
        $script:WorkerPath = Join-Path $script:RunDir 'supervisor.py'
        $worker = @'
import ctypes, json, os, pathlib, subprocess, sys, time
from ctypes import wintypes as W
cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
base = pathlib.Path(cfg['cwd'])
label = cfg['label']
env = dict(os.environ, CXX=cfg['compiler'], PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
env['PATH'] = str(pathlib.Path(cfg['compiler']).parent) + os.pathsep + env.get('PATH', '')
result = dict(label=label, command=cfg['command'], returncode=None, timed_out=False,
              started=False, cleanup_ok=True, job_guard=False, worker_pid=os.getpid(),
              error=None, duration_seconds=None)
stdout = (base / (label + '.stdout.txt')).open('w', encoding='utf-8')
stderr = (base / (label + '.stderr.txt')).open('w', encoding='utf-8')
started = time.monotonic()
class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
        ('flags', W.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
        ('active', W.DWORD), ('affinity', ctypes.c_size_t), ('priority', W.DWORD), ('scheduling', W.DWORD)]
class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', ctypes.c_ulonglong * 6),
        ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
        ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, W.LPCWSTR]
kernel.CreateJobObjectW.restype = W.HANDLE
kernel.SetInformationJobObject.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]
kernel.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
kernel.GetCurrentProcess.restype = W.HANDLE
kernel.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
job = None
def save():
    result['duration_seconds'] = round(time.monotonic() - started, 3)
    stdout.flush(); stderr.flush()
    (base / (label + '.result.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
try:
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; nunca permitir breakaway.
    if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
        raise ctypes.WinError(ctypes.get_last_error())
    result['job_guard'] = True  # O supervisor entra no job ANTES de criar qualquer filho.
    process = subprocess.Popen(cfg['command'], cwd=cfg['cwd'], env=env, stdin=subprocess.PIPE,
        stdout=stdout, stderr=stderr, text=True, encoding='utf-8', errors='replace',
        creationflags=subprocess.CREATE_NO_WINDOW)
    result['started'] = True
    result['pid'] = process.pid
    (base / (label + '.started.json')).write_text(json.dumps(result), encoding='utf-8')
    try:
        process.communicate(cfg['stdin'], timeout=cfg['timeout'])
        result['returncode'] = process.returncode
    except subprocess.TimeoutExpired:
        result['timed_out'] = True
        result['cleanup_ok'] = False  # O pai confirma a saida do dono do job.
        save()  # Salvar evidencias ANTES de encerrar o job, que inclui este supervisor.
        if not kernel.TerminateJobObject(job, 124):
            raise ctypes.WinError(ctypes.get_last_error())
except Exception as exc:
    result['error'] = type(exc).__name__ + ': ' + str(exc)
finally:
    save()
    stdout.close(); stderr.close()
# Nao fechar o handle explicitamente: ele pertence apenas a este processo, sem heranca.
# ExitProcess (normal, erro ou Kill pelo pai) o fecha e o kernel encerra os descendentes.
sys.exit(0 if result['error'] is None else 1)
'@
        [IO.File]::WriteAllText($script:WorkerPath, $worker, $script:Utf8)
        foreach ($path in @($source, $mainFile, (Join-Path $repoRoot 'src/codegen.py'), (Join-Path $repoRoot 'src/cpp_template.py'))) {
            $script:Evidence.hashes[(Split-Path -Leaf $path)] = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        }
        $script:Evidence.phase = 'compile'
        $compiled = Invoke-GuardedProcess 'compile' @($script:PythonPath, '-B', $mainFile, $source, 't01') 130
        if ($compiled.timed_out -or $null -ne $compiled.error -or -not $compiled.cleanup_ok -or $compiled.returncode -ne 0) {
            $script:Evidence.status = 'FAIL'; throw 'Compilacao falhou ou expirou; consultar compile.*.'
        }
        $binary = Join-Path $script:RunDir 'output/t01.exe'
        if (-not (Test-Path -LiteralPath $binary -PathType Leaf) -or (Get-Item -LiteralPath $binary).Length -eq 0) {
            $script:Evidence.status = 'FAIL'; throw 'Compilacao sem binario atual nao vazio.'
        }
        $script:Evidence.hashes['t01.exe'] = (Get-FileHash -Algorithm SHA256 -LiteralPath $binary).Hash.ToLowerInvariant()
        $script:Evidence.phase = 'run'
        Assert-T01PortsFree
        $script:Evidence.runtime_requested = $true
        $ran = Invoke-GuardedProcess 'run' @($binary) $RunTimeoutSeconds "+`n2`n3`n"
        if (-not $ran.job_guard -or -not $ran.started) {
            throw 'ENVIRONMENT: supervisor nao conseguiu iniciar o teste protegido; consultar run.*.'
        }
        if ($ran.timed_out -or $null -ne $ran.error -or -not $ran.cleanup_ok -or $ran.returncode -ne 0) {
            $script:Evidence.status = 'FAIL'; throw 'Execucao falhou ou expirou; consultar run.*.'
        }
        $script:Evidence.phase = 'oracle'
        $text = [IO.File]::ReadAllText((Join-Path $script:RunDir 'run.stdout.txt'))
        $errors = [IO.File]::ReadAllText((Join-Path $script:RunDir 'run.stderr.txt'))
        if (-not (Test-T01Output $text) -or -not [string]::IsNullOrWhiteSpace($errors)) {
            $script:Evidence.status = 'FAIL'; throw 'Oraculo divergente: exigir servidor + 2 3 e um resultado numerico 5, sem stderr.'
        }
        $script:Evidence.status = 'PASS'
        $script:Evidence.reason = 'Compilacao atual, controles de rede aprovados, servidor recebeu + 2 3 e cliente recebeu 5.'
        $finalExit = 0
    }
}
catch {
    $script:Evidence.reason = $_.Exception.Message
    if ($script:Evidence.reason.StartsWith('ISOLATION:') -or $script:Evidence.reason.StartsWith('ENVIRONMENT:')) {
        $script:Evidence.status = 'BLOCKED'
    }
    if ($script:Evidence.status -eq 'FAIL' -and $script:Evidence.phase -in @('run', 'oracle')) {
        $script:Evidence.handoff = 'CORE-01 / Eixo A: falha funcional T01; ambiente UCRT64 validado separadamente.'
    }
    $finalExit = if ($script:Evidence.status -eq 'FAIL') { 1 } else { 2 }
}
finally {
    if ($null -ne $script:RunDir) {
        [IO.File]::WriteAllText((Join-Path $script:RunDir 'resultado.json'), ($script:Evidence | ConvertTo-Json -Depth 12), $script:Utf8)
        Write-Host "Evidencias: $script:RunDir"
    }
}
Write-Host "$($script:Evidence.status): $($script:Evidence.reason)"
exit $finalExit
