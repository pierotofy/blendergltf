import json
import os

import bpy
from bpy.props import *
from bpy_extras.io_utils import (
    axis_conversion,
)

from .filters import visible_only, selected_only, used_only
from .blendergltf import export_gltf

profile_items = (
    ('WEB', 'Web', 'Export shaders for WebGL 1.0 use (shader version 100)'),
    ('DESKTOP', 'Desktop', 'Export shaders for OpenGL 3.0 use (shader version 130)')
)

image_storage_items = (
    ('EMBED', 'Embed', 'Embed image data into the glTF file'),
    ('REFERENCE', 'Reference', 'Use the same filepath that Blender uses for images'),
    ('COPY', 'Copy', 'Copy images to output directory and use a relative reference')
)

shader_storage_items = (
    ('EMBED', 'Embed', 'Embed shader data into the glTF file'),
    ('NONE', 'None', 'Use the KHR_material_common extension instead of a shader'),
    ('EXTERNAL', 'External', 'Save shaders to the output directory')
)

def exportToGlTF(outdir, levels):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print("Created {}".format(outdir))

    modifiers = []

    for obj in [x for x in bpy.data.objects if x.type == 'MESH']:
        m = obj.modifiers.new(name='decimate', type='DECIMATE')
        m.ratio = 1.0
        modifiers.append(m)

    for level in range(levels):
        print("Generating LOD {} for {}...".format(level, outdir))

        filepath = os.path.join(outdir, str(level) + ".gltf")


        settings = {
            'filepath': filepath, 
            'check_existing': True,
            'draft_prop': False, 
            'materials_disable': False, 
            'buffers_embed_data': True, 
            'buffers_combine_data': True, 
            'nodes_export_hidden': False, 
            'nodes_selected_only': False, 
            'blocks_prune_unused': False,
            'shaders_data_storage': 'NONE', 
            'meshes_apply_modifiers': True, 
            'meshes_interleave_vertex_data': True, 
            'images_data_storage': 'EMBED',
            'images_allow_srgb': False,  
            'asset_profile': 'WEB',
            'asset_version': '2.0',
            'animations_object_export': 'ACTIVE', 
            'animations_armature_export': 'ELIGIBLE', 
            'ext_export_physics': False, 
            'ext_export_actions': False, 
            'pretty_print': False, 
            'gltf_output_dir': outdir,
            'nodes_global_matrix': axis_conversion(
                                        to_up="-Z",
                                        to_forward="-Y",
                                    ).to_4x4()
        }

        # filter data according to settings
        data = {
            'actions': list(bpy.data.actions),
            'cameras': list(bpy.data.cameras),
            'lamps': list(bpy.data.lamps),
            'images': list(bpy.data.images),
            'materials': list(bpy.data.materials),
            'meshes': list(bpy.data.meshes),
            'objects': list(bpy.data.objects),
            'scenes': list(bpy.data.scenes),
            'textures': list(bpy.data.textures),
        }

        if not settings['nodes_export_hidden']:
            data = visible_only(data)

        if settings['nodes_selected_only']:
            data = selected_only(data)

        if settings['blocks_prune_unused']:
            data = used_only(data)

        gltf = export_gltf(data, settings)
        with open(filepath, 'w') as fout:
            # Figure out indentation
            if settings['pretty_print']:
                indent = 4
            else:
                indent = None

            # Dump the JSON
            json.dump(gltf, fout, indent=indent, sort_keys=True,
                      check_circular=False)

            if settings['pretty_print']:
                # Write a newline to the end of the file
                fout.write('\n')

        for m in modifiers:
            m.ratio /= 2

    print("Done")
