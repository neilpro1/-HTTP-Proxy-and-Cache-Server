from socket import *
import sys
from urllib.parse import urlparse

def proxyServer(port_no):
    tcp_server_socket = socket(AF_INET, SOCK_STREAM)
    tcp_server_socket.bind(("0.0.0.0", port_no))
    tcp_server_socket.listen(5)
    print(f"Proxy server is start {port_no}. wait for connections...")

    while True:
        try:
            tcp_client_socket, addr = tcp_server_socket.accept()
            print('Received a connection from:', addr)

            request = tcp_client_socket.recv(1024).decode()
            if not request:
                tcp_client_socket.close()
                continue

            request_line = request.splitlines()[0]
            print(f"{request_line}")

            try:
                method, full_url, http_version = request_line.split()
                if method != "GET":
                    raise ValueError("not supported, only GET")
            except ValueError:
                tcp_client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                tcp_client_socket.close()
                continue

            print('Connecting to original destination')

            parsed_url = urlparse(full_url)
            if not parsed_url.netloc or not parsed_url.path:
                tcp_client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                tcp_client_socket.close()
                continue

            print('Connecting to original destination')

            host = parsed_url.netloc
            path = parsed_url.path

            try:
                origin_socket = socket(AF_INET, SOCK_STREAM)
                origin_socket.connect((host, 80))
                origin_socket.send(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
                print('received reply from http server')
            except Exception:
                tcp_client_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
                tcp_client_socket.close()
                continue

            while True:
                response = origin_socket.recv(1024)
                if not response:
                    break
                tcp_client_socket.send(response)

            origin_socket.close()
            tcp_client_socket.close()
            print('reply forwarded to client')
        except KeyboardInterrupt:
            print("Proxy is close...")
            break
        except Exception as e:
            print(f"{e}")
            tcp_client_socket.close()

    tcp_server_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use: python3 ProxyServerSequencial.py <Port>")
        sys.exit(1)
    else:
        proxyServer(int(sys.argv[1]))

