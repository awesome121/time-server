"""
A program as a server to receive request from clients

Author: Changxing Gong
Date: 09/Aug/2020
"""
import socket, sys, select, datetime
HOST = '' #Automatically assigned to this device
PORT_ENG = 0    #Command argument
PORT_MAORI = 0  #Command argument
PORT_GER = 0    #Command argument

DATE_TEMPLATE = {}
TIME_TEMPLATE = {}
MONTH = {}

def set_datetime_template():
    """Set templates"""
    global PORT_ENG, PORT_MAORI, PORT_GER, DATE_TEMPLATE, TIME_TEMPLATE, MONTH

    DATE_TEMPLATE = {PORT_ENG : "Today’s date is {1} {0}, {2}",
                 PORT_MAORI : "Ko te ra o tenei ra ko {1} {0}, {2}",
                 PORT_GER : "Heute ist der {0}. {1} {2}"}

    TIME_TEMPLATE = {PORT_ENG : "The current time is {0}:{1}",
                 PORT_MAORI :"Ko te wa o tenei wa {0}:{1}",
                 PORT_GER : "Die Uhrzeit ist {0}:{1}"}

    MONTH = {PORT_ENG:{1:"January", 2:"February", 3:"March", 4:"April", 5:"May", 
                       6:"June", 7:"July", 8:"August", 9:"September", 10:"October",
                       11:"November", 12:"December"},

             PORT_MAORI:{1:"Kohitatea", 2:"Hui-tanguru", 3:"Poutu-te-rangi",
                         4:"Paenga-whawha ", 5:"Haratua", 6:"Pipiri",
                         7:"Hongongoi", 8:"Here-turi-koka", 9:"Mahuru",
                         10:"Whiringa-a-nuku", 11:"Whiringa-a-rangi", 12:"Hakihea"},

             PORT_GER:{1:"Januar", 2:"Februar", 3:"Marz", 4:"April", 5:"Mai", 6:"Juni",
                       7:"Juli", 8:"August", 9:"September", 10:"Oktober", 11:"November",
                       12:"Dezember"}
             }

def args_checker():
    """Check argument number and check if they are valid
       if they are valid then return (port1, port2, port3)
    """
    if len(sys.argv) == 4:
        try:
            port1 = int(sys.argv[1])
            port2 = int(sys.argv[2])
            port3 = int(sys.argv[3])
        except ValueError:
            print("Port numbers should be integer! [1024, 64000]\n")
            sys.exit("Invalid arguments")
        else:
            if port1 not in range(1024, 64001):
                print("Port number not in [1024, 64000]\n")
                sys.exit("Invalid arguments")
            if port2 not in range(1024, 64001):
                print("Port number not in [1024, 64000]\n")
                sys.exit("Invalid arguget_response_pktments")
            if port3 not in range(1024, 64001):
                print("Port number not in [1024, 64000]\n")
                sys.exit("Invalid arguments")
            else:
                return port1, port2, port3
    else:
        print("Three port numbers required [] [] []\n")
        sys.exit("Invalid arguments")

def get_response_pkt(typ, port):
    """Prepare response packet"""
    global PORT_ENG, PORT_MAORI, PORT_GER, DATE_TEMPLATE, TIME_TEMPLATE, MONTH
    magic_num = [0x49, 0x7E]
    pkt_type = [0, 2]
    if port == PORT_ENG:
        language_code = [0, 0x1]
    elif port == PORT_MAORI:
        language_code = [0, 0x2]
    elif port == PORT_GER:
        language_code = [0, 0x3]
    time = datetime.datetime.now().strftime("%d/%m/%Y/%H/%M")
    day, month, year, hour, minute = [int(num) for num in time.split('/')]
    buffer = magic_num + pkt_type + language_code + [year>>8, year&0b11111111, month, day, hour, minute, 0]
    if typ == 1:   #date
        text = DATE_TEMPLATE[port].format(day, MONTH[port][month], year)
    else:          #time
        if len(str(minute)) == 1:
            minute = '0' + str(minute)
        if len(str(hour)) == 1:
            hour = '0' + str(hour)
        text = TIME_TEMPLATE[port].format(hour, minute)
    datetime_buffer = bytearray(text.encode('utf-8'))
    if len(datetime_buffer) > 255:
        raise ValueError
    else:
        buffer[-1] = len(datetime_buffer)
        return bytearray(buffer) + datetime_buffer


def parse_pkt(data):
    """Parse incoming packet, drop the packet if it's unexpected"""
    if len(data) != 6:
        print("Unexpected packet length\n")
        raise TypeError
    elif (data[0] << 8) + data[1] != 0x497E:
        print("Unexpected MagicNo\n")
        raise TypeError
    elif (data[2] << 8) + data[3] != 1:
        print("Unexpected packet type\n")
        raise TypeError
    else:
        typ = (data[4] << 8) + data[5]
        if typ not in [1, 2]:
            print("Unexpected request type\n")
            raise TypeError
        return typ

def listening_loop(sock_eng, sock_maori, sock_ger):
    """infinite loop, not consuming CPU resource whlie waiting for request"""
    while True:
        print("Waiting for the next event....\n")
        readable, writble, excep = select.select([sock_eng, sock_maori, sock_ger], [], [],)
        for sock in readable:
            data, connection = sock.recvfrom(1024)
            try:
                typ = parse_pkt(bytearray(data))
                pkt = get_response_pkt(typ, sock.getsockname()[1])
            except TypeError:
                print(f"Unexpected packet from {connection}: Discard\n")
            except ValueError:
                print("Failed datetime_bufferto response: Too large text to carry\n")
            else:
                typ = "date" if typ == 1 else "time"
                print(f"A packet from {connection} requests for {typ}\n")
                sock.sendto(pkt, connection)
                print(f"Responded Successfully\n\n\n")

def main():
    """Main function"""
    global HOST, PORT_ENG, PORT_MAORI, PORT_GER
    PORT_ENG, PORT_MAORI, PORT_GER = args_checker()
    set_datetime_template()
    sock_eng = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_maori = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_ger = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock_eng.bind((HOST, PORT_ENG))
        sock_maori.bind((HOST, PORT_MAORI))
        sock_ger.bind((HOST, PORT_GER))
        print("Device name: " + socket.gethostname())
        print(f"Assigned port for English: {PORT_ENG}")
        print(f"Assigned port for Te reo Maori: {PORT_MAORI}")
        print(f"Assigned port for German: {PORT_GER}\n")
        listening_loop(sock_eng, sock_maori, sock_ger)
    except OSError:
        sock_eng.close()
        sock_maori.close()
        sock_ger.close()
        sys.exit("Can't bind these port numbers")
    except:
        sock_eng.close()
        sock_maori.close()
        sock_ger.close()
        sys.exit("\n\nStop listening")

main()
