from dataclasses import dataclass

@dataclass
class Request:
    method: bytes
    path: bytes          # full target, e.g. b"/echo/abc"
    route: bytes         # first segment, e.g. b"echo"
    route_value: bytes   # second segment, e.g. b"abc"
    headers: dict
    body: bytes

def parse(data) -> Request | None:
    # all your current helper logic goes here
    # return None if the request is malformed
    starter_line , header_lines = _parse_request(data)
    _ , _, body = data.partition(b"\r\n\r\n") # body || b""

    parsed = _parse_starter_line(starter_line)
    if parsed == "" : return None       # in case of missing starter line parts

    method , route = parsed

    path , path_value = _parse_routes(route)
    headers = _parse_headers(header_lines)

    return Request(method=method, path=route, route=path, route_value=path_value, headers=headers, body=body)



def _parse_request(data):
    lines = data.split(b"\r\n\r\n")     # list of lines (bytes)
    head = lines[0]
    body = b""
    head_lines = head.split(b"\r\n")
    starter_line = head_lines[0]        # b'GET /user-agent HTTP/1.1'
    headers = head_lines[1:]            # [b'Host: ...', b'User-Agent: ...', b'Accept: ...']

    # parsed = _parse_starter_line(starter_line)
    # if parsed == "" : return None       # in case of missing starter line parts
    # method , route = parsed
    # if method == b"POST": body = lines[1]

    return starter_line , headers

def _parse_headers(headers):
    headers_list = {}

    for line in headers:
        name, _, value = line.partition(b":")
        headers_list[name.strip().lower()] = value.strip()

    return headers_list

def _parse_starter_line(starter_line):
    parts = starter_line.split(b" ")     # [b'GET', b'/abcdefg', b'HTTP/1.1']
    if len(parts) != 3:
        return ""

    method = parts[0]
    path = parts[1]

    return method , path


def _parse_routes(route):
    routes = route.split(b"/") # ["" , "echo" , "value"] || [""]

    path = b""
    path_value = b""

    if len(routes) > 1:
        path = routes[1]
        if len(routes) > 2:
            path_value = routes[2]

    return path , path_value

def _parse_body():
    ...

# // Request line
# POST /files/number HTTP/1.1
# \r\n

# // Headers
# Host: localhost:4221\r\n
# User-Agent: curl/7.64.1\r\n
# Accept: */*\r\n
# Content-Type: application/octet-stream  // Header that specifies the format of the request body
# Content-Length: 5\r\n                   // Header that specifies the size of the request body, in bytes
# \r\n

# // Request Body
# 12345
