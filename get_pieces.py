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


def get_pieces(raw_map):
    peices = {}
    for y in range(raw_map.shape[1]):
        peices[y] = []
        flat = [[Tile(raw_map[x, y, z]) for x in range(raw_map.shape[0])] for z in range(raw_map.shape[2])]
        for x in range(raw_map.shape[0]):
            for z in range(raw_map.shape[2]):
                peice = spread(flat, x, z)
                if len(peice) > 0:
                    peices[y].append(peice)
    return peices

