import os
from app.response import RES200RAW, RES200TXT, RES201RAW, RES400RAW, RES404RAW , response

DIRECTORY = None

def handel(req):

    # check for the headers

    handler = ROUTES.get(req.route, lambda r:  RES404RAW())
    return handler(req)


def handle_root(req):
    return RES200RAW()


def handle_echo(req):
    return response(200 , req.route_value , req.headers)
    # return RES200TXT(req.route_value)


def handle_user_agent(req):
    if b"user-agent" in req.headers:
        return RES200TXT(req.headers[b"user-agent"])
    return RES400RAW()


def handel_file(req):
    if req.method == b"POST":
        return handel_post_file(req)
    elif req.method == b"GET" :
        return handel_get_file(req)

def handel_get_file(req):
    not_found = RES404RAW()
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
    not_found = RES404RAW()
    if DIRECTORY is None:
        return not_found

    name = req.path[len(b"/files/"):].decode(errors="replace")
    if not name:
        return not_found

    base = os.path.realpath(DIRECTORY)
    full_path = os.path.realpath(os.path.join(base, name))
    content = req.body

    try:
        if os.path.commonpath([base, full_path]) != base:
            return not_found
        with open(full_path, "wb") as f:
            f.write(content)
            return RES201RAW()

    except (OSError, ValueError):
        return not_found





ROUTES = {
    b"": handle_root,
    b"echo": handle_echo,
    b"user-agent": handle_user_agent,
    b"files" : handel_file
}
