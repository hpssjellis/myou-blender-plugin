import bpy
Object = bpy.types.Object
# TODO: defer loading numpy?
import numpy as np
from hashlib import md5
from . import object

from time import perf_counter
import inspect
def perf_t(last_t):
    t = perf_counter()
    linenum = inspect.stack()[1][2]
    print("{}: {:0.8f}".format(linenum, t-last_t))
    return t


def mesh_hash(ob, used_data, extra_data):
    '''Repeatable mesh hash for caching purposes'''
    # t = perf_counter()

    hash = md5()

    vlen = len(ob.data.vertices)
    # reusing array
    vertices = normals = shape_key = np.empty(vlen*3, dtype=np.float32)
    ob.data.vertices.foreach_get('co', vertices)
    hash.update(vertices)
    ob.data.vertices.foreach_get('normal', normals)
    hash.update(normals)
    if ob.data.shape_keys:
        for kb in ob.data.shape_keys.key_blocks[1:]:
            kb.data.foreach_get('co', shape_key)
            hash.update(shape_key)
    # Something's going on with normals when editing a shape key
    # but it shouoldn't be an issue since they're only used without shape keys

    # t = perf_t(t)

    face_sizes = np.empty(len(ob.data.polygons), dtype=np.uint16)
    ob.data.polygons.foreach_get('loop_total', face_sizes)
    num_indices = int(face_sizes.sum())
    hash.update(face_sizes)

    # t = perf_t(t)

    indices = np.empty(num_indices, dtype=np.uint32)
    ob.data.polygons.foreach_get('vertices', indices)
    hash.update(indices)

    # t = perf_t(t)

    # reusing array
    materials = flags = np.empty(len(ob.data.polygons), dtype=np.uint8)
    ob.data.polygons.foreach_get('material_index', materials)
    hash.update(materials)
    ob.data.polygons.foreach_get('use_smooth', flags)
    hash.update(flags)

    # TODO: detect if this is necessary by looking at:
    # * auto smooth
    # * edge sharp modifier in _all_ users
    edge_sharp = np.empty(len(ob.data.edges), dtype=np.uint8)
    ob.data.edges.foreach_get('use_edge_sharp', edge_sharp)
    hash.update(edge_sharp)

    # t = perf_t(t)

    uv_data = np.empty(num_indices*2, dtype=np.float32)
    for i in range(len(ob.data.uv_layers)):
        ob.data.uv_layers[i].data.foreach_get('uv', uv_data)
        hash.update(uv_data)

    # t = perf_t(t)

    if ob.vertex_groups:
        num_groups = 0
        for v in ob.data.vertices:
            num_groups += len(v.groups)
        # using the same float array both for weights and indices
        groups = np.empty(num_groups*2, dtype=np.float32)
        i = 0
        for v in ob.data.vertices:
            for g in v.groups:
                groups[i] = g.weight
                groups[i+1] = g.group
                i += 2
        hash.update('|'.join(ob.vertex_groups.keys()).encode())
        hash.update(groups)

    modifier_data = []
    for m in ob.modifiers:
        if m.show_viewport:
            for k in dir(m):
                v = getattr(m,k)
                if not callable(v):
                    modifier_data.append(k)
                    # TODO: Convert meshes too, for booleans etc
                    # but avoiding infinite loops
                    if isinstance(v, Object) and v.type != 'MESH':
                        v = object.ob_to_json(v, None, used_data, export_pose=False)
                        open('/tmp/b.txt', 'w').write(repr(v))
                    modifier_data.append(repr(v))
    hash.update('|'.join(modifier_data).encode())

    material_names = [m.name for m in ob.material_slots]
    material_indices = [material_names.index(name) for name in material_names]
    hash.update(bytes(material_indices))

    hash.update(repr(extra_data).encode())

    # t = perf_t(t)

    return hash.hexdigest()

    # t = perf_t(t)

def start_watcher(ob):
    pass

def stop_watcher(ob):
    pass
