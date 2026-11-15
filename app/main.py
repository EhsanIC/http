import socket


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))

    while True:
        try:
            conn, addr = server_socket.accept()
        except OSError:
            continue   # a probe/reset connection failed before accept finished

        try:
            data = conn.recv(4096)          # read the request first
            starter_line , header_lines = parse_request(data)

            parsed_starter_line = parse_starter_line(starter_line)
            if parsed_starter_line == "" : continue   # in case of missing starter line parts
            method , route = parsed_starter_line

            path , path_value = parse_routes(route)


            headers = parse_headers(header_lines)


            if path == b"" :
                conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

            elif path == b"echo"  :

                length = len(str(path_value.decode()))
                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + path_value)

            elif path == b"user-agent" and b"user-agent" in headers:

                length = len(str(headers[b"user-agent"].decode()))

                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + headers[b"user-agent"])

            else :
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


        except OSError:
            pass   # client vanished mid-exchange; never kill the loop
        finally:
            conn.close()



def parse_request(data):
    lines = data.split(b"\r\n\r\n")     # list of lines (bytes)
    head = lines[0]
    head_lines = head.split(b"\r\n")
    starter_line = head_lines[0]    # b'GET /user-agent HTTP/1.1'
    headers = head_lines[1:]   # [b'Host: ...', b'User-Agent: ...', b'Accept: ...']

    return starter_line , headers

def parse_headers(headers):
    headers_list = {}

    for line in headers:
        name, _, value = line.partition(b":")
        headers_list[name.strip().lower()] = value.strip()

    return headers_list

def parse_starter_line(starter_line):
    parts = starter_line.split(b" ")     # [b'GET', b'/abcdefg', b'HTTP/1.1']
    if len(parts) != 3:
        return ""

    method = parts[0]
    path = parts[1]

    return method , path


def parse_routes(route):
    routes = route.split(b"/") # ["" , "echo" , "value"] || [""]

    path = b""
    path_value = b""

    if len(routes) > 1:
        path = routes[1]
        if len(routes) > 2:
            path_value = routes[2]

    return path , path_value


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
