import socket


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))

    while True:
        try:
            conn, addr = server_socket.accept()
        except OSError:
            continue   # a probe/reset connection failed before accept finished


    # // Request line
    # GET
    # /user-agent
    # HTTP/1.1
    # \r\n

    # // Headers
    # Host: localhost:4221\r\n
    # User-Agent: foobar/1.2.3\r\n  // Read this value
    # Accept: */*\r\n
    # \r\n

    # // Request body (empty)

        try:
            data = conn.recv(4096)          # read the request first
            lines = data.split(b"\r\n\r\n")     # list of lines (bytes)
            head = lines[0]
            head_lines = head.split(b"\r\n")
            starter_line = head_lines[0]    # b'GET /user-agent HTTP/1.1'
            header_lines = head_lines[1:]   # [b'Host: ...', b'User-Agent: ...', b'Accept: ...']


            parts = starter_line.split(b" ")     # [b'GET', b'/abcdefg', b'HTTP/1.1']
            if len(parts) < 2:
                continue
            path = parts[1]
            routes = path.split(b"/") # ["echo" , "value"]

            headers = {}

            if len(header_lines) >= 1 :
                # print(key_header + b" * and * " + value_header )


                for line in header_lines:
                    name, _, value = line.partition(b":")
                    headers[name.strip().lower()] = value.strip()

            # print(parts)
            # print(path)
            # print(routes)

            if path == b"/" :
                conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
            elif routes[1] == b"echo"  :
                length = len(str(routes[2].decode()))
                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + routes[2])

            elif routes[1] == b"user-agent" and b"user-agent" in headers:

                length = len(str(headers[b"user-agent"].decode()))

                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + headers[b"user-agent"])

            else :
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


        except OSError:
            pass   # client vanished mid-exchange; never kill the loop
        finally:
            conn.close()


if __name__ == "__main__":
    main()


    # // Request line
    # GET
    # /user-agent
    # HTTP/1.1
    # \r\n

    # // Headers
    # Host: localhost:4221\r\n
    # User-Agent: foobar/1.2.3\r\n  // Read this value
    # Accept: */*\r\n
    # \r\n

    # // Request body (empty)
