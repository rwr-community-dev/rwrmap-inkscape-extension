import gettext
import os
import subprocess
import sys
import tempfile
import threading

import inkex


# Setup some constants
INKSCAPE_LABEL = f"{{{inkex.NSS['inkscape']}}}label"
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
        # inkex.errormsg(stderr_value)


class MyEffect(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

        self.arg_parser.add_argument("--desc")
        self.arg_parser.add_argument("--folderpath", type=str, dest="folderpath", default=None, help="")
        self.arg_parser.add_argument("--mapview", type=inkex.Boolean, dest="handle_mapview", default=True, help="")
        self.arg_parser.add_argument("--height", type=inkex.Boolean, dest="handle_height", default=True, help="")
        self.arg_parser.add_argument("--splats", type=inkex.Boolean, dest="handle_splats", default=True, help="")

    def output(self):
        pass

    def effect(self):
        # Find layers.
        exportNodes = self.document.xpath("//svg:g[@inkscape:groupmode='layer']", namespaces=inkex.NSS)

        # If there are no layers, write an error message for display by Inkscape and exit fast
        if len(exportNodes) < 1:
            inkex.errormsg("Error: No layers found")
            sys.exit()

        # DEBUG: log object info via an errormsg
        # inkex.errormsg(exportNodes[0].attrib)

        # Set all nodes to 'display: none' so that specific nodes can be made visible per export
        for node in exportNodes:
            setStyle(node, "display", "none")

        # export terrain alpha splat and height maps one by one
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]

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
                label = node.attrib[INKSCAPE_LABEL]

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
                label = node.attrib[INKSCAPE_LABEL]

                # include these layers only
                if ((label.startswith("woods_")) or (label.startswith("layer"))):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_woods")

            # map view decoration layer
            for node in exportNodes:
                label = node.attrib[INKSCAPE_LABEL]

                # include these layers only
                if (label == "map_view_decoration"):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_decoration")

            # map view bases layer
            for node in exportNodes:
                label = node.attrib[INKSCAPE_LABEL]

                # include these layers only
                if (label == "map_view_bases"):
                    setStyle(node, "display", "inherit")
                else:
                    setStyle(node, "display", "none")

            self.takeSnapshot("map_view_bases")

    # Function to export the current state of the file using Inkscape.
    def takeSnapshot(self, name):
        # Write the svg file.
        svg_fd, svg_f = tempfile.mkstemp(suffix=".svg", prefix="_rwr_")
        fhl = os.fdopen(svg_fd, "wb")
        self.document.write(fhl)
        # Make sure to close the file handle after writing the file
        fhl.close()

        export_name = f"{self.options.folderpath}/_rwr_{name}.png"
        export_command = f"inkscape --export-area-page --export-filename=\"{export_name}\" \"{svg_f}\""
        # inkex.errormsg(f"Running: {export_command}")
        PopenThread(export_command).start()


e = MyEffect()
e.run()
