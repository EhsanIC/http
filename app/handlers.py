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


def handle_not_found(req):
    return (b"HTTP/1.1 404 Not Found\r\n\r\n")



ROUTES = {
    b"": handle_root,
    b"echo": handle_echo,
    b"user-agent": handle_user_agent,
}
