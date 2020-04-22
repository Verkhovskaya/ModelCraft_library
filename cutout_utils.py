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


# from dxfwrite import DXFEngine as dxf

class Cutout():
    def __init__(self, block_id_array, no_cut_array, full_cut_array):
        self.block_id_array = block_id_array
        self.no_cut_array = no_cut_array
        self.full_cut_array = full_cut_array
    
    def set_location(self, x, z):
        self.x = x
        self.z = z
    
    def __str__(self):
        return str(self.block_id_array.shape)

def get_cutouts(raw_map, args, colors, peices):
    cutouts = []
    for y in peices.keys():
        for peice in peices[y]:
            min_x = min([i[0] for i in peice])
            width = max([i[0] for i in peice]) - min_x + 1
            min_z = min([i[1] for i in peice])
            length = max([i[1] for i in peice]) - min_z + 1
            block_id_array = np.zeros((width, length), dtype=np.uint8)
            no_cut_array = np.zeros((width*args.scale+4, length*args.scale+4), dtype=bool)
            full_cut_array = np.zeros((width*args.scale+4, length*args.scale+4), dtype=bool)

            for block in peice:
                block_id = raw_map[block[0], y, block[1]]
                x = block[0]-min_x
                z = block[1]-min_z
                block_id_array[x, z] = block_id
                if block_id not in args.filter:
                    no_cut_array[x*args.scale+2:((x+1)*args.scale)+2, z*args.scale+2:((z+1)*args.scale)+2] = True
                    full_cut_array[x*args.scale:(x+1)*args.scale+4, z*args.scale:((z+1)*args.scale)+4] = True
            cutouts.append(Cutout(block_id_array, no_cut_array, full_cut_array))
            
    return cutouts

def negative_area(array):
    return -array.full_cut_array.shape[0] * array.full_cut_array.shape[1]

def can_fit(sheet, array, x, z):
    for xi in range(array.shape[0]):
        if np.any(np.logical_and(array[xi, :], sheet[x+xi, z:z+array.shape[1]])):
            return False
    return True

def try_to_place(sheet, cutout, args):
    if (cutout.full_cut_array.shape[0] > sheet.shape[0] or cutout.full_cut_array.shape[1] > sheet.shape[1]):
        raise Exception("Cutout is too big to place on sheet")
    for x in range(0,sheet.shape[0]-cutout.full_cut_array.shape[0],args.skip):
        for z in range(0,sheet.shape[1]-cutout.full_cut_array.shape[1],args.skip):
            if can_fit(sheet, cutout.no_cut_array, x, z):
                cutout.set_location(x, z)
                sheet[x:x+cutout.full_cut_array.shape[0], z:z+cutout.full_cut_array.shape[1]] = np.logical_or(sheet[x:x+cutout.full_cut_array.shape[0], z:z+cutout.full_cut_array.shape[1]], cutout.full_cut_array)
                return True
    return False

def place_cutouts(cutouts, args):
    cutouts.sort(key=negative_area)
    cutouts_by_sheet = {}
    sheets = []
    for cutout in cutouts:
        print(cutout.block_id_array.shape)
        sheet_id = 0
        while True:
            if sheet_id == len(sheets):
                sheets.append(np.zeros((int(args.sheet[0]/args.unit), int(args.sheet[1]/args.unit)), dtype=bool))
                cutouts_by_sheet[sheet_id] = []
            else:
                if try_to_place(sheets[sheet_id], cutout, args):
                    cutouts_by_sheet[sheet_id].append(cutout)
                    break
                else:
                    sheet_id += 1
    return cutouts_by_sheet

def scale(val):
    if val == 0:
        return 0
    if val > 0:
        return 1
    else:
        return -1

def get_dir(point1, point2):
    x = scale(point1[0] - point2[0])
    z = scale(point1[1] - point2[1])
    return (x,z)

def get_cut_vectors(cutouts_by_sheet, args):
    for sheet_id in cutouts_by_sheet.keys():
        cutouts = cutouts_by_sheet[sheet_id]
        cut_sheet = np.zeros((int(args.sheet[0]/args.unit), int(args.sheet[1]/args.unit)), dtype=bool)
        for cutout in cutouts:
            cutout_width = cutout.full_cut_array.shape[0]
            cutout_length = cutout.full_cut_array.shape[1]
            cut_sheet[cutout.x:cutout.x+cutout_width, cutout.z:cutout.z+cutout_length] = np.logical_xor(cutout.full_cut_array, cutout.no_cut_array)
        cut_points = []
        for x in range(cut_sheet.shape[0]):
            for z in range(cut_sheet.shape[1]):
                if cut_sheet[x,z] and cut_sheet[x+1,z] and cut_sheet[x,z+1] and cut_sheet[x+1,z+1]:
                    cut_points.append((x,z))
        cut_points = [tuple(i) for i in np.unique(cut_points, axis=0)]
        paths_by_endpoint = {}
        for point in cut_points:
            for previous_point in [(point[0]-1,point[1]), (point[0], point[1]-1), (point[0]+1, point[1]), (point[0], point[1]+1)]:
                if previous_point in paths_by_endpoint.keys():
                    paths_by_endpoint[point] = paths_by_endpoint[previous_point]
                    paths_by_endpoint[point].append(point)
                    del paths_by_endpoint[previous_point]
            if point not in paths_by_endpoint.keys():
                paths_by_endpoint[point] = [point]
        for endpoint in paths_by_endpoint.keys():
            if len(paths_by_endpoint[endpoint]) == 1:
                del paths_by_endpoint[endpoint]
        condensed_paths = []
        for path in paths_by_endpoint.values():
            condensed_path = [path[0], path[1]]
            for point in path[2:]:
                if get_dir(point,condensed_path[-1]) == get_dir(condensed_path[-1], condensed_path[-2]):
                    condensed_path[-1] = point
                else:
                    condensed_path.append(point)
            condensed_paths.append(condensed_path)
        
        generate_gcode(condensed_paths, sheet_id, args)

def generate_gcode(condensed_paths, sheet_id, args):
    file_out = open(args.out + "/" + str(sheet_id) + ".gcode", "w")
    for i in range(int(args.thickness/args.cut_step)):
        cut_depth = i*args.cut_step
        for path in condensed_paths:
            file_out.write("G0 Z0" + "\n")
            file_out.write("X" + str(path[0][0]*args.unit) + " Y" + str(path[0][1]*args.unit) + "\n")
            file_out.write("G1 F" + str(args.feed_rate) + "\n")
            file_out.write("Z" + str(-cut_depth) + "\n")
            for point in path[1:]:
                file_out.write("X" + str(point[0]*args.unit) + " Y" + str(point[1]*args.unit) + "\n")
        file_out.write("G0 Z0" + "\n")
        file_out.write("X0 Y0" + "\n")
    file_out.close()


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
