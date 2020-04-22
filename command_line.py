import minecraft_utils
import voxel_utils
import numpy as np
import cutout_utils
import argparse
import os, shutil
from get_pieces import get_pieces
from generate_layout_images import generate_layout_images

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--minecraft', help='minecraft map path')
parser.add_argument('--voxel', help='voxel file path')
parser.add_argument('--start', help='minecraft map starting position', nargs=3, type=int)
parser.add_argument('--end', help='minecraft map end position', nargs=3, type=int)
parser.add_argument('--out', help='destination folder path')
parser.add_argument('--sheet', help='sheet size (x by y mm)', nargs=2, type=int)
parser.add_argument('--limit', help='max peice size (x by x mm)', type=float)
parser.add_argument('--thickness', help='material thickness (x mm)', type=float)
parser.add_argument('--tab', help='tab size (x mm)', type=float)
parser.add_argument('--half_cut', help='drill radius or half of laser kerf (x mm)', type=float)
parser.add_argument('--filter', help='block ids to filter (ie air)', nargs="+", type=int)
parser.add_argument('--skip', help="place step size (increase to make it run faster. min 1", type=int)
parser.add_argument('--cut_step', help="cut_step", type=float)
parser.add_argument('--feed_rate', type=int)
# Layout file parameters
parser.add_argument('--colors', help='Color map for voxel files. List of repeated values of C R G B', nargs="+", type=int)
parser.add_argument('--pixels', help='pixels per block', type=int)
parser.add_argument('--line_color', help='line color (R G B)', type=int, nargs=3)
parser.add_argument('--line_width', help='line width (x pixels)', type=int)

args = parser.parse_args()
args.scale = int(args.thickness/args.half_cut)
args.unit = args.half_cut

assert(args.scale*args.half_cut == args.thickness)

if os.path.isdir(args.out):
    input("Confirm deleting folder at " + args.out)
    shutil.rmtree(args.out)
    os.mkdir(args.out)

if args.minecraft:
    start = np.array(args.start)
    end = np.array(args.end)
    raw_map = minecraft_utils.read_minecraft_map(args.minecraft, start, end)
    colors = minecraft_utils.block_colors
else:
    raw_map = voxel_utils.read_voxel_file(args.voxel)
    colors = {args.colors[i*4] : (args.colors[i*4+1], args.colors[i*4+2], args.colors[i*4+3]) for i in range(int(len(args.colors)/4))}

for block_id in [int(i) for i in np.unique(raw_map)]:
    if block_id not in colors.keys():
        colors[block_id] = (0,0,0)
        print("Missing color for block id " + str(block_id))

generate_layout_images(raw_map, args, colors)
pieces = get_pieces(raw_map)

cutouts=cutout_utils.get_cutouts(raw_map, args, colors, pieces)
print("Number of cutouts: " + str(len(cutouts)))
cutouts_by_sheet = cutout_utils.place_cutouts(cutouts, args)
cut_vectors = cutout_utils.get_cut_vectors(cutouts_by_sheet, args)
print("Done")
# pieces = cutout_utils.get_cutouts(raw_map, args)


# generate_cutout_files.generate_laser_cut_files(destination_path, read_map, settings)
# print("Done!")
