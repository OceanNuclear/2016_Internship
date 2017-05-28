from argparse import ArgumentParser
from collections import namedtuple
from math import sin, cos, radians, sqrt, ceil
from os import path

from direct.showbase.ShowBase import ShowBase
from numpy import empty, uint8, float32, zeros, clip
from panda3d.core import Vec4, Vec3, BitMask32, loadPrcFileData

from controls import CameraController
from parse.event import parse_files, FIELD_KEYS
from shader import create_depth_texture, xyz_n_channel_float_texture_from_array, create_volume, setup_shader, transfer_texture_from_array
from spectrum import channel_to_energy_kev, energy_kev_to_channel

# from direct.showbase.DirectObject import DirectObject

loadPrcFileData("", "win-size 1600 900")
loadPrcFileData("", "win-origin 10 20")

# TOOD
#
# The 3D version can be assumed to account for the earth's curvature to produce realistic 3D model. If not, it can be ignored anyway
# In the case there was curvature and the model accounted for it, the volume may need to consider the impact of curvature

# Constants

ENERGY_LOWER_BOUND = channel_to_energy_kev(0)
ENERGY_UPPER_BOUND = channel_to_energy_kev(4095)
DEFAULT_WINDOW = (ENERGY_LOWER_BOUND, ENERGY_UPPER_BOUND)

RED = Vec4(1, 0, 0, 1)
BLUE = Vec4(0, 0, 1, 1)
GREEN = Vec4(0, 1, 0, 1)


LLA = namedtuple("LLA", "lat long alt")


class MissingArgToken:
    pass


def compute_world_positions(events):
    for event in events:
        latitude = event.fields['latitude']['value']
        longitude = event.fields['longitude']['value']
        altitude = event.fields['altitude']['value']
        world_pos = lla_to_ecef(LLA(latitude, longitude, altitude))
        event.fields["world_position"] = world_pos


def compute_local_positions(events, lla_origin):
    for event in events:
        event.fields['local_position'] = ecef_to_enu(lla_origin, event.fields['world_position'])


def compute_relative_positions(events, origin):
    for event in events:
        event.fields['relative_position'] = event.fields['local_position'] - origin


def compute_origin_bounding_volume_size(events):
    N = len(events)
    x_coords = empty(N)
    y_coords = empty(N)
    z_coords = empty(N)

    for i, event in enumerate(events):
        x, y, z = event.fields['local_position']

        x_coords[i] = x
        y_coords[i] = y
        z_coords[i] = z

    p_min = Vec3(x_coords.min(), y_coords.min(), z_coords.min())
    p_max = Vec3(x_coords.max(), y_coords.max(), z_coords.max())

    bounds = p_max - p_min
    origin = p_min + bounds / 2

    return {'bounds': bounds, 'origin': origin, 'min': p_min}


def calculate_voxels_volume_dimensions(cell_dimensions, bounding_dimensions):
    """Determine the required volume size to contain cells of given dimensions.

    May be larger than bounding volume if cells are not a perfect divisor of its bounds.

    Includes voxel array dimensions for volume.
    """
    voxels_dims = []
    volume_dims = []

    for x, y in zip(cell_dimensions, bounding_dimensions):
        array_dim = ceil(y/x)
        voxels_dims.append(array_dim)

        volume_dims.append(array_dim * x)

    return {'voxels': voxels_dims, 'volume': Vec3(*volume_dims)}


def parse_delimited_str(string, data_type, delimiter=':', default=MissingArgToken):
    result = []
    for element in string.split(delimiter):
        if not element:
            if default is MissingArgToken:
                raise ValueError(string)
            else:
                item = default
        else:
            item = data_type(element)
        result.append(item)
    return tuple(result)


def parse_window(window_str):
    window = DEFAULT_WINDOW
    if window_str:
        raw_window = parse_delimited_str(window_str, float, default=None)
        if raw_window:
            window = tuple(y if x is None else x for x, y in zip(raw_window, DEFAULT_WINDOW))  # Replace None with respective bounds

    return window


def create_transfer_function_array_from_function(func, samples=None):
    if samples is None:
        samples = 2

    assert samples > 1

    transfer_array = empty((samples, 4), float32)
    for i in range(samples):
        factor = i / (samples - 1)
        r, g, b, a = func(factor)
        transfer_array[i] = b, g, r, a

    return transfer_array


def compute_data_coordinates(events, vox_vol_dimensions):
    vx_sx, vx_sy, vx_sz = vox_vol_dimensions['voxels']
    vx_dx, vx_dy, vx_dz = vx_sx-1, vx_sy-1, vx_sz-1

    vo_dx, vo_dy, vo_dz = vox_vol_dimensions['volume']
    u, v, w = vx_dx / vo_dx, vx_dy / vo_dy, vx_dz / vo_dz

    present_coords = []
    for event in events:
        x, y, z = event.fields['relative_position']
        data_coord = round(x*u), round(y*v), round(z*w)

        event.fields['data_coord'] = data_coord
        present_coords.append(data_coord)

    return present_coords


def write_events_to_data(events, data, alpha, window):
    chan_min = energy_kev_to_channel(window[0])
    chan_max = energy_kev_to_channel(window[1])
    chan_slice = slice(chan_min, chan_max+1)

    cell_members = zeros(data.shape, uint8) # Assume only <255 possible resuses of a cell

    for event in events:
        coord = event.fields['data_coord']
        counts = event.spectrum[chan_slice].sum()
        interval = event.fields['live_time']

        data[coord] = counts / interval
        cell_members[coord] += 1

    mask = (cell_members != 0)
    data[mask] /= cell_members[mask]

    alpha[~mask] = 0.0
    alpha[mask] = 1

    return mask


def data_normalize_absolute(lower_bound, upper_bound, data):
    data -= lower_bound
    data /= upper_bound - lower_bound
    clip(data, 0, 1)


def data_normalize_relative(data, mask):
    data[mask] /= data[mask].ptp()


def colour_transform_blue_red(factor):
    colour = BLUE + (RED - BLUE) * factor
    f = 0.05
    colour.w = f + (1-f)*factor
    return colour


def render_events(args):
    # Get energy window
    window = parse_window(args.w)

    # Get cell dimmensions
    cell_dimensions = parse_delimited_str(args.c, float)
    assert all(x > 0 for x in cell_dimensions), "Invalid cell dimensions"

    # Take lla->ecef and then transform from ecef to local coordinate system
    file_pattern = path.join(path.dirname(__file__), args.pattern)
    print("Loading events from disk: {}".format(file_pattern))
    events = [e for e in parse_files(file_pattern) if all(n in e.fields for n in FIELD_KEYS)] # Requires all meta info

    if not events:
        raise FileNotFoundError("No events found")

    # Add coordinates (map pos)
    print("Determining world-space positions")
    compute_world_positions(events)

    print("Computing local positions")
    if args.o is None:
        first_event = min(events, key=lambda e: e.fields['prog_timestamp'])
        lla_local_origin = LLA(*[first_event.fields[n]['value'] for n in ("latitude", "longitude", "altitude")])

    else:
        lla_local_origin = LLA(*parse_delimited_str(args.o, float))

    # Re-orient and translate to local coordinate system about (0, 0, 0) according to a fixed LLA origin
    compute_local_positions(events, lla_local_origin)

    print("Finding bounding volume")
    origin_bounding_size = compute_origin_bounding_volume_size(events)

    # Compute relative position to bounding box corner
    print("Computing relative positions")
    compute_relative_positions(events, origin_bounding_size['min'])

    print("Finding true volume and array dimensions")
    vox_vol_dimensions = calculate_voxels_volume_dimensions(cell_dimensions, origin_bounding_size['bounds'])

    print("Computing data_array coordinates")
    compute_data_coordinates(events, vox_vol_dimensions)

    # Create arrays
    voxels_shape = vox_vol_dimensions['voxels']
    data_array = zeros(voxels_shape, float32)
    has_datapoint_array = zeros(data_array.shape, float32)
    transfer_array = create_transfer_function_array_from_function(colour_transform_blue_red, samples=2)

    print("Writing events to data_array in voxel shape({})".format(voxels_shape))

    mask = write_events_to_data(events, data_array, has_datapoint_array, window)
    data_normalize_relative(data_array, mask)

    return data_array, has_datapoint_array, transfer_array


def false_data(args):
    N = 200
    voxels_shape = (N, N, N)

    from itertools import product
    import numpy

    try:
        data_array = numpy.load('cache.npy')
        #raise IOError

    except IOError:
        data_array = zeros(voxels_shape, float32)
        half_n = N/2
        from math import exp
        k=6
        func = lambda x: exp(-x/N*k)
        for x, y, z in product(range(N), repeat=3):
            dx = (x - half_n)
            dy = (y - half_n)
            dz = (z - half_n)

            rad = (dx**2 + dy**2 + dz**2) ** 0.5
            value = func(rad)
            data_array[x, y, z] = value

        numpy.save('cache.npy', data_array)

    has_datapoint_array = zeros(data_array.shape, float32)
    transfer_array = create_transfer_function_array_from_function(colour_transform_blue_red, samples=200)

    has_datapoint_array[:,:,:N//2] = 1
    has_datapoint_array[:,:N//2,:] = 1

    return data_array, has_datapoint_array, transfer_array


def spider_data(args):
    from parse.spiderweb import parse_files, direction_to_rad
    from collections import defaultdict

    results = list(parse_files("false_data"))

    pos_to_data = defaultdict(list)

    for result in results:
        direction = result.fields['direction']
        height = result.fields['height']

        if direction == 'C':
            pos = 0, 0, height

        else:
            length = result.fields['length']
            angle = direction_to_rad[direction]

            x = cos(angle) * length
            y = sin(angle) * length
            pos = x, y, height

        pos_to_data[pos].append(result.spectrum)

    x_co, y_co, z_co = zip(*pos_to_data.keys())

    x_bound = max(x_co)
    y_bound = max(y_co)
    z_bound = max(z_co)

    N = 50

    from numpy import meshgrid, linspace, dstack, vstack, asarray, array

    x = linspace(-x_bound, x_bound, N)
    y = linspace(-y_bound, y_bound, N)
    z = linspace(-z_bound, z_bound, N)

    gx, gy, gz = meshgrid(x, y, z)

    def mean(x):
        return sum(x) / len(x)

    p2v = {k: mean([sum(a) for a in v]) for k, v in pos_to_data.items()}

    from scipy.interpolate import griddata
    keys, values = zip(*p2v.items())
    keys_array = asarray(keys)
    values_array = array(values)

    grid = griddata(keys_array, values_array, (gx, gy, gz))

    from numpy import isnan, where

    voxels_shape = (N, N, N)
    data_array = grid.astype(float32)# zeros(voxels_shape, float32)

    has_datapoint_array = zeros(data_array.shape, float32)
    transfer_array = create_transfer_function_array_from_function(colour_transform_blue_red, samples=200)

    has_datapoint_array[:] = ~isnan(data_array)
   # has_datapoint_array[:,:,44:] = 0
 #   print(data_array[where(data_array != 0)])
    # has_datapoint_array[:,:,:N//2] = 1
    # has_datapoint_array[:,:N//2,:] = 1
    # from numpy import nan_to_num
    # data_array = nan_to_num(data_array)
  #  print((data_array == 0).sum())
    return data_array, has_datapoint_array, transfer_array


if __name__ == "__main__":
    parser = ArgumentParser(description="Volumetric data_array visualiser")
    parser.add_argument("pattern", type=str, help="Event file pattern (e.g 'events/record*.txt')")
    parser.add_argument("c", type=str, help="Cell size (x, y, z bin size)")
    parser.add_argument("-w", metavar="l:u", type=str, help="Energy window, colon separating upper and lower bounds")
    parser.add_argument("-o", metavar="lat:lon:alt", type=str, help="LLA coordinate to use as local coordinate system origin (default choose random point)")
    parser.add_argument("-a", metavar="1", default=1.0, type=float, help="Height of the viewer")
    args = parser.parse_args()


    #data_array, has_data_array, transfer_array = render_events(args)
    #data_array, has_data_array, transfer_array = false_data(args)
    data_array, has_data_array, transfer_array = spider_data(args)

    base = ShowBase()

    h = 1

    def tsk(task):
        ind = round(task.time *49 / 5)
        from numpy import isnan, where
        has_data_array[:] = ~isnan(data_array)
        has_data_array[:,:,:ind] = 0
        has_data_array[:,:,ind+h:] = 0
        from panda3d.core import PTAUchar
        print(ind)
        alpha_tex.set_ram_image(PTAUchar(has_data_array.tostring()))
        return task.cont

    taskMgr.add(tsk, "TASK")

    camera_render_mask = BitMask32(4)
    depth = create_depth_texture(camera_render_mask)

    # Volume is 2x2x2, with mask of camera_render_mask (ignored by depth tex cam)
    volume_nodepath = create_volume(camera_render_mask)

    data_tex = xyz_n_channel_float_texture_from_array(data_array, linear=True)
    transfer_tex = transfer_texture_from_array(transfer_array)
    alpha_tex = xyz_n_channel_float_texture_from_array(has_data_array, linear=True)
    setup_shader(volume_nodepath, data_tex, alpha_tex, transfer_tex, depth, (1, 0, 0))

    # Camera controller (LEFT, RIGHT, UP, DOWN)

    root = render.attach_new_node('view_root')
    root.set_pos(0, 0, 0)

    controller = CameraController(base.cam, root=root, height=args.a, radius=5)
    axis = loader.loadModel("models/zup-axis")
    axis.reparent_to(render)
    axis.set_scale(0.1  )



    base.run()
