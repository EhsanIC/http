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
# def response(res_code = 404, content = None , header = None):

#     if content == None:
#         response = RESPONSE_TYPE.get(res_code , RES404RAW)
#         return response()

#     accepted = (header or {}).get(b"accept-encoding", b"")

#     if b"gzip" in accepted:
#         return (f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
#                 f"Content-Length: {len(content)}\r\n"
#                 f"Content-Encoding: gzip\r\n\r\n").encode() + content

#     return RES200TXT(content)

# Corrected builder
# def response(res_code=200, content=None, headers=None):
#     headers = headers or {}

#     if content is None:
#         return RESPONSE_TYPE.get(res_code, RES404RAW)()

#     encoding = None
#     accepted = headers.get(b"accept-encoding", b"")
#     if b"gzip" in [s.strip() for s in accepted.split(b",")]:
#         encoding = "gzip"

#     head = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"

#     if encoding:
#         head += f"Content-Encoding: {encoding}\r\n"
#     head += f"Content-Length: {len(content)}\r\n\r\n"

#     return head.encode() + content


def response(res_code=200 , content = None , headers = None):
    headers = headers or {}

    if content is  None:
        return RESPONSE_TYPE.get(res_code , RES404RAW)()

    encoding = None
    accepted = headers.get(b"accept-encoding", b"")

    # list = []
    # for s in accepted.split(b","):
    #     list = s.strip()
    #     if b"gzip" in list:
    #         encoding = b"gzip"

    if b"gzip" in [s.strip() for s in accepted.split(b",")]:
        encoding = "gzip"

    head = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"

    if encoding:
        head += f"Content-Encoding: {encoding}\r\n"
    head += f"Content-Length: {len(content)}\r\n"
    head += "\r\n"
    return head.encode() + content



RESPONSE_TYPE = {
    200 : RES200RAW,
    201 : RES201RAW,
    400 : RES400RAW,
    404 : RES404RAW,
}



# response(200 , content = None , {"user_agent" : "samsung"} || None)
