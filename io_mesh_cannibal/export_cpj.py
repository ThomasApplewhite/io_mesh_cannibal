# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------------------------
import struct
import ctypes
import colorsys
import random

from os.path import exists as os_exists
from os.path import getsize as os_getsize # might not need this
from os import remove as os_remove

import bpy
import bmesh

# look for !!!ASSUME for places where I'm guessing lol

# ----------------------------------------------------------------------------
CPJ_HDR_RIFF_MAGIC = struct.unpack("I", b"RIFF")[0]
CPJ_HDR_FORM_MAGIC = struct.unpack("I", b"CPJB")[0]

# 0 for Magic number, 1 for Version, 2 for function
chunkDataDict = {
        0 : ["MACB", 1, chunk_mac],
        1 : ["GEOB", 1, chunk_geo],
        2 : ["SRFB", 1, chunk_srf],
        3 : ["LODB", 3, chunk_lod],
        4 : ["SKLB", 1, chunk_skl],
        5 : ["FRMB". 1, chunk_frm],
        6 : ["SEQB", 1, chunk_seq]
}

startingChunkNames = {
    0 : [""],
    1 : [""],
    2 : [""],
    3 : [""],
    4 : [""],
    5 : [""],
    6 : [""]
}

chunkNames = startingChunkNames

chunkImplemented = {
        "MACB" : True,
        "GEOB" : False,
        "SRFB" : False,
        "LODB" : False,
        "SKLB" : False,
        "FRMB" : False,
        "SEQB" : False
}

# ----------------------------------------------------------------------------
def save(context, filepath):

    # info
    print("Writing to %s..." % filepath)

    # might wanna do space check here, we need twice the output size of the
    # file to export rn

    if os_exists(filepath):
        # standard "Overwrite file?" prompt here
        pass

    # open temporary file to write non-header data
    temppath = filepath + ".tmp"
    if os_exists(temppath):
        # recovery logic? or just warn of overrite?
        pass

    # reset chunk names, just in case
    chunkNames = startingChunkNames

    # write data into chunks
    with open(temppath, mode="ab") as handle:
        # erase present data
        handle.truncate(0)

        # compatibility flags
        bl_object = None
        has_surface_already = False

        # Write one of each chunk type
        for loop in range(6):

            output_array = make_chunk(chunkIndex)
            # data manipulation here
            # if no chunk is created, don't write anything
            if output_array != False:
                handle.write(output_array)

        # after all chunks are processed, add the autoexec MAC
        output_array = create_autoexec_mac()
        handle.write(output_array)
    # Chunk order is irrelivant, I write them
    # to file in MAC->GEO->SRF->LOD->SKL->FRM->SEQ order,
    # with the autoexec chunk at the end
    # ----------

    # write to destination file
    with open(filepath, "ab") as destinationHandle:
        # first write header
        dataArray = bytearray()

        # get tempfile size for header
        # !!!ASSUME
        # not sure if this produces the same value as len(data) from
        # reading, will check later. Point is we need data size for header
        dataSize = os_getsize(temppath)

        # unsigned long riffMagic; // CPJ_HDR_RIFF_MAGIC
        # unsigned long lenFile; // length of file following this value
        # unsigned long formMagic; // CPJ_HDR_FORM_MAGIC
        struct.pack_into("III", dataArray, CPJ_HDR_RIFF_MAGIC, 
                dataSize, CPJ_HDR_FORM_MAGIC)

        # write header
        destinationHandle.write(dataArray)

        # then write temp file to destination file
        with open (temppath, "rb") as dataHandle:
            print("Writing to Destination File")
            for line in dataHandle:
                # I !!!ASSSUME that because there shouldn't be any newlines
                # in the tempfile, then the for->in version of getline
                # (which doesn't have a byte limit) will load the entire file
                # into memory at once. That's no good.
                destinationHandle.write(line)

        
        # ensure destination file integrity maybe

    # delete temp file
    os_remove(temppath)
            
    return {'FINISHED'}


# ----------------------------------------------------------------------------
# returns a byte array containing one chunk's worth of data
def make_chunk(chunkIndex):
    # 0 for Magic Number, 1 for Chunk version, 2 for Creation function
    # chunk creation goes outside so the name can be
    # properly initialized
    createdChunk = chunkDataDict[chunkIndex][2]()
    if createdChunk == False:
        return False

    return format_data(
            chunkDataDict[chunkIndex][0],
            chunkDataDict[chunkIndex][1],
            chunkNames[chunkIndex][0],
            createdChunk
    )

# ----------------------------------------------------------------------------
def format_data(chunkMagicNumber, chunkVersion, chunkName, data):
    # Every chunk needs to have a chunk header that follows the following
    # conventions found on line 29

    # The header looks like this:
    #struct SCpjChunkHeader
    #unsigned long magic; // chunk-specific magic marker
    #unsigned long lenFile; // length of chunk following this value
    #unsigned long version; // chunk-specific format version
    #unsigned long timeStamp; // time stamp of chunk creation
    #unsigned long ofsName; // offset of chunk name string from start of chunk
    #                      // If this value is zero, the chunk is nameless

    # Additionally, the chunk must have an extra byte added to it (WITHOUT
    # INCLUDING IT IN LENFILE) to make the chunk be RIFF compliant

    headerData = bytearray()

    struct.pack_int(
            "IIIII",
            headerData,     
            chunkMagicNumber
            len(data)        # !!!ASSUME we don't need to count header
            chunkVersion,
            0,               # Because chunks have no meaningful equivelant
                                # in blender, this will be defined as the
                                # the time of export. However, idk how 
                                # times are formatted in Cannibal longs,
                                # so for now it's zero.
            len(chunkName)   # Len of name I !!!ASSUME
                                #  Legally it's the offset of 
                                # the chunk name string from 
                                # the start of the chunk, which I !!!ASSUME
                                # is functionally equivilant here
                                # If chunk is nameless, this should be 0
    )

    headerData.append(chunkName)
    headerData.append(data)

    # not super efficient but whatever
    # If not even chunk size...
    if len(headerData) % 2 != 0:
        # append empty byte for RIFF compatability
        headerData.append(b'\0')

    return headerData



# ----------------------------------------------------------------------------
def chunk_mac():
    print("Cannibal Model Actor Configuration Chunk (MAC)")
    print("Custom MAC export not supported")

    return False

    # MACs have no functional eqivelant in Blender, since MACs are sensitive
    # to the install path of the Cannibal Editor itself.  Extensions for MACs
    # outside the 'autoexec' MAC probably need further blender addons. Thus,
    # all MACs other than the autoexec MAC will be skipped.

    # just remember that MAC chunks go
    # chunk header -> MAC header -> section headers -> commands
    # and that commands need to have a null terminator


def create_autoexec_mac():
    sectionData = bytearray()
    sectionHeader = bytearray()

    # The 0 is the index of the first command. Not sure
    # what it does for us, since it doesn't directly point to a byte
    # in data. But that's fine, I can set it to something useful later.
    struct.pack_into("III", sectionHeader, "autoexec\0", 11, 0)
    

    # And now we literally just append every command to the data.
    # encode encodes to ASCII by default

    # name and description
    auth_name = f"SetAuthor(\"{""}\")\0" # find .blend file author
    desc = f"SetDescription(\"{""}\")\0" # fund .blend file desc
    sectionData += auth_name.encode()
    sectionData += desc.encode()

    # default transform values
    # it seems world transforms are readonly in blender, so I can just
    # hardcode these to the defaults at line 213-218 of the cpj spec
    origin = f"SetOrigin({0}, {0}, {0})\0"
    scale = f"SetScale({1}, {1}, {1})\0"
    rot = f"SetRotation({0}, {0}, {0})\0"
    sectionData += origin.encode()
    sectionData += origin.encode()
    sectionData += origin.encode()

    # default chunks
    # these are funky for a few reasons:
    # 1: the chunk paths are relative to ???, where as their names
    # depend on ??
    # 2: with the exception of the geometry chunk, they might not
    # even be there. For now, that will be handled by adding an
    # empty file path

    # so, where do I want to get these file paths...?
    # Because the exporter works within the scope of the 
    # the cannibal file itself, the names of each chunk
    # is a sufficient file path

    if(chunkImplemented["GEOB"]):
        geo = f"SetGeometry(\"{chunkNames[1]}\")\0"
        sectionData += geo.encode()
    else:
        raise ExportError("Cannibal file must have at least 1 Geometry Chunk")

    # The number is represents what kind of surface this chunk is: 0 for
    # primary, any positive number for decals. Right now, we only support
    # primaries.
    srf = f"SetSurface({0}, \"{chunkNames[2]}\")\0"
            if chunkImplemented["SRFB"] else "SetSurface(0, \"\")\0"

    lod = f"SetLodData(\"{chunkName[3]}\")\0"
            if chunkImplemented["LODB"] else "SetLodData(\"\")\0"

    skl = f"SetSkeleton(\"{chunkNames[4]}\")\0"
            if chunkImplemented["SKLB"] else "SetSkeleton(\"\")\0"

    # This could also point to a completely seperate Cannibal project.
    # Maybe support for that should be added
    # NULL will point to a config project in Cannibal itself
    frm = f"AddFrames(\"{chunkNames[5]}\")\0"
            if chunkImplemented["FRMB"] else "AddFrames(\"NULL\")\0"

    # This could also point to a completely seperate Cannibal project.
    # Maybe support for that should be added
    # NULL will point to a config project in Cannibal itself
    seq = f"AddSequences(\"{chunkNames[6]}\")\0"
            if chunkImplemented["SEQB"] else "AddSequences(\"NULL\")\0"

    # then append literally all of them
    sectionData += srf.encode()
    sectionData += lod.encode()
    sectionData += skl.encode()
    sectionData += frm.encode()
    sectionData += seq.encode()

    # then we need the MAC header
    chunkHeader = bytearray()
    onlyAutoexec = True
    if(onlyAutoexec):
        struct.pack_into(
                "IIII", 
                mac_header, 
                1,  # only one section, autoexec 
                0,  # if offset is beginning, this is 0. If it's end, it's 12
                autoexecCommandCount, 
                12  # only one section means the commands start 12 bytes after
                    # the sections
                    # if offset is beginning, this is 12. If it's end, it's
                    # len(autoexecData)
    )

    
    # finally, the chunk header itself
    newData = chunkHeader + sectionHeader + sectionData
    return format_data(chunkDataDict[0][0], chunkDataDict[0][1], "autoexec", newData)

    
# ----------------------------------------------------------------------------
def chunk_geo(context):
    # !!!ASSUME
    # not an assumption but make sure to error multiple geo blocks
    # (that is, error if there are multiple blender objects)
    print("Geometry Chunk (GEO)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


    geoArray = bytearray()
    geoBuffer = bytearray()

    # unsigned long numVertices; // number of vertices
    # unsigned long ofsVertices; // offset of vertices in data block
    # unsigned long numEdges; // number of edges
    # unsigned long ofsEdges; // offset of edges in data block
    # unsigned long numTris; // number of triangles
    # unsigned long ofsTris; // offset of triangles in data block
    # unsigned long numMounts; // number of mounts
    # unsigned long ofsMounts; // offset of mounts in data block
    # unsigned long numObjLinks; // number of object links
    # unsigned long ofsObjLinks; // number of object links in data
    SGeoHeader = struct.pack("IIIIIIIIII", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,)

    # get object from blender in workable way
    objectCount = len(bpy.context.collection.all_objects.values)
    if objectCount != 1:
        raise ExportError("Multiple geometry objects are not supported")

    object = bpy.context.object
    if not object:
        raise ExportError("No geometry object found")

    if object.type != "MESH":
        raise ExportError("Object is not mesh/geometry")

    # alright time to actually have data
    verts = object.data.verticies
    faces = object.data.polygons # might not be triangles?
    edges = # derived? not in the actuall data?

    # need to get verts, tris, and edges

    # verts are easy I suppose
    vertcount = 0
    
    for vertex in object.data.verticies:
        geoBuffer.clear()

        # unsigned char flags; // GEOVF_ vertex flags
        # unsigned char groupIndex; // group index for vertex frame compression
        # unsigned short reserved; // reserved for future use, must be zero
        # unsigned short numEdgeLinks; // number of edges linked to this vertex
        # unsigned short numTriLinks; // number of triangles linked to this vertex
        # unsigned long firstEdgeLink; // first edge index in object link array
        # unsigned long firstTriLink; // first triangle index in object link array
        # CPJVECTOR refPosition; // reference position of vertex
        SGeoVert = struct.pack("BBHHHIIfff")
        SGeoVert[0] = 0  # !!!ASSUME has no equivilent in blender
        SGeoVert[1] = ?? # might have a blender equiveland
        SGeoVert[2] = 0  # by definition, see above
        SGeoVert[3] = ??
        SGeoVert[4] = ??
        SGeoVert[5] = ??
        SGeoVert[6] = ??
        SGeoVert[7] = vertex.co[0] # x
        SGeoVert[8] = vertex.co[2] # z
        SGeoVert[9] = vertex.co[1] # y

        SGeoVert.unpack(geoBuffer)
        geoArray += geoBuffer

        vertcount += 1
    
    SGeoHeader[0] = vertcount
    SGeoHeader[1] = # still don't know what offset should be
        

    # read all verticies
    # numVerts is number of verticies, dug
    # ofsVerts is the offset of the verticies with I
    # !!!ASSUME is the location of the vertex subchunk in the data file
    # Still need to deduce what that location is

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(cpj_verts, [], bl_faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    return obj

    # unsigned long numVertices; // number of vertices
    # unsigned long ofsVertices; // offset of vertices in data block
    # unsigned long numEdges; // number of edges
    # unsigned long ofsEdges; // offset of edges in data block
    # unsigned long numTris; // number of triangles
    # unsigned long ofsTris; // offset of triangles in data block
    # unsigned long numMounts; // number of mounts
    # unsigned long ofsMounts; // offset of mounts in data block
    # unsigned long numObjLinks; // number of object links
    # unsigned long ofsObjLinks; // number of object links in data
    SGeoFile = struct.unpack_from("IIIIIIIIII", data, idx + 20)

    print("- '%s'" % name)
    print("- %d Vertices" % SGeoFile[0])
    print("- %d Edges" % SGeoFile[2])
    print("- %d Tris" % SGeoFile[4])
    print("- %d Mounts" % SGeoFile[6])
    print("- %d ObjLinks" % SGeoFile[8])

    cpj_verts = []
    cpj_edges = []
    cpj_tris = []

    # read all vertices
    shift = idx + 20 + 40 + SGeoFile[1]
    for i in range(SGeoFile[0]):

        # unsigned char flags; // GEOVF_ vertex flags
        # unsigned char groupIndex; // group index for vertex frame compression
        # unsigned short reserved; // reserved for future use, must be zero
        # unsigned short numEdgeLinks; // number of edges linked to this vertex
        # unsigned short numTriLinks; // number of triangles linked to this vertex
        # unsigned long firstEdgeLink; // first edge index in object link array
        # unsigned long firstTriLink; // first triangle index in object link array
        # CPJVECTOR refPosition; // reference position of vertex
        SGeoVert = struct.unpack_from("BBHHHIIfff", data, shift)

        cpj_verts.append((SGeoVert[7], SGeoVert[9], SGeoVert[8]))  # X Z Y
        shift += 28

    # read all edges
    shift = idx + 20 + 40 + SGeoFile[3]
    for i in range(SGeoFile[2]):

        # unsigned short headVertex; // vertex list index of edge's head vertex
        # unsigned short tailVertex; // vertex list index of edge's tail vertex
        # unsigned short invertedEdge; // edge list index of inverted mirror edge
        # unsigned short numTriLinks; // number of triangles linked to this edge
        # unsigned long firstTriLink; // first triangle index in object link array
        SGeoEdge = struct.unpack_from("HHHHI", data, shift)

        cpj_edges.append((SGeoEdge[0], SGeoEdge[1]))
        shift += 12

    # read all triangles
    shift = idx + 20 + 40 + SGeoFile[5]
    for i in range(SGeoFile[4]):

        # unsigned short edgeRing[3]; // edge list indices used by triangle, whose
        #                             // tail vertices are V0, V1, and V2, in order
        # unsigned short reserved; // reserved for future use, must be zero
        SGeoTri = struct.unpack_from("HHHH", data, shift)

        cpj_tris.append((SGeoTri[0], SGeoTri[1], SGeoTri[2]))
        shift += 8

    # create list of mesh faces
    bl_faces = []
    for tris in cpj_tris:
        v0 = cpj_edges[tris[0]][1]
        v1 = cpj_edges[tris[1]][1]
        v2 = cpj_edges[tris[2]][1]
        bl_faces.append((v0, v1, v2))

    # create mesh and object
    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(cpj_verts, [], bl_faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    return obj


# ----------------------------------------------------------------------------
def chunk_srf(data, idx, name, bl_object):
    print("Surface Chunk (SRF)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


    print("Surface Chunk (SRF)")

    # unsigned long numTextures; // number of textures
    # unsigned long ofsTextures; // offset of textures in data block
    # unsigned long numTris; // number of triangles
    # unsigned long ofsTris; // offset of triangles in data block
    # unsigned long numUV; // number of UV texture coordinates
    # unsigned long ofsUV; // offset of UV texture coordinates in data block
    SSrfFile = struct.unpack_from("IIIIII", data, idx + 20)

    print("- '%s'" % name)
    print("- %d numTextures" % SSrfFile[0])
    print("- %d numTris" % SSrfFile[2])
    print("- %d numUV" % SSrfFile[4])

    # create new empty UV layer
    bl_uv_layer = bl_object.data.uv_layers.new(name=name, do_init=False)

    # init bmesh with object mesh
    bm = bmesh.new()
    bm.from_mesh(bl_object.data)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv[0]

    # check consistency
    if SSrfFile[2] != len(bm.faces):
        raise ImportError("Different number of mesh faces in GEO and SRF")

    # offset
    block = idx + 20 + 24

    # read textures
    shift = block + SSrfFile[1]
    for i in range(SSrfFile[0]):

        # unsigned long ofsName; // offset of texture name string in data block
        # unsigned long ofsRefName; // offset of optional reference name in block
        SSrfTex = struct.unpack_from("II", data, shift)

        label = ctypes.create_string_buffer(
            data[block + SSrfTex[0]:]).value.decode()
        if SSrfTex[1]:
            label += "___" + ctypes.create_string_buffer(
                data[block + SSrfTex[1]:]).value.decode()

        # make new texture with random colors
        col = colorsys.hls_to_rgb(random.random(), 0.6, 0.8)
        mat = bpy.data.materials.new(name=label)
        mat.diffuse_color = (col[0], col[1], col[2], 1.0)
        bl_object.data.materials.append(mat)

        shift += 8

    # read triangles
    shift = block + SSrfFile[3]
    for i in range(SSrfFile[2]):

        # unsigned short uvIndex[3]; // UV texture coordinate indices used
        # unsigned char texIndex; // surface texture index
        # unsigned char reserved; // reserved for future use, must be zero
        # unsigned long flags; // SRFTF_ triangle flags
        # unsigned char smoothGroup; // light smoothing group
        # unsigned char alphaLevel; // transparent/modulated alpha level
        # unsigned char glazeTexIndex; // second-pass glaze texture index if used
        # unsigned char glazeFunc; // ESrfGlaze second-pass glaze function
        SSrfTri = struct.unpack_from("HHHBBIBBBB", data, shift)

        # set UVs
        uv0 = struct.unpack_from(
            "ff", data, block + SSrfFile[5] + SSrfTri[0] * 8)
        uv1 = struct.unpack_from(
            "ff", data, block + SSrfFile[5] + SSrfTri[1] * 8)
        uv2 = struct.unpack_from(
            "ff", data, block + SSrfFile[5] + SSrfTri[2] * 8)
        bm.faces[i].loops[0][uv].uv = (uv0[0], 1.0 - uv0[1])
        bm.faces[i].loops[1][uv].uv = (uv1[0], 1.0 - uv1[1])
        bm.faces[i].loops[2][uv].uv = (uv2[0], 1.0 - uv2[1])

        # set material index
        bm.faces[i].material_index = SSrfTri[3]

        # TODO flags
        # SRFTF_INACTIVE    = 0x00000001, // triangle is not active
        # SRFTF_HIDDEN      = 0x00000002, // present but invisible
        # SRFTF_VNIGNORE    = 0x00000004, // ignored in vertex normal calculations
        # SRFTF_TRANSPARENT = 0x00000008, // transparent rendering is enabled
        # SRFTF_UNLIT       = 0x00000020, // not affected by dynamic lighting
        # SRFTF_TWOSIDED    = 0x00000040, // visible from both sides
        # SRFTF_MASKING     = 0x00000080, // color key masking is active
        # SRFTF_MODULATED   = 0x00000100, // modulated rendering is enabled
        # SRFTF_ENVMAP      = 0x00000200, // environment mapped
        # SRFTF_NONCOLLIDE  = 0x00000400, // traceray won't collide with this surface
        # SRFTF_TEXBLEND    = 0x00000800,
        # SRFTF_ZLATER      = 0x00001000,
        # SRFTF_RESERVED    = 0x00010000

        shift += 16

    # update object mesh
    bm.to_mesh(bl_object.data)
    bm.free()


# ----------------------------------------------------------------------------
def chunk_lod(data, idx, name):
    print("Level Of Detail Chunk (LOD)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


# ----------------------------------------------------------------------------
def chunk_skl(data, idx, name):
    print("Skeleton Chunk (SKL)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


# ----------------------------------------------------------------------------
def chunk_frm(data, idx, name):
    print("Vertex Frames Chunk (FRM)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


# ----------------------------------------------------------------------------
def chunk_seq(data, idx, name):
    print("Sequenced Animation Chunk (SEQ)")
    print("- '%s'" % name)
    print("! unsupported")
    return False


# EoF
