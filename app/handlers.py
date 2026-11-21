import os
from app.response import RES404RAW , response

DIRECTORY = None

def handel(req):

    # check for the headers

    handler = ROUTES.get(req.route, lambda r:  RES404RAW(r.headers.get(b"connection") == b"close"))
    return handler(req)


def handle_root(req):
    return response(200, None, req.headers)


def handle_echo(req):
    return response(200 , req.route_value , req.headers)
    # return RES200TXT(req.route_value)


def handle_user_agent(req):
    if b"user-agent" in req.headers:
        return response(200 , req.headers[b"user-agent"], req.headers)
    return response(400, None, req.headers)


def handel_file(req):
    if req.method == b"POST":
        return handel_post_file(req)
    elif req.method == b"GET" :
        return handel_get_file(req)

def handel_get_file(req):
    not_found = response(404, None, req.headers)
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

    return response(200, content, req.headers, content_type="application/octet-stream")

def handel_post_file(req):
    not_found = response(404, None, req.headers)
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
            return response(201, None, req.headers)

    except (OSError, ValueError):
        return not_found





ROUTES = {
    b"": handle_root,
    b"echo": handle_echo,
    b"user-agent": handle_user_agent,
    b"files" : handel_file
}
