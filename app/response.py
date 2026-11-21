import gzip

def response(res_code=200 , content = None , headers = None , content_type="text/plain"):
    headers = headers or {}

    connection_status = headers.get(b"connection", b"")


    if content is  None:
        if connection_status == b"close" :
            return RESPONSE_TYPE.get(res_code , RES404RAW)(True)
        return RESPONSE_TYPE.get(res_code , RES404RAW)()

    encoding = None
    accepted = headers.get(b"accept-encoding", b"")

    if b"gzip" in [s.strip() for s in accepted.split(b",")]:
        encoding = "gzip"
        content = gzip.compress(content)

    # for header in headers:
    #     if b"accept-encoding" in header and b"gzip" in header["accept-encoding"]:
    #         encoding = "gzip"
    #     if b"content-type" in header and b"application/octet-stream" in header["content-type"]:
    #         content_type = "application/octet-stream"

    head = f"HTTP/1.1 {res_code} {STATUS_TEXT[res_code]}\r\n"
    head += f"Content-Type: {content_type}\r\n"

    if encoding:
        head += f"Content-Encoding: {encoding}\r\n"
    if connection_status == b"close":
        head += "Connection: close\r\n"
    head += f"Content-Length: {len(content)}\r\n"

    head += "\r\n"
    return head.encode() + content

    # header = ("HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
    #           f"Content-Length: {len(content)}\r\n\r\n")
    # return header.encode() + content

# status codes //==================================================================================================================================================>
# 200s
def RES200RAW(close = False):
    if close:
        return b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n"
    return b"HTTP/1.1 200 OK\r\n\r\n"

# def RES200TXT(value):
#     return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(value.decode())}\r\n\r\n".encode() + value

def RES201RAW(close = False):
    if close:
        return b"HTTP/1.1 201 Created\r\nConnection: close\r\n\r\n"
    return b"HTTP/1.1 201 Created\r\n\r\n"

# 400s
def RES400RAW(close = False):
    if close:
        return b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
    return b"HTTP/1.1 400 Bad Request\r\n\r\n"

def RES404RAW(close = False):
    if close:
        return b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
    return b"HTTP/1.1 404 Not Found\r\n\r\n"



RESPONSE_TYPE = {
    200 : RES200RAW,
    201 : RES201RAW,
    400 : RES400RAW,
    404 : RES404RAW,
}

STATUS_TEXT = {
    200 : "OK",
    201 : "Created",
    400 : "Bad Request",
    404 : "Not Found"
}
