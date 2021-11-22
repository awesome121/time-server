"""
A program as a client to request for date or time

Author: Changxing Gong
Date: 09/Aug/2020
"""
import socket, sys, select
WAITING_TIME = 1

def args_checker():
    """Check argument number and check if they are valid
       if they are valid then return (request, (host, port))
    """
    message = ''
    if len(sys.argv) == 4:
        if sys.argv[1] not in ["date", "time"]:
            message += 'First argument: "date" or "time" only\n\n'
        try:
            address = None
            conn = socket.getaddrinfo(sys.argv[2], None)
            for family, kind, _, _, addr in conn:
                if family == socket.AddressFamily.AF_INET and kind == socket.SocketKind.SOCK_DGRAM:
                    address = addr
            if address is None:
                raise TypeError
        except:
            message += 'Second argument: invalid IP address or domain name\n\n'
        try:
            if int(sys.argv[3]) > 64000 or int(sys.argv[3]) < 1024:
                message += 'Third argument: invalid port number (must between 1024 and 64000 inclusive)\n\n'
        except:
            message += 'Third argument: not an integer (must between 1024 and 64000 inclusive)\n\n'
        if message != '':
            print(message)
            sys.exit('Invalid arguments')
        else:
            message += 'Sending request...\n'
            print(message)
            return sys.argv[1], (address[0], int(sys.argv[3]))
    else:
        message += "To request a date-time packet, you need exactly 3 arguments: [] [] [] \n\n"
        message += 'Request type: "date" or "time"\n\n'
        message += 'IP address(e.g. "000.00.00.000") or server name (e.g. "datetime.example.nz")\n\n'
        message += 'Port number: [1024, 64000]\n\n'
        print(message)
        sys.exit('Invalid arguments')

def get_request_pkt(request):
    """Prepare request packet"""
    magic_num = [0x49, 0x7E]
    pkt_type = [0, 1]
    request_type = [0, request]
    buffer = magic_num + pkt_type + request_type
    return bytearray(buffer)

def parse_pkt(data):
    """Parse incoming packet, exit the program if it's unexpected"""
    if len(data) < 13:
        print("Unexpected packet: too few bytes recevied")
        sys.exit()
    magicNo = (data[0] << 8) + data[1]
    pkt_typ = (data[2] << 8) + data[3]
    lang_code = (data[4] << 8) + data[5]
    year = (data[6] << 8) + data[7]
    month, day, hour, minute = data[8], data[9], data[10], data[11]
    length = data[12]
    if magicNo != 0x497E:
        print("Unexpected packet: magic number not match")
        raise TypeError
    elif pkt_typ != 0x0002: #Response pkt
        print("Unexpected packet: Not a reponse packet")
        raise TypeError
    elif lang_code not in [0x0001, 0x0002, 0x0003]: #Eng, Mao , Ger
        print("Unexpected packet: Can not recognise language contained")
        raise TypeError
    elif year >= 2100:
        print("Unexpected date: not a valid year")
        raise TypeError
    elif month not in range(1, 13):
        print("Unexpected date: not a valid month")
        raise TypeError
    elif day not in range(1, 32):
        print("Unexpected date: not a valid day")
        raise TypeError
    elif hour not in range(0, 24):
        print("Unexpected time: not a valid hour")
        raise TypeError
    elif minute not in range(0, 60):
        print("Unexpected time: not a valid minute")
        raise TypeError
    elif length != len(data[13:]):
        print("Unexpected length: actual packet length not match")
        raise TypeError
    else:
        if lang_code == 0x1:
            lang = "English"
        elif lang_code == 0x2:
            lang = "Te reo Maori"
        else:
            lang = "German"
        print(f"MagicNo: {hex(magicNo)}")
        print(f"Packet type: {hex(pkt_typ)}")
        print(f"language code: {hex(lang_code)} ({lang})")
        print(f"Year: {year}")
        print(f"Month: {month}")
        print(f"Day: {day}")
        print(f"Hour: {hour}")
        print(f"Minute: {minute}")
        print(f"Textual representation: \"{data[13:].decode('utf-8')}\"\n\n")

def wait_for_response(sock, address):
    """Wait for server to respond
       WAITING_TIME default to 1 second
    """
    global WAITING_TIME
    readable, _, _ = select.select([sock], [], [], WAITING_TIME)
    if len(readable) == 0:
        sock.close()
        sys.exit(f"Timeout: No response from {address}")
    else:
        data, address = sock.recvfrom(1024)
        print(f"Receiving from {address}\n")
        return data

def main():
    """Main function"""
    request, address = args_checker()
    request = 1 if request == "date" else 2
    request_pkt = get_request_pkt(request)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(request_pkt, address)
        data = wait_for_response(sock, address)
        parse_pkt(data)
    except OSError:
        print("Failed to send: Invalid address\n")
        sock.close()
        sys.exit("Invalid arguments")
    except TypeError:
        sys.exit("Can't parse the packet")
    else:
        sock.close()
        sys.exit("Succcess")


main()
