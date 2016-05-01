# -*- coding: utf-8 -*-

###############################################################################

import xbmc
import xbmcgui
import xbmcaddon

import utils
import clientinfo
import downloadutils
import userclient
import devices

from PlexFunctions import GetMachineIdentifier

import PlexAPI

###############################################################################

PLEX_SERVER = devices.Server()
PLEX_SERVER.scheme = 'https'
PLEX_SERVER.host = 'plex.tv'

@utils.logging
class InitialSetup():

    def __init__(self):
        self.clientInfo = clientinfo.ClientInfo()
        self.addonId = self.clientInfo.getAddonId()
        self.doUtils = downloadutils.DownloadUtils().downloadUrl
        self.userClient = userclient.UserClient()
        self.plx = PlexAPI.PlexAPI()

    def chooseServer(self, token):
        dialog = xbmcgui.Dialog()
        string = xbmcaddon.Addon().getLocalizedString
        # Populate g_PMS variable with the found Plex servers
        self.plx.discoverPMS(xbmc.getIPAddress(),
                             plexToken=token)
        self.logMsg('g_PMS: %s' % self.plx.g_PMS, 1)
        serverlist = self.plx.returnServerList(self.plx.g_PMS)
        self.logMsg('PMS serverlist: %s' % serverlist, 2)
        # Let user pick server from a list
        # Get a nicer list
        dialoglist = []
        # Exit if no servers found
        if len(serverlist) == 0:
            dialog.ok(
                self.addonName,
                string(39011)
            )
            return None
        for server in serverlist:
            if server.local:
                # server is in the same network as client. Add "local"
                msg = string(39022)
            else:
                # Add 'remote'
                msg = string(39054)
            if server.ownername:
                # Display username if its not our PMS
                dialoglist.append('%s (%s, %s)'
                                  % (server.name,
                                     server.ownername,
                                     msg))
            else:
                dialoglist.append('%s (%s)'
                                  % (server.name,
                                     msg))
        resp = dialog.multiselect(string(39012), dialoglist)
        if resp:
            map(lambda idx:serverlist[idx], resp)   
        return None
        
    def setup(self, forcePlexTV=False, chooseServer=False):
        """
        Initial setup. Run once upon startup.
        Check server, user, direct paths, music, direct stream if not direct
        path.
        """
        string = xbmcaddon.Addon().getLocalizedString
        # SERVER INFO #####
        self.logMsg("Initial setup called.", 0)
        # Get Plex credentials from settings file, if they exist
        plexdict = self.plx.GetPlexLoginFromSettings()
        myplexlogin = plexdict['myplexlogin']
        plexLogin = plexdict['plexLogin']
        plexToken = plexdict['plexToken']
        plexid = plexdict['plexid']
        if plexToken:
            self.logMsg('Found plex.tv token in settings', 0)

        dialog = xbmcgui.Dialog()

        # Optionally sign into plex.tv. Will not be called on very first run
        # as plexToken will be ''
        if (plexToken and myplexlogin == 'true' and forcePlexTV is False
                and chooseServer is False):
            chk = self.plx.CheckConnection('plex.tv', '', token=plexToken)
            try:
                chk.attrib
            except:
                pass
            else:
                # Success - we downloaded an xml!
                chk = 200
            # HTTP Error: unauthorized. Token is no longer valid
            if chk in (401, 403):
                self.logMsg('plex.tv connection returned HTTP %s' % chk, 0)
                # Delete token in the settings
                utils.settings('plexToken', value='')
                # Could not login, please try again
                dialog.ok(self.addonName,
                          string(39009))
                result = self.plx.PlexTvSignInWithPin()
                if result:
                    plexLogin = result['username']
                    plexToken = result['token']
                    plexid = result['plexid']
            elif chk is False or chk >= 400:
                # Problems connecting to plex.tv. Network or internet issue?
                self.logMsg('plex.tv connection returned HTTP %s'
                            % str(chk), 0)
                dialog.ok(self.addonName,
                          string(39010))
            else:
                self.logMsg('plex.tv connection with token successful', 0)
                # Refresh the info from Plex.tv
                xml = self.doUtils(PLEX_SERVER, '/users/account',
                                   authenticate=False,
                                   headerOptions={'X-Plex-Token': plexToken})
                try:
                    xml.attrib
                except:
                    self.logMsg('Failed to update Plex info from plex.tv', -1)
                else:
                    plexLogin = xml.attrib.get('title')
                    utils.settings('plexLogin', value=plexLogin)
                    home = 'true' if xml.attrib.get('home') == '1' else 'false'
                    utils.settings('plexhome', value=home)
                    utils.settings('plexAvatar', value=xml.attrib.get('thumb'))
                    utils.settings(
                        'plexHomeSize', value=xml.attrib.get('homeSize', '1'))
                    self.logMsg('Updated Plex info from plex.tv', 0)


        server = self.userClient.getActiveServer()
        # If a Plex server IP has already been set, return.
        if len(server) > 0 and forcePlexTV is False and chooseServer is False:
            self.logMsg("Server are already set.", 0)
            self.logMsg("url: %s, Plex machineIdentifiers: %s"
                        % (server, ",".join("%s" %s.machineIdentifier for s in server)), 0)
            return

        # If not already retrieved myplex info, optionally let user sign in
        # to plex.tv. This DOES get called on very first install run
        if ((not plexToken and myplexlogin == 'true' and chooseServer is False)
                or forcePlexTV):
            result = self.plx.PlexTvSignInWithPin()
            if result:
                plexLogin = result['username']
                plexToken = result['token']
                plexid = result['plexid']
        # Get g_PMS list of servers (saved to plx.g_PMS)
        serverlist = self.chooseServer(plexToken)
        if not serverlist:
            return
        activeServer = []
        failedServer = []
        for server in serverlist:
            httpsUpdated = False
            while True:
                # Deactive SSL verification if the server is local!
                # Watch out - settings is cached by Kodi - use dedicated var!
                if server.local:
                    utils.settings('sslverify', 'false')
                    self.logMsg("Setting SSL verify to false, because server is "
                                "local", 1)
                    verifySSL = False
                else:
                    utils.settings('sslverify', 'true')
                    self.logMsg("Setting SSL verify to true, because server is "
                                "not local", 1)
                    verifySSL = None
                chk = self.plx.CheckConnection(server, '',
                                               token=server.accesstoken,
                                               verifySSL=verifySSL)
                if chk == 504 and httpsUpdated is False:
                    # Not able to use HTTP, try HTTPs for now
                    server.scheme = 'https'
                    httpsUpdated = True
                    continue
                if chk == 401:
                    # Not yet authorized for Plex server
                    # Please sign in to plex.tv
                    dialog.ok(self.addonName,
                              string(39013) + server.name,
                              string(39014))
                    result = self.plx.PlexTvSignInWithPin()
                    if result:
                        plexLogin = result['username']
                        plexToken = result['token']
                        plexid = result['plexid']
                        
                        httpsUpdated = False
                    else:
                        # Exit while loop if user cancels
                        break
                # Problems connecting
                elif chk >= 400 or chk is False:
                    failedServer.append(server)
                    break
                # Otherwise: connection worked!
                else:
                    activeServer.append(server)
                    break
        if len(activeServer) == 0:
            # Enter Kodi settings instead
            xbmc.executebuiltin('Addon.OpenSettings(%s)' % self.addonId)
            return
        if len(failedServer) > 0:
            # Problems connecting to server. Pick another server?
            resp = dialog.yesno(self.addonName,
                                string(39015))
            # Exit while loop if user chooses No
            if not resp:
                return
        
        for server in activeServer:
            if not server.local:
                baseURL = server.baseURL.split(':')
                server.scheme = baseURL[0]
                server.ipaddress = baseURL[1].replace('//', '')
                server.port = baseURL[2]
                # User entered IP; we need to get the machineIdentifier
                if server.machineIdentifier == '':
                    machineIdentifier = GetMachineIdentifier(server)
                    if machineIdentifier is None:
                        server.machineIdentifier = ''
                    #TODO: find a better place for this
                    server.machineIdentifier = machineIdentifier
            # enforce https?
            # if scheme == 'https':
            #    utils.settings('https', 'true')
            #else:
            #    utils.settings('https', 'false')
            
        self.logMsg("Writing to Kodi user settings file", 0)
        # Write to Kodi settings file
        myStr = "|".join("%s" for server in activeServer)   
        utils.settings("activeserver", myStr)
        if forcePlexTV is True or chooseServer is True:
            return

        goToSettings = False
        # Direct paths (\\NAS\mymovie.mkv) or addon (http)?
        if dialog.yesno(heading=self.addonName,
                        line1=string(39027),
                        line2=string(39028),
                        nolabel="Addon (Default)",
                        yeslabel="Native (Direct Paths)"):
            self.logMsg("User opted to use direct paths.", 1)
            utils.settings('useDirectPaths', value="1")
            # Are you on a system where you would like to replace paths
            # \\NAS\mymovie.mkv with smb://NAS/mymovie.mkv? (e.g. Windows)
            if dialog.yesno(heading=self.addonName,
                            line1=string(39033)):
                self.logMsg("User chose to replace paths with smb", 1)
            else:
                utils.settings('replaceSMB', value="false")

            # complete replace all original Plex library paths with custom SMB
            if dialog.yesno(heading=self.addonName,
                            line1=string(39043)):
                self.logMsg("User chose custom smb paths", 1)
                utils.settings('remapSMB', value="true")
                # Please enter your custom smb paths in the settings under
                # "Sync Options" and then restart Kodi
                dialog.ok(heading=self.addonName,
                          line1=string(39044))
                goToSettings = True

            # Go to network credentials?
            if dialog.yesno(heading=self.addonName,
                            line1=string(39029),
                            line2=string(39030)):
                self.logMsg("Presenting network credentials dialog.", 1)
                utils.passwordsXML()
        # Disable Plex music?
        if dialog.yesno(heading=self.addonName,
                        line1=string(39016)):
            self.logMsg("User opted to disable Plex music library.", 1)
            utils.settings('enableMusic', value="false")
        else:
            utils.advancedSettingsXML()

        # Download additional art from FanArtTV
        if dialog.yesno(heading=self.addonName,
                        line1=string(39016)):
            self.logMsg("User opted to use FanArtTV", 1)
            utils.settings('FanartTV', value="true")

        if goToSettings is False:
            # Open Settings page now? You will need to restart!
            goToSettings = dialog.yesno(heading=self.addonName,
                                        line1=string(39017))
        if goToSettings:
            utils.window('emby_serverStatus', value="Stop")
            xbmc.executebuiltin(
                'Addon.OpenSettings(plugin.video.plexkodiconnect)')
        else:
            xbmc.executebuiltin('RestartApp')
        # We should always restart to ensure e.g. Kodi settings for Music
        # are in use!
