import sys
import inkex
import os.path
import subprocess
import threading
import tempfile
import os
import re
import gettext


# Setup the gettext function
_ = gettext.gettext
# These lines are only needed if you don't put the script directly into the installation directory
# Unix
sys.path.append('/usr/share/inkscape/extensions')
# OS X
sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
# Windows
sys.path.append(r'C:\Program Files\Inkscape\share\extensions')


def propStrToDict(inStr):
    dictio = {}

    for prop in inStr.split(";"):
        values = prop.split(":")

        if (len(values) == 2):
            dictio[values[0].strip()] = values[1].strip()

    return dictio


def dictToPropStr(dictio):
    str = ""

    for key in dictio.keys():
        str += " " + key + ":" + dictio[key] + ";"

    return str[1:]


def setStyle(node, propKey, propValue):
    props = {}

    if "style" in node.attrib:
        props = propStrToDict(node.get("style"))

    props[propKey] = propValue
    node.set("style", dictToPropStr(props))


class PopenThread(threading.Thread):
    def __init__(self, param):
        threading.Thread.__init__(self)
        self.param = param

    def run(self):
        proc = subprocess.Popen(self.param, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_value, stderr_value = proc.communicate()


class MyEffect(inkex.Effect):
    inkscapeCommand = None

    def __init__(self):
        inkex.Effect.__init__(self)

        self.OptionParser.add_option("--desc")
        self.OptionParser.add_option("--folderpath",
                                     action="store", type="string",
                                     dest="folderpath", default=None,
                                     help="")
        self.OptionParser.add_option("--mapview",
                                     action="store", type="inkbool",
                                     dest="handle_mapview", default=True,
                                     help="")
        self.OptionParser.add_option("--height",
                                     action="store", type="inkbool",
                                     dest="handle_height", default=True,
                                     help="")
        self.OptionParser.add_option("--splats",
                                     action="store", type="inkbool",
                                     dest="handle_splats", default=True,
                                     help="")

        # Set inkscape command.
        self.inkscapeCommand = self.findInkscapeCommand()

        if not self.inkscapeCommand:
            inkex.errormsg(_("Could not find Inkscape command.\n"))
            sys.exit(1)

    def output(self):
        pass

    def effect(self):
        # Find layers.
        exportNodes = self.document.xpath("//svg:g[@inkscape:groupmode='layer']", namespaces=inkex.NSS)

        if len(exportNodes) < 1:
            sys.stderr.write("No layers found.")

        for node in exportNodes:
            setStyle(node, "display", "none")

        # export terrain alpha splat and height maps one by one
        for node in exportNodes:
            label = node.attrib["{" + inkex.NSS["inkscape"] + "}label"]

            if ((self.options.handle_splats and (label == "asphalt")) or
                    (self.options.handle_splats and (label == "road")) or
                    (self.options.handle_splats and (label == "grass")) or
                    (self.options.handle_splats and (label == "sand")) or
                    (self.options.handle_height and (label == "height")) or
                    (self.options.handle_splats and label.startswith("alpha_"))):

                setStyle(node, "display", "inherit")
                setStyle(node, "opacity", "1")
                self.takeSnapshot(label)
                setStyle(node, "display", "none")

        # export tab-map image
        if (self.options.handle_mapview):
            for node in exportNodes:
                label = node.attrib["{" + inkex.NSS["inkscape"] + "}label"]

                # include these layers only
                if ((label == "objects") or
                        (label == "walls") or
                        (label == "rocks") or
                        (label.startswith("layer"))):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view")

            # take woods separately
            for node in exportNodes:
                label = node.attrib["{" + inkex.NSS["inkscape"] + "}label"]

                # include these layers only
                if ((label.startswith("woods_")) or (label.startswith("layer"))):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_woods")

            # map view decoration layer
            for node in exportNodes:
                label = node.attrib["{" + inkex.NSS["inkscape"] + "}label"]

                # include these layers only
                if (label == "map_view_decoration"):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_decoration")

            # map view bases layer
            for node in exportNodes:
                label = node.attrib["{" + inkex.NSS["inkscape"] + "}label"]

                # include these layers only
                if (label == "map_view_bases"):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_bases")

    # Function to export the current state of the file using Inkscape.
    def takeSnapshot(self, fileName):
        path = self.options.folderpath + "/"

        # Write the svg file.
        svgFileDesc, svgFile = tempfile.mkstemp(suffix=".svg", prefix="_rwr_")
        self.document.write(os.fdopen(svgFileDesc, "wb"))

        ext = "png"
        outFile = path + "_rwr_" + fileName + "." + ext
        PopenThread(self.inkscapeCommand + " --file=" + svgFile + " --without-gui --export-area-page --export-" + ext
                    + "=" + outFile).start()

    # Function to try and find the correct command to invoke Inkscape.
    def findInkscapeCommand(self):
        commands = []
        commands.append("inkscape")
        commands.append(r"C:\Program Files\Inkscape\inkscape.exe")
        commands.append("/Applications/Inkscape.app/Contents/Resources/bin/inkscape")

        for command in commands:
            proc = subprocess.Popen(command + " --without-gui --version", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_value, stderr_value = proc.communicate()

            if proc.returncode == 0:
                return command

        return None


e = MyEffect()
e.affect()
