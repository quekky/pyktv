import socket
import platform
import re
import requests
import struct
import array
from xml.etree import ElementTree
from urllib import parse
import settings

DISCOVERY_MSG = ('M-SEARCH * HTTP/1.1\r\n' +
                 'ST: urn:schemas-upnp-org:device:MediaServer:1\r\n' +
                 'MX: 3\r\n' +
                 'MAN: "ssdp:discover"\r\n' +
                 'HOST: 239.255.255.250:1900\r\n\r\n').encode('utf-8')

def interface_addresses(family=socket.AF_INET):
    """Get all ip address of client"""

    if platform.system() == 'Windows':
        for fam, _, _, _, sockaddr in socket.getaddrinfo('', None):
            if family == fam:
                yield sockaddr[0]

    else:
        # Linux
        import fcntl
        SIOCGIFCONF = 0x8912
        SIOCGIFFLAGS = 0x8913
        IFF_UP = 0x1
        IFF_LOOPBACK = 0x8
        IFF_MULTICAST = 0x1000

        # An ugly hack to account for different ifreq sizes on
        # different architectures
        arch = platform.architecture()[0]
        if arch == "32bit":
            offsets = (32, 32)
        elif arch == "64bit":
            offsets = (16, 40)
        else:
            raise OSError("Unsupported architecture: %s" % (arch))

        # Get the list of all network interfaces
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer = array.array('B', b'\0' * 128 * offsets[1])
        reply_length = struct.unpack('iL', fcntl.ioctl(_socket.fileno(), SIOCGIFCONF, struct.pack('iL', 4096, buffer.buffer_info()[0])))[0]
        if_list = buffer.tostring()
        if_list = filter(lambda x: len(x[0]) > 0,
                         [(if_list[i:i + offsets[0]].split(b'\0', 1)[0], socket.inet_ntoa(if_list[i + 20:i + 24]))
                          for i in range(0, 4096, offsets[1])])

        # Get ip addresses for each interface
        for (ifname, addr) in if_list:
            flags, = struct.unpack('H', fcntl.ioctl(_socket.fileno(), SIOCGIFFLAGS, ifname + b'\0' * 256)[16:18])
            if not(flags & IFF_LOOPBACK) and (flags & IFF_UP) and (flags & IFF_MULTICAST):
                yield(addr)

        _socket.close()


def get_attribute(xml, xml_name):
    """Tries to get an element extracted from the XML."""
    try:
        return xml.find(xml_name).text
    except AttributeError:
        return

def discoverDLNA():
    """
    Find DLNA servers on the local network.
    Fill in the name, Control URL and Service Type

    :return: list of servers
    """
    socket.setdefaulttimeout(1)
    location_regex = re.compile("location:[ ]*(.+)\r\n", re.IGNORECASE)
    servers = []

    for addr in interface_addresses():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.bind((addr, 0))
        sock.sendto(DISCOVERY_MSG, ('239.255.255.250', 1900))

        while True:
            try:
                location_result = location_regex.search(sock.recv(1024).decode('utf-8'))
                servers.append({'location':location_result[1]})
            except socket.timeout:
                break
        sock.close()

    for location in servers:
        try:
            resp = requests.get(location['location'], timeout=2)
            try:
                xmlRoot = ElementTree.fromstring(resp.text)
            except:
                #Failed XML parsing
                continue

            location["name"] = get_attribute(xmlRoot,"./{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}friendlyName")

            iconurl = xmlRoot.find(".//*{urn:schemas-upnp-org:device-1-0}icon/{urn:schemas-upnp-org:device-1-0}url")
            if iconurl is not None:
                location['image'] = parse.urljoin(location['location'], iconurl.text)

            # service = xmlRoot.find('.//*{urn:schemas-upnp-org:device-1-0}service[{urn:schemas-upnp-org:device-1-0}serviceType="urn:schemas-upnp-org:service:ContentDirectory:1"]')
            # location["controlURL"] = parse.urljoin(location['location'], service.find('./{urn:schemas-upnp-org:device-1-0}controlURL').text)
            # location["servicetype"] = service.find('./{urn:schemas-upnp-org:device-1-0}serviceType').text

            services = xmlRoot.findall(".//*{urn:schemas-upnp-org:device-1-0}serviceList/")
            for service in services:
                serviceURL = parse.urljoin(location['location'], service.find('./{urn:schemas-upnp-org:device-1-0}SCPDURL').text)
                # read in the SCP XML
                resp = requests.get(serviceURL, timeout=2)
                try:
                    serviceXML = ElementTree.fromstring(resp.text)
                except:
                    #Failed to parse the response XML
                    continue;

                actions = serviceXML.findall(".//*{urn:schemas-upnp-org:service-1-0}action")
                for action in actions:
                    if action.find('./{urn:schemas-upnp-org:service-1-0}name').text == 'Browse':
                        location["controlURL"] = parse.urljoin(location['location'], service.find('./{urn:schemas-upnp-org:device-1-0}controlURL').text)
                        location["servicetype"] = service.find('./{urn:schemas-upnp-org:device-1-0}serviceType').text

        except requests.exceptions.ConnectionError:
            settings.logger.warning('[!] Could not load %s' % location)
        except requests.exceptions.ReadTimeout:
            settings.logger.warning('[!] Timeout reading from %s' % location)

    return servers


def find_directories(server, parentobject=0):
    """
    Send a 'Browse' request for the directory.

    :param server: DLNA server
    :param parentobject: object number to search for
    :return: list of children
    """
    if 'servicetype' not in server.keys() or 'controlURL' not in server.keys():
        return
    payload = ('<?xml version="1.0" encoding="utf-8" standalone="yes"?>' +
               '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' +
               '<s:Body>' +
               '<u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">' +
               '<ObjectID>' + str(parentobject) +  '</ObjectID>' +
               '<BrowseFlag>BrowseDirectChildren</BrowseFlag>' +
               '<Filter>*</Filter>' +
               '<StartingIndex>0</StartingIndex>' +
               '<RequestedCount>0</RequestedCount>' +
               '<SortCriteria></SortCriteria>' +
               '</u:Browse>' +
               '</s:Body>' +
               '</s:Envelope>')

    soapActionHeader = { 'Soapaction' : '"' + server['servicetype'] + '#Browse' + '"',
                         'Content-type' : 'text/xml;charset="utf-8"' }

    resp = requests.post(server['controlURL'], data=payload, headers=soapActionHeader)
    if resp.status_code != 200:
        settings.logger.warning('Request failed with status: %d' % resp.status_code)
        return

    try:
        xmlRoot = ElementTree.fromstring(resp.text)
        containers = xmlRoot.find(".//*Result").text
        if not containers:
            return

        children = []
        xmlRoot = ElementTree.fromstring(containers)
        containers = xmlRoot.findall("./{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}container")
        for container in containers:
            try:
                child = {'type':'container'}
                child['id'] = container.get('id')
                child['parentID'] = container.get('parentID')
                child['class'] = container.find("./{urn:schemas-upnp-org:metadata-1-0/upnp/}class").text
                child['title'] = container.find("./{http://purl.org/dc/elements/1.1/}title").text

                children.append(child)
            except:
                settings.logger.printException()

        items = xmlRoot.findall("./{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item")
        for item in items:
            try:
                child = {'type':'item'}
                child['id'] = item.get('id')
                child['parentID'] = item.get('parentID')
                child['class'] = item.find("./{urn:schemas-upnp-org:metadata-1-0/upnp/}class").text
                child['title'] = item.find("./{http://purl.org/dc/elements/1.1/}title").text
                try:
                    res = item.find("./{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res")
                    child['url'] = res.text
                    child['size'] = res.get('size')
                    child['duration'] = res.get('duration')
                except:
                    pass
                try:
                    child['artist'] = item.find("./{urn:schemas-upnp-org:metadata-1-0/upnp/}artist").text
                except:
                    pass
                try:
                    child['image'] = item.find("./{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI").text
                except:
                    pass

                children.append(child)
            except:
                settings.logger.printException()

        return children
    except:
        settings.logger.printException('Failed to parse the response XML')


if __name__ == "__main__":
    servers=discoverDLNA()
    print(servers)
    for s in servers:
        print(find_directories(s))
        # print(find_directories(s,26))
