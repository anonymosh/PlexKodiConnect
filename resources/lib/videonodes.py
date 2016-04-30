# -*- coding: utf-8 -*-

###############################################################################

import shutil
import xml.etree.ElementTree as etree

import xbmc
import xbmcvfs

import utils

###############################################################################


@utils.logging
class VideoNodes(object):

    def __init__(self):
        self.kodiversion = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def commonRoot(self, order, label, tagname, roottype=1):

        if roottype == 0:
            # Index
            root = etree.Element('node', attrib={'order': "%s" % order})
        elif roottype == 1:
            # Filter
            root = etree.Element('node', attrib={'order': "%s" % order, 'type': "filter"})
            etree.SubElement(root, 'match').text = "all"
            # Add tag rule
            rule = etree.SubElement(root, 'rule', attrib={'field': "tag", 'operator': "is"})
            etree.SubElement(rule, 'value').text = tagname
        else:
            # Folder
            root = etree.Element('node', attrib={'order': "%s" % order, 'type': "folder"})

        etree.SubElement(root, 'label').text = label
        etree.SubElement(root, 'icon').text = "special://home/addons/plugin.video.plexkodiconnect/icon.png"

        return root

    def viewNode(self, indexnumber, tagname, mediatype, viewtype, viewid, delete=False):
        # Plex: reassign mediatype due to Kodi inner workings
        # How many items do we get at most?
        limit = "100"
        mediatypes = {
            'movie': 'movies',
            'show': 'tvshows',
            'photo': 'photos',
            'homevideo': 'homevideos',
            'musicvideos': 'musicvideos'
        }
        mediatype = mediatypes[mediatype]

        window = utils.window

        if viewtype == "mixed":
            dirname = "%s-%s" % (viewid, mediatype)
        else:
            dirname = viewid
        
        path = xbmc.translatePath("special://profile/library/video/").decode('utf-8')
        nodepath = xbmc.translatePath(
                    "special://profile/library/video/Plex-%s/" % dirname).decode('utf-8')

        # Verify the video directory
        # KODI BUG
        # Kodi caches the result of exists for directories
        #  so try creating a file
        if utils.IfExists(path) is False:
            shutil.copytree(
                src=xbmc.translatePath("special://xbmc/system/library/video").decode('utf-8'),
                dst=xbmc.translatePath("special://profile/library/video").decode('utf-8'))

        # Create the node directory
        if mediatype != "photo":
            if utils.IfExists(nodepath) is False:
                # folder does not exist yet
                self.logMsg('Creating folder %s' % nodepath, 1)
                xbmcvfs.mkdirs(nodepath.encode('utf-8'))
                if delete:
                    dirs, files = xbmcvfs.listdir(nodepath.encode('utf-8'))
                    for file in files:
                        xbmcvfs.delete(
                            (nodepath + file.decode('utf-8')).encode('utf-8'))

                    self.logMsg("Sucessfully removed videonode: %s."
                                % tagname, 1)
                    return

        # Create index entry
        nodeXML = "%sindex.xml" % nodepath
        # Set windows property
        path = "library://video/Plex-%s/" % dirname
        for i in range(1, indexnumber):
            # Verify to make sure we don't create duplicates
            if window('Emby.nodes.%s.index' % i) == path:
                return

        if mediatype == "photo":
            path = "plugin://plugin.video.plexkodiconnect/?id=%s&mode=getsubfolders" % indexnumber
            
        window('Emby.nodes.%s.index' % indexnumber, value=path)
        
        # Root
        if not mediatype == "photo":
            if viewtype == "mixed":
                specialtag = "%s-%s" % (tagname, mediatype)
                root = self.commonRoot(order=0, label=specialtag, tagname=tagname, roottype=0)
            else:
                root = self.commonRoot(order=0, label=tagname, tagname=tagname, roottype=0)
            try:
                utils.indent(root)
            except: pass
            etree.ElementTree(root).write(nodeXML)

        nodetypes = {

            '1': "all",
            '2': "recent",
            '3': "recentepisodes",
            '4': "inprogress",
            '5': "inprogressepisodes",
            '6': "unwatched",
            '7': "nextepisodes",
            '8': "sets",
            '9': "genres",
            '10': "random",
            '11': "recommended",
            '12': "ondeck"
        }
        mediatypes = {
            # label according to nodetype per mediatype
            'movies': 
                {
                '1': tagname,
                '2': 30174,
                # '4': 30177,
                # '6': 30189,
                '8': 39501,
                '9': 135,
                '10': 30227,
                '11': 30230,
                '12': 39500,
                },

            'tvshows': 
                {
                '1': tagname,
                # '2': 30170,
                '3': 30174,
                # '4': 30171,
                # '5': 30178,
                # '7': 30179,
                '9': 135,
                '10': 30227,
                # '11': 30230,
                '12': 39500,
                },
                
            'homevideos': 
                {
                '1': tagname,
                '2': 30251,
                '11': 30253
                },
                
            'photos': 
                {
                '1': tagname,
                '2': 30252,
                '8': 30255,
                '11': 30254
                },

            'musicvideos': 
                {
                '1': tagname,
                '2': 30256,
                '4': 30257,
                '6': 30258
                }
        }

        # Key: nodetypes, value: sort order in Kodi
        sortorder = {
            '1': '3',  # "all",
            '2': '2',  # "recent",
            '3': '2',  # "recentepisodes",
            # '4': # "inprogress",
            # '5': # "inprogressepisodes",
            # '6': # "unwatched",
            # '7': # "nextepisodes",
            '8': '7',  # "sets",
            '9': '6',  # "genres",
            '10': '8',  # "random",
            '11': '5',  # "recommended",
            '12': '1',  # "ondeck"
        }

        nodes = mediatypes[mediatype]
        for node in nodes:

            nodetype = nodetypes[node]
            nodeXML = "%s%s_%s.xml" % (nodepath, viewid, nodetype)
            # Get label
            stringid = nodes[node]
            if node != "1":
                label = utils.language(stringid)
                if not label:
                    label = xbmc.getLocalizedString(stringid)
            else:
                label = stringid

            # Set window properties
            if (mediatype == "homevideos" or mediatype == "photo") and nodetype == "all":
                # Custom query
                path = ("plugin://plugin.video.plexkodiconnect/?id=%s&mode=browsecontent&type=%s"
                        % (tagname, mediatype))
            elif (mediatype == "homevideos" or mediatype == "photo"):
                # Custom query
                path = ("plugin://plugin.video.plexkodiconnect/?id=%s&mode=browsecontent&type=%s&folderid=%s"
                        % (tagname, mediatype, nodetype))
            elif nodetype == "nextepisodes":
                # Custom query
                path = "plugin://plugin.video.plexkodiconnect/?id=%s&mode=nextup&limit=%s" % (tagname, limit)
            # elif kodiversion == 14 and nodetype == "recentepisodes":
            elif nodetype == "recentepisodes":
                # Custom query
                path = ("plugin://plugin.video.plexkodiconnect/?id=%s&mode=recentepisodes&type=%s&tagname=%s&limit=%s"
                    % (viewid, mediatype, tagname, limit))
            elif self.kodiversion == 14 and nodetype == "inprogressepisodes":
                # Custom query
                path = "plugin://plugin.video.plexkodiconnect/?id=%s&mode=inprogressepisodes&limit=%s" % (tagname, limit)
            elif nodetype == 'ondeck':
                # PLEX custom query
                if mediatype == "tvshows":
                    path = ("plugin://plugin.video.plexkodiconnect/?id=%s&mode=ondeck&type=%s&tagname=%s&limit=%s"
                        % (viewid, mediatype, tagname, limit))
                elif mediatype =="movies":
                    # Reset nodetype; we got the label
                    nodetype = 'inprogress'
            else:
                path = "library://video/Plex-%s/%s_%s.xml" % (dirname, viewid, nodetype)
            
            if mediatype == "photo":
                windowpath = "ActivateWindow(Pictures,%s,return)" % path
            else:
                windowpath = "ActivateWindow(Video,%s,return)" % path
            
            if nodetype == "all":

                if viewtype == "mixed":
                    templabel = "%s-%s" % (tagname, mediatype)
                else:
                    templabel = label

                embynode = "Emby.nodes.%s" % indexnumber
                window('%s.title' % embynode, value=templabel)
                window('%s.path' % embynode, value=windowpath)
                window('%s.content' % embynode, value=path)
                window('%s.type' % embynode, value=mediatype)
            else:
                embynode = "Emby.nodes.%s.%s" % (indexnumber, nodetype)
                window('%s.title' % embynode, value=label)
                window('%s.path' % embynode, value=windowpath)
                window('%s.content' % embynode, value=path)

            if mediatype == "photo":
                # For photos, we do not create a node in videos but we do want the window props
                # to be created.
                # To do: add our photos nodes to kodi picture sources somehow
                continue
            
            if xbmcvfs.exists(nodeXML.encode('utf-8')):
                # Don't recreate xml if already exists
                continue

            # Create the root
            if (nodetype in ("nextepisodes", "ondeck", 'recentepisodes') or mediatype == "homevideos"):
                # Folder type with plugin path
                root = self.commonRoot(order=sortorder[node], label=label, tagname=tagname, roottype=2)
                etree.SubElement(root, 'path').text = path
                etree.SubElement(root, 'content').text = "episodes"
            else:
                root = self.commonRoot(order=sortorder[node], label=label, tagname=tagname)
                if nodetype in ('recentepisodes', 'inprogressepisodes'):
                    etree.SubElement(root, 'content').text = "episodes"
                else:
                    etree.SubElement(root, 'content').text = mediatype

                # Elements per nodetype
                if nodetype == "all":
                    etree.SubElement(root, 'order', {'direction': "ascending"}).text = "sorttitle"
                
                elif nodetype == "recent":
                    etree.SubElement(root, 'order', {'direction': "descending"}).text = "dateadded"
                    etree.SubElement(root, 'limit').text = limit
                    rule = etree.SubElement(root, 'rule', {'field': "playcount", 'operator': "is"})
                    etree.SubElement(rule, 'value').text = "0"
                
                elif nodetype == "inprogress":
                    etree.SubElement(root, 'rule', {'field': "inprogress", 'operator': "true"})
                    etree.SubElement(root, 'limit').text = limit
                    etree.SubElement(
                        root,
                        'order',
                        {'direction': 'descending'}
                    ).text = 'lastplayed'

                elif nodetype == "genres":
                    etree.SubElement(root, 'order', {'direction': "ascending"}).text = "sorttitle"
                    etree.SubElement(root, 'group').text = "genres"
                
                elif nodetype == "unwatched":
                    etree.SubElement(root, 'order', {'direction': "ascending"}).text = "sorttitle"
                    rule = etree.SubElement(root, "rule", {'field': "playcount", 'operator': "is"})
                    etree.SubElement(rule, 'value').text = "0"

                elif nodetype == "sets":
                    etree.SubElement(root, 'order', {'direction': "ascending"}).text = "sorttitle"
                    etree.SubElement(root, 'group').text = "tags"

                elif nodetype == "random":
                    etree.SubElement(root, 'order', {'direction': "ascending"}).text = "random"
                    etree.SubElement(root, 'limit').text = limit

                elif nodetype == "recommended":
                    etree.SubElement(root, 'order', {'direction': "descending"}).text = "rating"
                    etree.SubElement(root, 'limit').text = limit
                    rule = etree.SubElement(root, 'rule', {'field': "playcount", 'operator': "is"})
                    etree.SubElement(rule, 'value').text = "0"
                    rule2 = etree.SubElement(root, 'rule',
                        attrib={'field': "rating", 'operator': "greaterthan"})
                    etree.SubElement(rule2, 'value').text = "7"

                elif nodetype == "recentepisodes":
                    # Kodi Isengard, Jarvis
                    etree.SubElement(root, 'order', {'direction': "descending"}).text = "dateadded"
                    etree.SubElement(root, 'limit').text = limit
                    rule = etree.SubElement(root, 'rule', {'field': "playcount", 'operator': "is"})
                    etree.SubElement(rule, 'value').text = "0"

                elif nodetype == "inprogressepisodes":
                    # Kodi Isengard, Jarvis
                    etree.SubElement(root, 'limit').text = limit
                    rule = etree.SubElement(root, 'rule',
                        attrib={'field': "inprogress", 'operator':"true"})

            try:
                utils.indent(root)
            except: pass
            etree.ElementTree(root).write(nodeXML)

    def singleNode(self, indexnumber, tagname, mediatype, itemtype):

        window = utils.window

        tagname = tagname.encode('utf-8')
        cleantagname = utils.normalize_nodes(tagname)
        nodepath = xbmc.translatePath("special://profile/library/video/").decode('utf-8')
        nodeXML = "%splex_%s.xml" % (nodepath, cleantagname)
        path = "library://video/plex_%s.xml" % cleantagname
        windowpath = "ActivateWindow(Video,%s,return)" % path
        
        # Create the video node directory
        if not xbmcvfs.exists(nodepath):
            # We need to copy over the default items
            shutil.copytree(
                src=xbmc.translatePath("special://xbmc/system/library/video").decode('utf-8'),
                dst=xbmc.translatePath("special://profile/library/video").decode('utf-8'))
            xbmcvfs.exists(path)

        labels = {

            'Favorite movies': 30180,
            'Favorite tvshows': 30181,
            'channels': 30173
        }
        label = utils.language(labels[tagname])
        embynode = "Emby.nodes.%s" % indexnumber
        window('%s.title' % embynode, value=label)
        window('%s.path' % embynode, value=windowpath)
        window('%s.content' % embynode, value=path)
        window('%s.type' % embynode, value=itemtype)

        if xbmcvfs.exists(nodeXML):
            # Don't recreate xml if already exists
            return

        if itemtype == "channels":
            root = self.commonRoot(order=1, label=label, tagname=tagname, roottype=2)
            etree.SubElement(root, 'path').text = "plugin://plugin.video.plexkodiconnect/?id=0&mode=channels"
        else:
            root = self.commonRoot(order=1, label=label, tagname=tagname)
            etree.SubElement(root, 'order', {'direction': "ascending"}).text = "sorttitle"

        etree.SubElement(root, 'content').text = mediatype

        try:
            utils.indent(root)
        except: pass
        etree.ElementTree(root).write(nodeXML)

    def clearProperties(self):

        window = utils.window

        self.logMsg("Clearing nodes properties.", 1)
        embyprops = window('Emby.nodes.total')
        propnames = [
        
            "index","path","title","content",
            "inprogress.content","inprogress.title",
            "inprogress.content","inprogress.path",
            "nextepisodes.title","nextepisodes.content",
            "nextepisodes.path","unwatched.title",
            "unwatched.content","unwatched.path",
            "recent.title","recent.content","recent.path",
            "recentepisodes.title","recentepisodes.content",
            "recentepisodes.path","inprogressepisodes.title",
            "inprogressepisodes.content","inprogressepisodes.path"
        ]

        if embyprops:
            totalnodes = int(embyprops)
            for i in range(totalnodes):
                for prop in propnames:
                    window('Emby.nodes.%s.%s' % (str(i), prop), clear=True)