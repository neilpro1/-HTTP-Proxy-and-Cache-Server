import os
from hashlib import md5
import sys
from socket import *
from urllib.parse import urlparse

CACHE_DIR = "proxy_cache"
cache_index = {}

def initialize_cache():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    global cache_index
    for file in os.listdir(CACHE_DIR):
        cache_index[file] = os.path.join(CACHE_DIR, file)

def get_cache_path(url):
    hashed_url = md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, hashed_url)

def handle_client_with_cache(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        if not request:
            client_socket.close()
            return

        request_line = request.splitlines()[0]
        print(f"{request_line}")

        try:
            method, full_url, http_version = request_line.split()
            if method != "GET":
                raise ValueError("Not supported, only GET")
        except ValueError:
            client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            return

        print('Connecting to original destination')

        parsed_url = urlparse(full_url)
        if not parsed_url.netloc or not parsed_url.path:
            client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            return

        print('Connecting to original destination')

        host = parsed_url.netloc
        path = parsed_url.path

        # Check cache index
        if full_url in cache_index:
            with open(cache_index[full_url], "rb") as cached_file:
                client_socket.sendall(cached_file.read())
            client_socket.close()
            print("Cache hit. Serving from cache.")
            print('reply forwarded to client')
            return
        else:
            cache_path = get_cache_path(full_url)
            print("Cache miss. Fetching from origin server.")


        try:
            origin_socket = socket(AF_INET, SOCK_STREAM)
            origin_socket.connect((host, 80))
            origin_socket.send(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        except Exception:
            client_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
            client_socket.close()
            return
        print('received reply from http server')

        # Fetch response and store in cache
        with open(cache_path, "wb") as cached_file:
            while True:
                response = origin_socket.recv(1024)
                if not response:
                    break
                cached_file.write(response)
                client_socket.send(response)

        # Update cache index
        cache_index[full_url] = cache_path
        origin_socket.close()
        client_socket.close()
        print('reply forwarded to client')

    except Exception as e:
        print(f"{e}")
        client_socket.close()

def proxyServer(port_no):
 
    initialize_cache()
    tcp_server_socket = socket(AF_INET, SOCK_STREAM)
    tcp_server_socket.bind(("0.0.0.0", port_no))
    tcp_server_socket.listen(5)
    print(f"Proxy is start in {port_no}. wait for connections...")

    while True:
        try:
            client_socket, addr = tcp_server_socket.accept()
            print('Received a connection from:', addr)
            handle_client_with_cache(client_socket)
        except KeyboardInterrupt:
            print("Shutting down proxy server.")
            break
        except Exception as e:
            print(f"{e}")

    tcp_server_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 ProxyServerSequencialCache.py <port>")
        sys.exit(1)
    else:
        proxyServer(int(sys.argv[1]))
