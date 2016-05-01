from utils import logging

@logging
class Server():
    """
    Output: List of all servers, with an entry of the form:
    {
    'name': friendlyName,      the Plex server's name
    'address': ip:port
    'ip': ip,                   without http/https
    'port': port
    'scheme': 'http'/'https',   nice for checking for secure connections
    'local': '1'/'0',           Is the server a local server?
    'owned': '1'/'0',           Is the server owned by the user?
    'machineIdentifier': id,    Plex server machine identifier
    'accesstoken': token        Access token to this server
    'baseURL': baseURL          scheme://ip:port
    'ownername'                 Plex username of PMS owner
    'serverOffset'              milliseconds between server and local wall clock
    }
    """
    def __init__(self):
        self.name = ''
        self.address = ''
        self.host = ''
        self.ip = ''
        self.port = ''
        self.scheme = ''
        self.local = False
        self.owned = False
        self.machineIdentifier = ''
        self.accesstoken = ''
        self.baseURL = ''
        self.ownername = ''
        
    @classmethod
    def parse(cls, value):
        print "val: %r" % value
        server = Server()    
        server.name =  value.get('name')
        server.address =  value.get('address')
        server.ip =  value.get('ip')
        server.port =  value.get('port')
        server.scheme =  value.get('scheme')
        server.machineIdentifier =  value['uuid']
        server.accesstoken = value.get('accesstoken')
        server.baseURL =  value.get('baseURL')
        server.ownername =  value.get('ownername')
        server.local =  value.get('local') == '1'
        server.owned =  value.get('owned') == '1'
        
        return server

    def __str__(self):
        return ','.join("%s:%r" % (entry[0],entry[1]) for entry in vars(self).items())

    def __repr__(self):
        url = 'http'
        if self.scheme == 'https':
            url = 'https'
        host = self.ip
        if self.host:
            host = self.host
        port = ''
        if self.port:
            port = ":"+self.port
        return "%s://%s%s" % (url, host, port)
        
    @classmethod
    def fromString(cls, s):
        server = Server()
        d = {}
        a = s.split(',')
        for entry in a:
            print entry
            (key,value) = entry.split(':')
            d[key] = value
        server.__dict__.update(d)
        return server
