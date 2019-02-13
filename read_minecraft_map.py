import nbt
import numpy as np

def read_minecraft_map(map_path, start, end):
    metadata = nbt.nbt.NBTFile(map_path+'/level.dat', 'rb')
    version = metadata[0]['Version']['Name']
    position = metadata[0]['Player']['Pos']
    world = nbt.world.WorldFolder(map_path)

    sections = {}
    for x_chunk in range(int(start[0]/16), int(end[0]/16+1)):
        for z_chunk in range(int(start[2]/16), int(end[2]/16+1)):
            temp = world.get_nbt(x_chunk, z_chunk)
            chunk = world.get_nbt(x_chunk, z_chunk)['Level']['Sections']
            for section in chunk:
                if '12' in version:
                    sections[(x_chunk, section["Y"].value, z_chunk)] = section["Blocks"]
                elif '13' in version:
                    sections[(x_chunk, section["Y"].value, z_chunk)] = section["BlockStates"]
                else:
                    raise Exception("WTF")

    new_map = np.zeros(end - start)
    for x_point in range(int(start[0]), int(end[0])):
        for y_point in range(int(start[1]), int(end[1])):
            for z_point in range(int(start[2]), int(end[2])):
                section_x = int(x_point/16)
                section_y = int(y_point/16)
                section_z = int(z_point/16)
                if (section_x, section_y, section_z) not in sections.keys():
                    raise Exception("Could not find chunk " + str(section_x) + ", " + str(section_y) + ", " + str(section_z))

                section = sections[(section_x, section_y, section_z)]
                offset = (x_point%16) + (z_point%16)*16 + (y_point)%(16*16)*(16*16)
                if offset < len(section):
                    block = section[offset]
                    new_map[x_point-start[0], y_point-start[1], z_point-start[2]] = block

    return new_map
