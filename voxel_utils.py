import struct
import numpy as np


# This function is based on https://github.com/RichysHub/MagicaVoxel-VOX-importer
def import_vox(path):
    import time
    time_start = time.time()

    with open(path, 'rb') as vox:

        voxels = []
        palette = {}

        # assert is VOX 150 file
        assert (struct.unpack('<4ci', vox.read(8)) == (b'V', b'O', b'X', b' ', 150))

        # MAIN chunk
        assert (struct.unpack('<4c', vox.read(4)) == (b'M', b'A', b'I', b'N'))
        N, M = struct.unpack('<ii', vox.read(8))
        assert (N == 0)  # MAIN chunk should have no content

        # M is remaining # of bytes in file

        while True:
            try:
                *name, s_self, s_child = struct.unpack('<4cii', vox.read(12))
                assert (s_child == 0)  # sanity check
                name = b''.join(name).decode('utf-8')  # unsure of encoding..
            except struct.error:
                # end of file
                break
            if name == 'PACK':
                # number of models
                num_models = struct.unpack('<i', vox.read(4))
            elif name == 'SIZE':
                # model size
                # x, y, z = struct.unpack('<3i', vox.read(12))
                vox.read(12)
            elif name == 'XYZI':
                # voxel data
                num_voxels, = struct.unpack('<i', vox.read(4))
                for voxel in range(num_voxels):
                    voxel_data = struct.unpack('<4B', vox.read(4))
                    voxels.append(voxel_data)
                return voxels
            elif name == 'RGBA':
                # palette
                for col in range(256):
                    palette.update({col + 1: struct.unpack('<4B', vox.read(4))})
            elif name == 'MATT':
                # material
                matt_id, mat_type, weight = struct.unpack('<iif', vox.read(12))

                prop_bits, = struct.unpack('<i', vox.read(4))
                binary = bin(prop_bits)
                # Need to read property values, but this gets fiddly
                # TODO: finish implementation
            else:
                # Any other chunk, we don't know how to handle
                # This puts us out-of-step
                print('Unknown Chunk id {}'.format(name))
                return {'CANCELLED'}


def read_voxel_file(filepath):
    m = import_vox(filepath)
    voxels = {}
    for voxel in m:
        voxels[(voxel[0], voxel[2], voxel[1])] = voxel[3]
    size_x = max([x[0] for x in m])+1
    size_y = max([x[2] for x in m])+1
    size_z = max([x[1] for x in m])+1
    voxel_map = np.zeros((size_x, size_y, size_z), dtype=np.uint8)
    for x in range(size_x):
        for y in range(size_y):
            for z in range(size_z):
                if (x,y,z) in voxels.keys():
                    voxel_map[x,y,z] = int(voxels[(x,y,z)])

    return voxel_map