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

    new_map = np.zeros(end - start, dtype=np.uint8)
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
                    new_map[x_point-start[0], y_point-start[1], z_point-start[2]] = int(block)

    return new_map


block_colors = {1: (100, 100, 100), 2: (150, 180, 100), 3: (100, 80, 60),  4: (80, 80, 80), 5: (150, 130, 80),
                6: (130, 100, 50), 7: (30, 30, 30), 8: (40, 60, 240), 9: (40, 60, 240), 10: (180, 60, 30),
                11: (180, 60, 30), 12: (200, 200, 150), 13: (50, 50, 50), 14: (200, 200, 110), 15: (160, 140, 130),
                16: (70, 70, 70), 17: (160, 130, 90), 18: (120, 150, 100), 19: (200, 200, 90), 20: (250, 250, 250),
                21: (50, 70, 150), 22:(20, 30, 60), 23: (70, 70, 70), 24: (200, 200, 150), 25: (100, 170, 50),
                26: (120, 30, 30), 27: (120, 180, 90), 28: (70, 20, 20), 29: (110, 130, 80), 30:(230, 230, 230),
                31: (50, 80, 50), 32: (140, 100, 50), 33: (120, 100, 70), 34: (120, 100, 70), 35: (210, 210, 210),
                36: (0, 0, 0), 37: (240, 250, 80), 38: (200, 40, 30), 39: (190, 150, 120), 40:(230, 70, 60),
                41: (240, 240, 110), 42: (210, 210, 210), 43: (150, 150, 150), 44: (155, 155, 155), 45: (125, 80, 60),
                46: (100, 40, 20), 47: (140, 120, 80), 48: (90, 110, 90), 49: (20, 20, 30), 50: (210, 150, 80),
                51: (180, 100, 40), 52: (40, 50, 50)}