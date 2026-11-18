# 200s
def RES200RAW():
    return b"HTTP/1.1 200 OK\r\n\r\n"

def RES200TXT(value):
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(value.decode())}\r\n\r\n".encode() + value

def RES201RAW():
    return b"HTTP/1.1 201 Created\r\n\r\n"

# 400s
def RES400RAW():
    return b"HTTP/1.1 400 Bad Request\r\n\r\n"

def RES404RAW():
    return b"HTTP/1.1 404 Not Found\r\n\r\n"

# response(200 , content = None , {"user_agent" : "samsung"} || None)
def response(res_code = 404, content = None , header = None):

    # new_header = b""

    # if "Accept-Encoding" in req.header:
    #     if "gzip" in req.header.get("Accept-Encoding"):

    if content == None:
        response = RESPONSE_TYPE.get(res_code , RES404RAW)
        return response()
        # handler = ROUTES.get(req.route, RES404RAW)
        # return handler(req)

    # if content and header == None:
    #     return RES200TXT(content)
    #
    accepted = (header or {}).get(b"accept-encoding", b"")

    if b"gzip" in accepted:
        return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                f"Content-Length: {len(content)}\r\n"
                f"Content-Encoding: gzip\r\n\r\n").encode() + content

    return RES200TXT(content)
    # if header != None:
    #     if content != None and b"gzip" in header[b"accept-encoding"] in header:
    #         # if header[b"Accept-Encoding"] == b"gzip":
    #         # if b"gzip" in header[b"accept-encoding"]:
    #             return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(content.decode())}\r\nContent-Encoding: gzip\r\n\r\n".encode() + content


    # return RES200TXT(content)

    # return RES404RAW()

RESPONSE_TYPE = {
    200 : RES200RAW,
    201 : RES201RAW,
    400 : RES400RAW,
    404 : RES404RAW,
}



# response(200 , content = None , {"user_agent" : "samsung"} || None)
