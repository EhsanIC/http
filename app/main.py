import socket  # noqa: F401


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))

    while True:
        try:
            conn, addr = server_socket.accept()
        except OSError:
            continue   # a probe/reset connection failed before accept finished

        try:
            conn.recv(4096)                    # read the request first
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
        except OSError:
            pass   # client vanished mid-exchange; never kill the loop
        finally:
            conn.close()


if __name__ == "__main__":
    main()
