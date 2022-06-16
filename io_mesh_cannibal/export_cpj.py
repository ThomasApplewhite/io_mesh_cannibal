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

CPJ_FRM_MAGIC = "FRMB"
CPJ_FRM_VERSION = 1
CPJ_GEO_MAGIC = "GEOB"
CPJ_GEO_VERSION = 1
CPJ_LOD_MAGIC = "LODB"
CPJ_LOD_VERSION = 3
CPJ_MAC_MAGIC = "MACB"
CPJ_MAC_VERSION = 1
CPJ_SEQ_MAGIC = "SEQB"
CPJ_SEQ_VERSION = 1
CPJ_SKL_MAGIC = "SKLB"
CPJ_SKL_VERSION = 1
CPJ_SRF_MAGIC = "SRFB"
CPJ_SRF_VERSION = 1


# ----------------------------------------------------------------------------
def save(context, filepath):
    # raise Exception('Exporting CPJ is not supported')
    # return {'CANCELLED'}

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

    with open(temppath, mode="ab") as handle:
        # erase present data
        handle.truncate(0)

        # compatibility flags
        bl_object = None
        has_surface_already = False

        # chunks order workaround
        # loop 0: MAC
        # loop 1: GEO
        # loop 2: SRF
        # loop 3: rest
        for loop in range(4):

            output_array = operate_chunk_order(handle, loop)
            # data manipulation here
            handle.write(output_array)

    # header logic
    with open(filepath, "ab") as destinationHandle:
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

        with open (temppath, "rb") as dataHandle:
            print("Writing to Destination File")
            for line in dataHandle:

                # !!!ASSUME
                # making some assumptions here:
                # 1: no ASCII encoding occurs in binary read mode
                # (that is, line will be written as binary)
                # 2: It's acceptable to load the entire file at once
                # into memory because the importer does it lol
                destinationHandle.write(line)

        
        # ensure destination file integrity maybe

    # delete temp file
    os_remove(temppath)
            
    return {'FINISHED'}


# ----------------------------------------------------------------------------
# returns a byte array containing one chunk's worth of data
def operate_chunk_order(fileHandler, loop):
    # !!!ASSUME
    # Assuming chunk order is irrelivant, and that I can write them
    # to file in MAC->GEO->SRF->LOD->SKL->FRM->SEQ order

    functionDict = {
        0 : chunk_mac,
        1 : chunk_geo,
        2 : chunk_srf,
        3 : chunk_lod,
        4 : chunk_skl,
        5 : chunk_frm,
        6 : chunk_seq
    }

    newData = bytearray()
    # delegate
    # not sure what signature I'm gonna need since data comes from
    # blender. Let's just not have one right now.

    # if the dict works we'll probably put this back in the save method
    # where it went originally

    # or return format_data(functionDict[loop]()) if you wanna be extra
    newData = functionDict[loop]()
    newData = format_data(newData)
    return newData

    if loop == 0:
        chunk_mac(data, idx, name)

    elif loop == 1:
        # will fail if multiple geos
        chunk_geo(data, idx, name)

    elif loop == 2:
        # will fail if multiple srf
        # but we can assume a geo will exist
        chunk_srf(data, idx, name, bl_object)
    elif loop == 3:
        chunk_lod(data, idx, name)
    elif loop == 4:
        chunk_skl(data, idx, name)
    elif loop == 5:
        chunk_frm(data, idx, name)
    elif loop == 6:
        chunk_seq(data, idx, name)
    else:
        # nothing should happen here so it should be fine?
        pass

    # seek to next chunk (16 bit aligned)
    return #SCpjChunkHeader[1] + (SCpjChunkHeader[1] % 2) + 8

# ----------------------------------------------------------------------------
def format_data(data):
    pass


# ----------------------------------------------------------------------------
def chunk_mac(data, idx, name):
    print("Cannibal Model Actor Configuration Chunk (MAC)")
    print("- '%s'" % name)
    print("! unsupported")

    # MACs have no functional eqivelant in Blender, since MACs are sensitive
    # to the install path of the Cannibal Editor itself. However,
    # the autoexec MAC is required and has easily defined values. So,
    # this exporter will only add that MAC for now.
    # See line 122 of CpjFmt.h for more details
    # 
    # Study the importer. It (probably?) knows how to shift everything
    # To keep the data aligned 

    return

    # What is a MAC in the context of blender

    print("Cannibal Model Actor Configuration Chunk (MAC)")

    # unsigned long numSections; // number of sections
    # unsigned long ofsSections; // offset of sections in data block
    # unsigned long numCommands; // number of commands
    # unsigned long ofsCommands; // offset of command strings in data block
    SMacFile = struct.unpack_from("IIII", data, idx + 20)

    print("- '%s'" % name)
    print("- %d Sections" % SMacFile[0])
    print("- %d Commands" % SMacFile[2])

    # offset
    block = idx + 20 + 16

    # read sections
    shift = block + SMacFile[1]
    for i in range(SMacFile[0]):

        # unsigned long ofsName // offset of section name string in data block
        # unsigned long numCommands // number of command strings in section
        # unsigned long firstCommand // first command string index
        SMacSection = struct.unpack_from("III", data, shift)

        section = ctypes.create_string_buffer(
            data[block + SMacSection[0]:]).value.decode()

        # read commands
        count = SMacSection[1]
        for j in range(count):

            ofs = struct.unpack_from("I", data,
                                     block + SMacFile[3] + (SMacSection[2] + j) * 4)[0]
            command = ctypes.create_string_buffer(
                data[block + ofs:]).value.decode()

            print("+ #%d %s %d/%d : %s" %
                  (i + 1, section, j + 1, count, command))

        # next section
        shift += 12


# ----------------------------------------------------------------------------
def chunk_geo(context):
    # !!!ASSUME
    # not an assumption but make sure to error multiple geo blocks
    # (that is, error if there are multiple blender objects)
    print("Geometry Chunk (GEO)")

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
    return


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


# ----------------------------------------------------------------------------
def chunk_skl(data, idx, name):
    print("Skeleton Chunk (SKL)")
    print("- '%s'" % name)
    print("! unsupported")


# ----------------------------------------------------------------------------
def chunk_frm(data, idx, name):
    print("Vertex Frames Chunk (FRM)")
    print("- '%s'" % name)
    print("! unsupported")


# ----------------------------------------------------------------------------
def chunk_seq(data, idx, name):
    print("Sequenced Animation Chunk (SEQ)")
    print("- '%s'" % name)
    print("! unsupported")


# EoF
