import os
import subprocess
import sys
import tempfile
import threading

import inkex


# Setup some constants
INKSCAPE_LABEL = f"{{{inkex.NSS['inkscape']}}}label"
TERRAIN_LAYERS = ["height", "asphalt", "road", "grass", "sand"]
MAPVIEW_LAYERS = ["objects", "walls", "rocks"]


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

        # Export height and terrain alpha splat maps
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]
            if label in TERRAIN_LAYERS or label.startswith("alpha_"):
                setStyle(node, "display", "inherit")
                setStyle(node, "opacity", "1")
                self.takeSnapshot(label)
                setStyle(node, "display", "none")

        # Export map_view
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]
            # Layers, such as walls, are in sub-layers - we must display the parent layers that start with "layer"
            if label.startswith("layer") or label in MAPVIEW_LAYERS:
                setStyle(node, "display", "inherit")
            else:
                setStyle(node, "display", "none")

        self.takeSnapshot("map_view")

        # Export map_view_woods
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]
            if label.startswith("layer") or label.startswith("woods_"):
                setStyle(node, "display", "inherit")
            else:
                setStyle(node, "display", "none")

        self.takeSnapshot("map_view_woods")

        # Export map_view_decoration layer
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]
            if label == "map_view_decoration":
                setStyle(node, "display", "inherit")
            else:
                setStyle(node, "display", "none")

        self.takeSnapshot("map_view_decoration")

        # Export map_view_bases layer
        for node in exportNodes:
            label = node.attrib[INKSCAPE_LABEL]
            if label == "map_view_bases":
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
