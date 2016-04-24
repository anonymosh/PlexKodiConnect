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
    }
    """
    def __init__(self):
        self.name = ''
        self.address = ''
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
        server = Server()    
        server.name =  value.get('name'),
        server.address =  value.get('address'),
        server.ip =  value.get('ip'),
        server.port =  value.get('port'),
        server.scheme =  value.get('scheme'),
        server.local =  value.get('local') == '1',
        server.owned =  value.get('owned') == '1',
        server.machineIdentifier =  value.get('uuid'),
        server.accesstoken =  value.get('accesstoken'),
        server.baseURL =  value.get('baseURL'),
        server.ownername =  value.get('ownername')
        return server

    def toStruct(self):
        d = {}
        d['plex_machineIdentifier'] =  self.machineIdentifier
        d['plex_servername'] =  self.name
        d['plex_serverowned'] = self.owned
        d['ipaddress'] =  self.ip
        d['port'] =  self.port
        d['ipaddress'] =  self.ipaddress
        d['port'] =  self.port
        return dict
