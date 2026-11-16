import os

DIRECTORY = None

def handel(req):

    handler = ROUTES.get(req.route, handle_not_found)
    return handler(req)

def handle_root(req):
    return (b"HTTP/1.1 200 OK\r\n\r\n")

def handle_echo(req):
    length = len(req.route_value)
    header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
    return (header.encode() + req.route_value)


def handle_user_agent(req):
    if b"user-agent" in req.headers:
        length = len(str(req.headers[b"user-agent"].decode()))

        header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
        return (header.encode() + req.headers[b"user-agent"])
    return (b"HTTP/1.1 400 Bad Request\r\n\r\n")


def handel_file(req):
    if req.method == "POST":
        return handel_get_file(req)
    elif req.method == "GET" :
        return handel_post_file(req)

def handel_get_file(req):
    not_found = b"HTTP/1.1 404 Not Found\r\n\r\n"
    if DIRECTORY is None:
        return not_found

    name = req.path[len(b"/files/"):].decode(errors="replace")
    if not name:
        return not_found

    base = os.path.realpath(DIRECTORY)
    full_path = os.path.realpath(os.path.join(base, name))

    try:
        if os.path.commonpath([base, full_path]) != base:
            return not_found
        with open(full_path, "rb") as f:
            content = f.read()
    except (OSError, ValueError):
        return not_found

    header = ("HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
              f"Content-Length: {len(content)}\r\n\r\n")
    return header.encode() + content

def handel_post_file(req):
    ...

def handle_not_found(req):
    return (b"HTTP/1.1 404 Not Found\r\n\r\n")



ROUTES = {
    b"": handle_root,
    b"echo": handle_echo,
    b"user-agent": handle_user_agent,
    b"files" : handel_file
}
