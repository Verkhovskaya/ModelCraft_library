import sys
import numpy as np
import os
from fpdf import FPDF
from PIL import Image
import shutil
import sys
import copy
import random
import shutil

sys.setrecursionlimit(100000)


from dxfwrite import DXFEngine as dxf

colors = {0: (255, 255, 255), 1: (139,105,20), 2: (0, 0, 255), 3: (100, 100, 100)}


def generate_laser_cut_files(destination_path, read_map, settings):
    side_length = float(settings['thickness'])
    material_length = int(settings['material_length'])
    material_width = int(settings['material_width'])

    units_x = int(material_length/side_length) - 2
    units_z = int(material_width/side_length) - 2

    image_directory = destination_path + "/cutout_images"
    if os.path.exists(image_directory):
        shutil.rmtree(image_directory)
    os.mkdir(image_directory)

    lines_dict = {}

    read_map = read_map > 0.1

    block_type = 'temp'
    for i in range(1):
        if True:
            cutouts = get_cutouts(read_map, int(settings['max_cutout_piece_size']))
            settings['num_pieces'] = len(cutouts)
            if settings['num_pieces'] > 5000:
                raise Exception("Too many (>5000) pieces. Maybe try something a little smaller?")
            cutouts_placed_by_sheets = place_basic(cutouts, units_x, units_z)
            number_of_sheets_generated = len(cutouts_placed_by_sheets)
            all_lines = []
            all_rasters = []
            for sheet_id in range(1, number_of_sheets_generated+1):
                cutouts_in_sheet = list(cutouts_placed_by_sheets[sheet_id-1])
                lines, rasters = get_lines(cutouts_in_sheet)
                lines_with_tabs = add_tabs(lines, float(settings['tab_size'])/side_length)
                generate_png(destination_path, sheet_id, units_x, units_z, lines_with_tabs, block_type)
                for line in lines_with_tabs:
                    all_lines.append(((line[0][0]*side_length, line[0][1]*side_length+(sheet_id-1)*material_width*1.2),
                                      (line[1][0]*side_length, line[1][1]*side_length+(sheet_id-1)*material_width*1.2)))
                for raster in rasters:
                    all_rasters.append(((raster[0][0]*side_length, raster[0][1]*side_length+(sheet_id-1)*material_width*1.2),
                                      (raster[1][0]*side_length, raster[1][1]*side_length+(sheet_id-1)*material_width*1.2)))
            lines_dict[block_type] = {'vector': all_lines, 'raster': all_rasters}

    bottom_layer_lines = generate_bottom_layer_cutout(read_map, settings)
    generate_dxf(destination_path, bottom_layer_lines, lines_dict, material_length, settings)


def generate_bottom_layer_cutout(block_array, settings):
    vectors = set([])
    rasters = set([])

    for x in range(block_array.shape[0]):
        for z in range(block_array.shape[2]):
            if block_array[x,0,z]:
                vectors = vectors.symmetric_difference([((x,z),(x+1,z))])
                vectors = vectors.symmetric_difference([((x,z),(x,z+1))])
                vectors = vectors.symmetric_difference([((x+1,z),(x+1,z+1))])
                vectors = vectors.symmetric_difference([((x,z+1),(x+1,z+1))])
            if block_array[x,1,z] and block_array[x,0,z]:
                rasters = rasters.symmetric_difference([((x,z),(x+1,z))])
                rasters = rasters.symmetric_difference([((x,z),(x,z+1))])
                rasters = rasters.symmetric_difference([((x+1,z),(x+1,z+1))])
                rasters = rasters.symmetric_difference([((x,z+1),(x+1,z+1))])
    vectors_scaled = set([])
    rasters_scaled = set([])
    i = settings['thickness']
    for vector in vectors:
        vectors_scaled.add(((vector[0][0]*i, vector[0][1]*i), (vector[1][0]*i, vector[1][1]*i)))
    for raster in rasters:
        rasters_scaled.add(((raster[0][0]*i, raster[0][1]*i), (raster[1][0]*i, raster[1][1]*i)))

    return {'vector': vectors_scaled, 'raster': rasters_scaled-vectors_scaled}


def get_cutouts(block_array, piece_max):
    all_cutouts = []
    for y in range(1,block_array.shape[1]):
        flat = [[Tile(block_array[x, y, z]) for x in range(block_array.shape[0])] for z in range(block_array.shape[2])]
        for x in range(block_array.shape[0]):
            for z in range(block_array.shape[2]):
                cutout = spread(flat, x, z)
                if cutout:
                    min_x = min([a[0] for a in cutout])
                    max_x = max([a[0] for a in cutout])
                    min_z = min([a[1] for a in cutout])
                    max_z = max([a[1] for a in cutout])
                    cutout_array = np.zeros((int(max_x - min_x + 1), int(max_z - min_z + 1)), dtype=bool)
                    for x_next in range(cutout_array.shape[0]):
                        for z_next in range(cutout_array.shape[1]):
                            cutout_array[x_next, z_next] = (x_next + min_x, z_next + min_z) in cutout
                    if y+1 < block_array.shape[1]:
                        cutout_above = block_array[min_x:max_x+1,y+1,min_z:max_z+1] & cutout_array
                    else:
                        cutout_above = np.zeros(cutout_array.shape, dtype=bool)
                    all_cutouts.append({'is': cutout_array, 'above': cutout_above})

    cutouts_smaller_than_max = []
    for cutout in all_cutouts:
        for x in range(int(cutout['is'].shape[0]/piece_max)+1):
            for z in range(int(cutout['is'].shape[1]/piece_max)+1):
                start_x = x*piece_max
                start_z = z*piece_max
                end_x = min((x+1)*piece_max, cutout['is'].shape[0])
                end_z = min((z+1)*piece_max, cutout['is'].shape[1])
                small_is = cutout['is'][start_x:end_x,start_z:end_z]
                small_above = cutout['above'][start_x:end_x, start_z:end_z]
                cutouts_smaller_than_max.append({'is': small_is, 'above': small_above})

    return cutouts_smaller_than_max


def add_tabs(lines, tab_unit_size):
    original_lines = set(lines)
    new_lines = []
    for line in lines:
        line_vector = ((line[1][0]-line[0][0]), (line[1][1]-line[0][1]))
        if line_vector[1] == 0:
            if ((line[0][0], line[0][1]), (line[0][0], line[0][1]+1)) in original_lines or \
                ((line[0][0], line[0][1]+1), (line[0][0], line[0][1])) in original_lines:
                new_lines.append(((line[0][0], line[0][1]),\
                    (line[0][0]+line_vector[0]*(1-tab_unit_size)/2, line[0][1]+line_vector[1]*(1-tab_unit_size)/2)))
                new_lines.append(((line[1][0], line[1][1]), \
                                 (line[1][0] - line_vector[0] * (1 - tab_unit_size) / 2,
                                  line[1][1] - line_vector[1] * (1 - tab_unit_size) / 2)))
            else:
                if random.random()*4 < 1:
                    new_lines.append(((line[0][0], line[0][1]),\
                        (line[0][0]+line_vector[0]*(1-tab_unit_size)/2, line[0][1]+line_vector[1]*(1-tab_unit_size)/2)))
                    new_lines.append(((line[1][0], line[1][1]), \
                                     (line[1][0] - line_vector[0] * (1 - tab_unit_size) / 2,
                                      line[1][1] - line_vector[1] * (1 - tab_unit_size) / 2)))
                else:
                    new_lines.append(line)
        else:
            if random.random()*4 < 1:
                new_lines.append(((line[0][0], line[0][1]),\
                    (line[0][0]+line_vector[0]*(1-tab_unit_size)/2, line[0][1]+line_vector[1]*(1-tab_unit_size)/2)))
                new_lines.append(((line[1][0], line[1][1]), \
                                 (line[1][0] - line_vector[0] * (1 - tab_unit_size) / 2,
                                  line[1][1] - line_vector[1] * (1 - tab_unit_size) / 2)))
            else:
                new_lines.append(line)

    return new_lines


class Tile:
    def __init__(self, type):
        self.seen = False
        self.type = type


def spread(flat, x, y):
    if x < 0 or x >= len(flat[0]) or y < 0 or y >= len(flat):
        return []
    if flat[y][x].seen or not flat[y][x].type:
        return []
    flat[y][x].seen = True
    visited = []
    visited += spread(flat, x + 1, y)
    visited += spread(flat, x, y + 1)
    visited += spread(flat, x - 1, y)
    visited += spread(flat, x, y - 1)
    visited.append((x, y))
    return visited



class Cutout():
    def __init__(self, array, x, y):
        self.array = array
        self.x = x
        self.y = y

    def __str__(self):
        return str(self.x) + " " + str(self.y)


class Sheet:
    def __init__(self, x_size, y_size):
        self.x_size = x_size
        self.y_size = y_size
        self.array = np.zeros((x_size, y_size), dtype=bool)
        # TODO: Fix this down here. It technically should be just x_size, but whatever
        self.empty_verticals = [x_size-1 for y in range(y_size)]
        self.cutouts = []

    def place(self, cutout):
        for y in range(self.array.shape[1] - cutout['is'].shape[1]):
            if self.empty_verticals[y] >= cutout['is'].shape[0]:
                for x in range(self.array.shape[0] - cutout['is'].shape[0]):
                    for rotate in range(1):
                        rotated_cutout = np.rot90(cutout['is'], k=rotate, axes=(0, 1))
                        if y + rotated_cutout.shape[1] < self.y_size and x + rotated_cutout.shape[0] < self.x_size:
                            if not True in self.array[x:x + rotated_cutout.shape[0], y:y + rotated_cutout.shape[1]] * rotated_cutout:
                                self.array[x:x + rotated_cutout.shape[0], y:y + rotated_cutout.shape[1]] += rotated_cutout
                                for y_level in range(rotated_cutout.shape[1]):
                                    self.empty_verticals[y+y_level] -= sum(rotated_cutout[:,y_level])
                                self.cutouts.append(Cutout(cutout, x, y))
                                return

        raise Exception("Could not place. cutout: " + str(cutout) + ", empty verticals: " + str(self.empty_verticals))


def place_basic(cutouts, units_x, units_y):
    sheets = [Sheet(units_x, units_y)]
    cutouts_by_height = sorted(cutouts, key=lambda cutout: cutout['is'].shape[1])[::-1]
    num_cutouts = len(cutouts_by_height)
    cutouts_with_placement = []
    i = 0
    for new_cutout in cutouts_by_height:
        i += 1
        placed = False
        for sheet in sheets:
            try:
                sheet.place(new_cutout)
                placed = True
                break
            except Exception as e:
                pass
        if not placed:
            new_sheet = Sheet(units_x, units_y)
            new_sheet.place(new_cutout)
            sheets.append(new_sheet)
    return [sheet.cutouts for sheet in sheets]


def get_lines(cutouts):
    vectors = set([])
    rasters = set([])

    for cutout in cutouts:
        cutout_vectors = set([])
        cutout_rasters = set([])
        for x in range(cutout.x, cutout.x+cutout.array['is'].shape[0]):
            for y in range(cutout.y, cutout.y+cutout.array['is'].shape[1]):
                if cutout.array['is'][x-cutout.x,y-cutout.y]:
                    cutout_vectors = cutout_vectors.symmetric_difference([((x,y),(x+1,y))])
                    cutout_vectors = cutout_vectors.symmetric_difference([((x,y),(x,y+1))])
                    cutout_vectors = cutout_vectors.symmetric_difference([((x+1,y),(x+1,y+1))])
                    cutout_vectors = cutout_vectors.symmetric_difference([((x,y+1),(x+1,y+1))])
                if cutout.array['above'][x-cutout.x,y-cutout.y] and cutout.array['is'][x-cutout.x,y-cutout.y]:
                    cutout_rasters = cutout_rasters.symmetric_difference([((x,y),(x+1,y))])
                    cutout_rasters = cutout_rasters.symmetric_difference([((x,y),(x,y+1))])
                    cutout_rasters = cutout_rasters.symmetric_difference([((x+1,y),(x+1,y+1))])
                    cutout_rasters = cutout_rasters.symmetric_difference([((x,y+1),(x+1,y+1))])
        vectors = vectors.union(cutout_vectors)
        rasters = rasters.union(cutout_rasters)
    return vectors, rasters-vectors


def generate_dxf(destination_path, bottom_layer_lines, lines_dict, sheet_length, settings):
    drawing = dxf.drawing(destination_path + '/cutout.dxf')
    drawing.add_layer('RASTER')
    drawing.add_layer('VECTOR')

    for line in bottom_layer_lines['vector']:
        drawing.add(dxf.line(line[0], line[1], color=7, layer='VECTOR', thickness=0))

    for line in bottom_layer_lines['raster']:
        drawing.add(dxf.line(line[0], line[1], color=7, layer='RASTER', thickness=0.05))

    x_offset = int(sheet_length * 1.1)
    y_offset = 30
    keys = list(lines_dict.keys())


    for i in range(len(keys)):
        key = keys[i]
        for line in lines_dict[key]['vector']:
            start = (line[0][0]+x_offset*i+int(settings["size_z"]*settings["thickness"])*1.2, line[0][1]+y_offset)
            end = (line[1][0]+x_offset*i+int(settings["size_z"]*settings["thickness"])*1.2, line[1][1]+y_offset)
            drawing.add(dxf.line(start, end, color=7, layer='VECTOR', thickness=0))
        for line in lines_dict[key]['raster']:
            start = (line[0][0]+x_offset*i+int(settings["size_z"]*settings["thickness"])*1.2, line[0][1]+y_offset)
            end = (line[1][0]+x_offset*i+int(settings["size_z"]*settings["thickness"])*1.2, line[1][1]+y_offset)
            drawing.add(dxf.line(start, end, color=7, layer='RASTER', thickness=0.05))

    drawing.add_layer('TEXTLAYER', color=2)

    for i in range(len(keys)):
        key = keys[i]
        #drawing.add(dxf.text(key, insert=(i*x_offset, 0), layer='TEXTLAYER', height=25))

    drawing.add_vport('*ACTIVE', upper_right=(100,100), center_point=(50,50), grid_spacing=(1,1), snap_spacing=(1,1), aspect_ratio=20)
    drawing.save()


def generate_png(destination_path, sheet_id, units_x, units_y, lines, block_type):
    render_unit_length = 10
    image = np.zeros(((units_y+2) * render_unit_length, (units_x + 2) * render_unit_length, 3), dtype=np.uint8)
    for line in lines:
        start = min(line[0][0], line[1][0])+1, min(line[0][1], line[1][1])+1
        end = max(line[0][0], line[1][0])+1, max(line[0][1], line[1][1])+1
        image[int(render_unit_length*start[1])-2:int(render_unit_length*end[1])+2,
              int(render_unit_length*start[0])-2:int(render_unit_length*end[0])+2] = (255, 255, 255)

    img = Image.fromarray(image, 'RGB')
    img_name = destination_path + "/cutout_images/" + block_type + "_" + str(sheet_id) + "_cutout.png"
    img.save(img_name)
