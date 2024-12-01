import socket
import subprocess

def start_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(5)
    print(f"Listening on {ip}:{port}")

    while True:
        client, addr = server.accept()
        print(f"Connection from {addr}")
        handle_client(client)

def handle_client(client_socket):
    with client_socket:
        while True:
            request = client_socket.recv(1024)
            if not request:
                break
            command = request.decode()
            print(f"Received: {command}")
            output = subprocess.run(command, shell=True, capture_output=True, text=True)
            response = output.stdout + output.stderr
            client_socket.send(response.encode())

if __name__ == "__main__":
    ip = input("Enter public facing IP address (or leave blank for default): ")
    if not ip:
        ip = '0.0.0.0'  # Default to all interfaces
    port = int(input("Enter port: "))
    start_server(ip, port)
