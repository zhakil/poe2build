# PoE2智能构筑生成器 - 系统性能验证脚本
# System Performance Verification Script for PoE2 Build Generator

param(
    [switch]$Detailed = $false,
    [switch]$ExportResults = $true,
    [string]$OutputPath = "system_verification",
    [switch]$QuickCheck = $false
)

# 性能等级定义
enum PerformanceLevel {
    Excellent = 4
    Good = 3 
    Basic = 2
    Poor = 1
    Insufficient = 0
}

class SystemPerformanceVerifier {
    [hashtable]$Results = @{}
    [hashtable]$SystemInfo = @{}
    [int]$OverallScore = 0
    [string]$RecommendedConfig = ""
    
    SystemPerformanceVerifier() {
        $this.CollectSystemInfo()
    }
    
    # 收集系统信息
    [void] CollectSystemInfo() {
        Write-Host "🔍 收集系统信息..." -ForegroundColor Cyan
        
        try {
            $computerInfo = Get-ComputerInfo
            $this.SystemInfo = @{
                'OS' = "$($computerInfo.WindowsProductName) $($computerInfo.WindowsVersion)"
                'CPU' = (Get-WmiObject -Class Win32_Processor).Name
                'TotalRAM' = [Math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 2)
                'AvailableRAM' = [Math]::Round($computerInfo.AvailablePhysicalMemory / 1GB, 2)
                'PowerShellVersion' = $PSVersionTable.PSVersion.ToString()
                'DotNetVersion' = $PSVersionTable.CLRVersion.ToString()
            }
            
            # 显卡信息
            try {
                $gpu = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -notlike "*Basic*" } | Select-Object -First 1
                $this.SystemInfo['GPU'] = if ($gpu) { $gpu.Name } else { "集成显卡或未检测到" }
            } catch {
                $this.SystemInfo['GPU'] = "无法检测"
            }
            
            # 存储信息
            try {
                $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | Where-Object { $_.DeviceID -eq "C:" }
                $this.SystemInfo['DiskType'] = if (Get-PhysicalDisk | Where-Object { $_.MediaType -eq "SSD" }) { "SSD" } else { "HDD" }
                $this.SystemInfo['AvailableSpace'] = [Math]::Round($disk.FreeSpace / 1GB, 2)
            } catch {
                $this.SystemInfo['DiskType'] = "无法检测"
                $this.SystemInfo['AvailableSpace'] = 0
            }
            
        } catch {
            Write-Warning "部分系统信息收集失败: $($_.Exception.Message)"
        }
    }
    
    # CPU性能测试
    [hashtable] TestCPUPerformance() {
        Write-Host "`n💻 CPU性能测试..." -ForegroundColor Yellow
        
        $startTime = Get-Date
        $iterations = if ($QuickCheck) { 100000 } else { 1000000 }
        
        # 简单的数学计算基准测试
        for ($i = 0; $i -lt $iterations; $i++) {
            $null = [Math]::Sqrt($i) * [Math]::PI
        }
        
        $endTime = Get-Date
        $cpuTime = ($endTime - $startTime).TotalMilliseconds
        
        # CPU核心数
        $coreCount = (Get-WmiObject -Class Win32_Processor).NumberOfCores
        $logicalProcessors = (Get-WmiObject -Class Win32_Processor).NumberOfLogicalProcessors
        
        # 性能评分
        $cpuScore = switch (true) {
            ($cpuTime -lt 500 -and $coreCount -ge 8) { [PerformanceLevel]::Excellent }
            ($cpuTime -lt 1000 -and $coreCount -ge 4) { [PerformanceLevel]::Good }
            ($cpuTime -lt 2000 -and $coreCount -ge 2) { [PerformanceLevel]::Basic }
            ($cpuTime -lt 4000) { [PerformanceLevel]::Poor }
            default { [PerformanceLevel]::Insufficient }
        }
        
        $cpuResult = @{
            'BenchmarkTime' = $cpuTime
            'CoreCount' = $coreCount
            'LogicalProcessors' = $logicalProcessors
            'Score' = $cpuScore
            'Recommendation' = switch ($cpuScore) {
                ([PerformanceLevel]::Excellent) { "CPU性能优异，支持所有功能" }
                ([PerformanceLevel]::Good) { "CPU性能良好，推荐配置" }
                ([PerformanceLevel]::Basic) { "CPU性能基本满足，建议升级" }
                ([PerformanceLevel]::Poor) { "CPU性能较低，可能出现卡顿" }
                default { "CPU性能不足，不建议使用" }
            }
        }
        
        $this.Results['CPU'] = $cpuResult
        return $cpuResult
    }
    
    # 内存性能测试
    [hashtable] TestMemoryPerformance() {
        Write-Host "`n🧠 内存性能测试..." -ForegroundColor Yellow
        
        $totalRAM = $this.SystemInfo['TotalRAM']
        $availableRAM = $this.SystemInfo['AvailableRAM']
        $usedRAM = $totalRAM - $availableRAM
        $memoryUsagePercent = [Math]::Round(($usedRAM / $totalRAM) * 100, 1)
        
        # 内存分配测试
        $startTime = Get-Date
        try {
            $testArray = @()
            for ($i = 0; $i -lt 1000000; $i++) {
                $testArray += $i
            }
            $null = $testArray
        } catch {
            Write-Warning "内存分配测试失败"
        }
        $endTime = Get-Date
        $memoryAllocationTime = ($endTime - $startTime).TotalMilliseconds
        
        # 内存性能评分
        $memoryScore = switch (true) {
            ($totalRAM -ge 16 -and $availableRAM -ge 8 -and $memoryAllocationTime -lt 1000) { [PerformanceLevel]::Excellent }
            ($totalRAM -ge 8 -and $availableRAM -ge 4 -and $memoryAllocationTime -lt 2000) { [PerformanceLevel]::Good }
            ($totalRAM -ge 4 -and $availableRAM -ge 2 -and $memoryAllocationTime -lt 4000) { [PerformanceLevel]::Basic }
            ($totalRAM -ge 4) { [PerformanceLevel]::Poor }
            default { [PerformanceLevel]::Insufficient }
        }
        
        $memoryResult = @{
            'TotalRAM' = $totalRAM
            'AvailableRAM' = $availableRAM
            'UsedRAM' = $usedRAM
            'UsagePercent' = $memoryUsagePercent
            'AllocationTime' = $memoryAllocationTime
            'Score' = $memoryScore
            'Recommendation' = switch ($memoryScore) {
                ([PerformanceLevel]::Excellent) { "内存充足，支持多实例运行" }
                ([PerformanceLevel]::Good) { "内存良好，推荐配置" }
                ([PerformanceLevel]::Basic) { "内存基本够用，建议关闭其他程序" }
                ([PerformanceLevel]::Poor) { "内存偏低，可能影响性能" }
                default { "内存不足，强烈建议升级" }
            }
        }
        
        $this.Results['Memory'] = $memoryResult
        return $memoryResult
    }
    
    # 存储性能测试
    [hashtable] TestStoragePerformance() {
        Write-Host "`n💾 存储性能测试..." -ForegroundColor Yellow
        
        $diskType = $this.SystemInfo['DiskType']
        $availableSpace = $this.SystemInfo['AvailableSpace']
        
        # 文件I/O性能测试
        $testFile = [System.IO.Path]::GetTempFileName()
        $testData = "0" * 1048576  # 1MB测试数据
        
        try {
            # 写入性能测试
            $startTime = Get-Date
            for ($i = 0; $i -lt 10; $i++) {
                $testData | Out-File -FilePath $testFile -Append
            }
            $endTime = Get-Date
            $writeTime = ($endTime - $startTime).TotalMilliseconds
            
            # 读取性能测试
            $startTime = Get-Date
            for ($i = 0; $i -lt 10; $i++) {
                $null = Get-Content -Path $testFile
            }
            $endTime = Get-Date
            $readTime = ($endTime - $startTime).TotalMilliseconds
            
            Remove-Item -Path $testFile -Force
            
        } catch {
            $writeTime = 9999
            $readTime = 9999
            Write-Warning "存储性能测试失败"
        }
        
        # 存储性能评分
        $storageScore = switch (true) {
            ($diskType -eq "SSD" -and $writeTime -lt 1000 -and $readTime -lt 500 -and $availableSpace -gt 10) { [PerformanceLevel]::Excellent }
            ($diskType -eq "SSD" -and $writeTime -lt 2000 -and $readTime -lt 1000 -and $availableSpace -gt 5) { [PerformanceLevel]::Good }
            ($writeTime -lt 4000 -and $readTime -lt 2000 -and $availableSpace -gt 2) { [PerformanceLevel]::Basic }
            ($availableSpace -gt 1) { [PerformanceLevel]::Poor }
            default { [PerformanceLevel]::Insufficient }
        }
        
        $storageResult = @{
            'DiskType' = $diskType
            'AvailableSpace' = $availableSpace
            'WriteTime' = $writeTime
            'ReadTime' = $readTime
            'Score' = $storageScore
            'Recommendation' = switch ($storageScore) {
                ([PerformanceLevel]::Excellent) { "存储性能优异，SSD快速响应" }
                ([PerformanceLevel]::Good) { "存储性能良好，推荐配置" }
                ([PerformanceLevel]::Basic) { "存储性能基本，建议升级到SSD" }
                ([PerformanceLevel]::Poor) { "存储性能较低，影响用户体验" }
                default { "存储空间不足或性能太差" }
            }
        }
        
        $this.Results['Storage'] = $storageResult
        return $storageResult
    }
    
    # 网络性能测试
    [hashtable] TestNetworkPerformance() {
        Write-Host "`n🌐 网络性能测试..." -ForegroundColor Yellow
        
        $networkResults = @{}
        $endpoints = @(
            @{ Name = "PoE2Scout"; URL = "poe2scout.com"; Port = 443 },
            @{ Name = "PoE2Ninja"; URL = "poe.ninja"; Port = 443 },
            @{ Name = "PathOfBuilding"; URL = "pathofbuilding.community"; Port = 443 }
        )
        
        $totalLatency = 0
        $successfulTests = 0
        
        foreach ($endpoint in $endpoints) {
            try {
                $result = Test-NetConnection -ComputerName $endpoint.URL -Port $endpoint.Port -WarningAction SilentlyContinue
                
                if ($result.TcpTestSucceeded) {
                    $networkResults[$endpoint.Name] = @{
                        'Status' = '✅ 连接成功'
                        'Latency' = if ($result.PingSucceeded) { $result.PingReplyDetails.RoundtripTime } else { 'N/A' }
                    }
                    
                    if ($result.PingSucceeded -and $result.PingReplyDetails.RoundtripTime) {
                        $totalLatency += $result.PingReplyDetails.RoundtripTime
                        $successfulTests++
                    }
                } else {
                    $networkResults[$endpoint.Name] = @{
                        'Status' = '❌ 连接失败'
                        'Latency' = 'N/A'
                    }
                }
            } catch {
                $networkResults[$endpoint.Name] = @{
                    'Status' = '⚠️ 测试异常'
                    'Latency' = 'N/A'
                }
            }
        }
        
        $averageLatency = if ($successfulTests -gt 0) { $totalLatency / $successfulTests } else { 9999 }
        
        # 网络性能评分
        $networkScore = switch (true) {
            ($successfulTests -eq 3 -and $averageLatency -lt 100) { [PerformanceLevel]::Excellent }
            ($successfulTests -ge 2 -and $averageLatency -lt 300) { [PerformanceLevel]::Good }
            ($successfulTests -ge 1 -and $averageLatency -lt 1000) { [PerformanceLevel]::Basic }
            ($successfulTests -ge 1) { [PerformanceLevel]::Poor }
            default { [PerformanceLevel]::Insufficient }
        }
        
        $networkResult = @{
            'EndpointTests' = $networkResults
            'SuccessfulConnections' = $successfulTests
            'AverageLatency' = $averageLatency
            'Score' = $networkScore
            'Recommendation' = switch ($networkScore) {
                ([PerformanceLevel]::Excellent) { "网络连接优异，低延迟" }
                ([PerformanceLevel]::Good) { "网络连接良好，推荐配置" }
                ([PerformanceLevel]::Basic) { "网络连接基本，可能偶有延迟" }
                ([PerformanceLevel]::Poor) { "网络连接较差，影响数据获取" }
                default { "网络连接失败，请检查网络设置" }
            }
        }
        
        $this.Results['Network'] = $networkResult
        return $networkResult
    }
    
    # 系统兼容性检查
    [hashtable] TestSystemCompatibility() {
        Write-Host "`n🔧 系统兼容性检查..." -ForegroundColor Yellow
        
        $osVersion = [Environment]::OSVersion.Version
        $windowsVersion = $this.SystemInfo['OS']
        $powershellVersion = $this.SystemInfo['PowerShellVersion']
        $dotnetVersion = $this.SystemInfo['DotNetVersion']
        
        # Windows版本兼容性
        $windowsCompat = if ($windowsVersion -match "Windows 11") {
            [PerformanceLevel]::Excellent
        } elseif ($windowsVersion -match "Windows 10" -and $osVersion.Build -ge 18362) {
            [PerformanceLevel]::Good
        } elseif ($windowsVersion -match "Windows 10") {
            [PerformanceLevel]::Basic
        } else {
            [PerformanceLevel]::Poor
        }
        
        # PowerShell版本兼容性
        $psVersion = [Version]$powershellVersion
        $psCompat = if ($psVersion.Major -ge 7) {
            [PerformanceLevel]::Excellent
        } elseif ($psVersion.Major -ge 5 -and $psVersion.Minor -ge 1) {
            [PerformanceLevel]::Good
        } else {
            [PerformanceLevel]::Poor
        }
        
        # .NET版本兼容性
        $dotnetVersionParsed = [Version]$dotnetVersion
        $dotnetCompat = if ($dotnetVersionParsed.Major -ge 4 -and $dotnetVersionParsed.Minor -ge 8) {
            [PerformanceLevel]::Good
        } elseif ($dotnetVersionParsed.Major -ge 4 -and $dotnetVersionParsed.Minor -ge 7) {
            [PerformanceLevel]::Basic
        } else {
            [PerformanceLevel]::Poor
        }
        
        $compatibilityResult = @{
            'WindowsVersion' = $windowsVersion
            'WindowsCompatibility' = $windowsCompat
            'PowerShellVersion' = $powershellVersion
            'PowerShellCompatibility' = $psCompat
            'DotNetVersion' = $dotnetVersion
            'DotNetCompatibility' = $dotnetCompat
            'OverallCompatibility' = [Math]::Min([Math]::Min([int]$windowsCompat, [int]$psCompat), [int]$dotnetCompat)
        }
        
        $this.Results['Compatibility'] = $compatibilityResult
        return $compatibilityResult
    }
    
    # 运行完整性能验证
    [void] RunCompleteVerification() {
        Write-Host "`n🚀 开始系统性能验证..." -ForegroundColor Green
        Write-Host "这将测试您系统运行PoE2智能构筑生成器的性能表现`n" -ForegroundColor Gray
        
        # 显示系统信息
        $this.DisplaySystemInfo()
        
        # 运行各项测试
        $cpuResult = $this.TestCPUPerformance()
        $memoryResult = $this.TestMemoryPerformance()
        $storageResult = $this.TestStoragePerformance()
        $networkResult = $this.TestNetworkPerformance()
        $compatibilityResult = $this.TestSystemCompatibility()
        
        # 计算总体评分
        $this.CalculateOverallScore()
        
        # 生成推荐配置
        $this.GenerateRecommendation()
        
        # 显示结果
        $this.DisplayResults()
        
        # 导出结果
        if ($ExportResults) {
            $this.ExportResults()
        }
    }
    
    # 显示系统信息
    [void] DisplaySystemInfo() {
        Write-Host "📋 检测到的系统信息:" -ForegroundColor Cyan
        Write-Host "操作系统: $($this.SystemInfo['OS'])" -ForegroundColor Gray
        Write-Host "处理器: $($this.SystemInfo['CPU'])" -ForegroundColor Gray
        Write-Host "内存: $($this.SystemInfo['TotalRAM'])GB (可用: $($this.SystemInfo['AvailableRAM'])GB)" -ForegroundColor Gray
        Write-Host "显卡: $($this.SystemInfo['GPU'])" -ForegroundColor Gray
        Write-Host "存储: $($this.SystemInfo['DiskType']) (可用空间: $($this.SystemInfo['AvailableSpace'])GB)" -ForegroundColor Gray
        Write-Host "PowerShell: $($this.SystemInfo['PowerShellVersion'])" -ForegroundColor Gray
    }
    
    # 计算总体评分
    [void] CalculateOverallScore() {
        $scores = @()
        foreach ($category in @('CPU', 'Memory', 'Storage', 'Network')) {
            if ($this.Results.ContainsKey($category) -and $this.Results[$category].ContainsKey('Score')) {
                $scores += [int]$this.Results[$category]['Score']
            }
        }
        
        if ($scores.Count -gt 0) {
            $this.OverallScore = [Math]::Round(($scores | Measure-Object -Average).Average, 0)
        } else {
            $this.OverallScore = 0
        }
    }
    
    # 生成推荐配置
    [void] GenerateRecommendation() {
        $this.RecommendedConfig = switch ($this.OverallScore) {
            4 { "🌟 您的系统配置优异！完全支持所有高级功能，包括多实例运行和GPU加速。" }
            3 { "✅ 您的系统配置良好！推荐使用所有功能，性能表现优秀。" }
            2 { "⚠️ 您的系统配置基本满足要求，但建议关闭其他程序以获得更好的性能。" }
            1 { "⚠️ 您的系统配置偏低，可能会遇到性能问题，建议升级硬件。" }
            default { "❌ 您的系统配置不足以流畅运行此应用程序，强烈建议升级。" }
        }
    }
    
    # 显示结果
    [void] DisplayResults() {
        Write-Host "`n" + "="*80 -ForegroundColor Yellow
        Write-Host "🎯 系统性能验证结果报告" -ForegroundColor Yellow
        Write-Host "="*80 -ForegroundColor Yellow
        
        foreach ($category in @('CPU', 'Memory', 'Storage', 'Network', 'Compatibility')) {
            if ($this.Results.ContainsKey($category)) {
                $result = $this.Results[$category]
                $scoreText = switch ([int]$result['Score']) {
                    4 { "🌟 优异" }
                    3 { "✅ 良好" }
                    2 { "⚠️ 基本" }
                    1 { "⚠️ 较差" }
                    default { "❌ 不足" }
                }
                
                Write-Host "`n$category 性能: $scoreText" -ForegroundColor $(
                    switch ([int]$result['Score']) {
                        4 { "Green" }
                        3 { "Green" }
                        2 { "Yellow" }
                        1 { "Red" }
                        default { "Red" }
                    }
                )
                
                if ($result.ContainsKey('Recommendation')) {
                    Write-Host "建议: $($result['Recommendation'])" -ForegroundColor Gray
                }
            }
        }
        
        Write-Host "`n🏆 总体性能评分: $($this.OverallScore)/4" -ForegroundColor Cyan
        Write-Host $this.RecommendedConfig -ForegroundColor $(
            switch ($this.OverallScore) {
                4 { "Green" }
                3 { "Green" }
                2 { "Yellow" }
                default { "Red" }
            }
        )
        
        Write-Host "`n💡 性能优化建议:" -ForegroundColor Cyan
        $this.DisplayOptimizationTips()
        
        Write-Host "`n⏱️ 验证完成时间: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
    }
    
    # 显示优化建议
    [void] DisplayOptimizationTips() {
        $tips = @()
        
        foreach ($category in @('CPU', 'Memory', 'Storage', 'Network')) {
            if ($this.Results.ContainsKey($category)) {
                $score = [int]$this.Results[$category]['Score']
                if ($score -le 2) {
                    switch ($category) {
                        'CPU' { $tips += "• 考虑升级到更快的多核处理器以提高计算性能" }
                        'Memory' { $tips += "• 增加内存容量，推荐8GB以上以获得流畅体验" }
                        'Storage' { $tips += "• 升级到SSD固态硬盘以提高启动速度和响应性" }
                        'Network' { $tips += "• 检查网络连接，确保稳定的互联网访问" }
                    }
                }
            }
        }
        
        if ($tips.Count -eq 0) {
            Write-Host "• 您的系统配置良好，无需额外优化建议" -ForegroundColor Green
        } else {
            foreach ($tip in $tips) {
                Write-Host $tip -ForegroundColor Yellow
            }
        }
    }
    
    # 导出结果
    [void] ExportResults() {
        Write-Host "`n📄 导出验证结果..." -ForegroundColor Cyan
        
        if (!(Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $jsonFile = Join-Path $OutputPath "system_verification_$timestamp.json"
        $htmlFile = Join-Path $OutputPath "system_verification_$timestamp.html"
        
        # 准备导出数据
        $exportData = @{
            'Timestamp' = Get-Date
            'SystemInfo' = $this.SystemInfo
            'TestResults' = $this.Results
            'OverallScore' = $this.OverallScore
            'Recommendation' = $this.RecommendedConfig
        }
        
        # 导出JSON
        $exportData | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
        Write-Host "JSON报告已保存: $jsonFile" -ForegroundColor Green
        
        # 导出HTML (简化版)
        $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PoE2智能构筑生成器 - 系统性能验证报告</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
        .score { font-size: 2em; font-weight: bold; text-align: center; margin: 20px 0; }
        .excellent { color: #27ae60; }
        .good { color: #2ecc71; }
        .basic { color: #f39c12; }
        .poor { color: #e74c3c; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 PoE2智能构筑生成器</h1>
            <h2>系统性能验证报告</h2>
            <p>验证时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        </div>
        
        <div class="score $(switch ($this.OverallScore) { 4 {'excellent'} 3 {'good'} 2 {'basic'} default {'poor'} })">
            总体性能评分: $($this.OverallScore)/4
        </div>
        
        <p><strong>系统建议：</strong> $($this.RecommendedConfig)</p>
        
        <h3>📋 系统信息</h3>
        <table>
            <tr><td><strong>操作系统</strong></td><td>$($this.SystemInfo['OS'])</td></tr>
            <tr><td><strong>处理器</strong></td><td>$($this.SystemInfo['CPU'])</td></tr>
            <tr><td><strong>内存</strong></td><td>$($this.SystemInfo['TotalRAM'])GB</td></tr>
            <tr><td><strong>显卡</strong></td><td>$($this.SystemInfo['GPU'])</td></tr>
            <tr><td><strong>存储类型</strong></td><td>$($this.SystemInfo['DiskType'])</td></tr>
        </table>
        
        <h3>🎯 性能测试结果</h3>
        <table>
"@
        
        foreach ($category in @('CPU', 'Memory', 'Storage', 'Network')) {
            if ($this.Results.ContainsKey($category)) {
                $result = $this.Results[$category]
                $scoreText = switch ([int]$result['Score']) {
                    4 { "🌟 优异" }
                    3 { "✅ 良好" }
                    2 { "⚠️ 基本" }
                    1 { "⚠️ 较差" }
                    default { "❌ 不足" }
                }
                
                $html += "<tr><td><strong>$category</strong></td><td>$scoreText</td><td>$($result['Recommendation'])</td></tr>"
            }
        }
        
        $html += @"
        </table>
    </div>
</body>
</html>
"@
        
        $html | Out-File -FilePath $htmlFile -Encoding UTF8
        Write-Host "HTML报告已保存: $htmlFile" -ForegroundColor Green
        
        # 自动打开HTML报告
        Start-Process $htmlFile
    }
}

# 主执行逻辑
Write-Host "🔧 PoE2智能构筑生成器 - 系统性能验证工具" -ForegroundColor Green
Write-Host "版本: 1.0.0 | 作者: PoE2 Build Generator Team`n" -ForegroundColor Gray

# 创建验证器实例
$verifier = [SystemPerformanceVerifier]::new()

# 运行验证
$verifier.RunCompleteVerification()

Write-Host "`n✨ 系统性能验证完成！" -ForegroundColor Green
Write-Host "💡 如果验证结果不理想，请参考性能优化建议进行调整。" -ForegroundColor Cyan