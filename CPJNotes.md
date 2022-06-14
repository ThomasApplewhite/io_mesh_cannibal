Some notes regarding the importer/exporter that I haven't written into a real doc

Import/Export does not support:
+Multiple blender objects
+Multiple surfaces
+Mounts or Object Links in Geometry
+LODs, Skeletons, Vertex Frames, or Animations

Exporter does not support:
+MAC or Surfaces
+Correct empty-chunk handling
    -Until this is resolved, the exporter won't work
    
 Other notes:
 All chunks need header data
 Chunks (and .cpj files in general) must be RIFF compatable
 The order and number of chunks doesn't matter
 If a chunk is an odd number of bytes long, a byte must be added to it.
 
 .MAC chunks have no meaningful equivenlant in Blender, probably, but are needed to make things work in Cannibal.
 So, either 0-out MAC chunks as a rule, or figure out how to recombing them with original .cpj files post-edit
 Or get fucking goated and simply invent the conversion
 However, the importer handles them. Maybe there's something there?
 
 HAH WAIT GOT IT
 Each file needs the 'autoexec' MAC chunk which runs basic setup commands! Check line 202!
 
 It's still unclear what a "mount" or an "object link" are, but the layout of a GeoChunk can be found starting at line 246
 
 So, for now, I'm just gonna try to make an empty .cjp file that Cannibal can load, since all the formatting is here. I just gotta use it...

Cannibal has a different coordinate system than Blender does
From the perspective of the camera, in a right handed coordinate system, right-up-forward is
Cannibal: x-y-z
Blender: x-z-y
So, like in the importer, z and y coordinates are swapped
Also, in Cannibal, Rotation is always the 2nd transform operation. Not sure if that matter

Do the scripts need to be in the same file? idk I'll figure that out later