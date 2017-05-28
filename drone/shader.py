from panda3d.core import PointLight, Shader, loadPrcFileData, GeomVertexFormat, GeomPoints, GeomVertexData, \
    GeomVertexWriter, Geom, GeomNode, TransparencyAttrib, Texture, GraphicsPipe, GraphicsOutput, FrameBufferProperties, WindowProperties,\
    BitMask32, AlphaTestAttrib, PTAUchar, ColorBlendAttrib, PTADouble, CPTADouble

loadPrcFileData("", "view-frustum-cull 0")
loadPrcFileData("", "pstats-gpu-timing 1")
#loadPrcFileData("", "want-pstats 1")


def create_depth_texture(mask):
    window_props = WindowProperties.size(1024, 1024)
    props = FrameBufferProperties()
    props.setRgbColor(1)
    props.setAlphaBits(1)
    props.setDepthBits(1)
    output = base.graphicsEngine.makeOutput(base.pipe, "offscreen buffer", -2, props, window_props,
                                            GraphicsPipe.BFRefuseWindow, base.win.getGsg(), base.win)

    depth_tex = Texture()
    output.addRenderTexture(depth_tex, GraphicsOutput.RTMBindOrCopy, GraphicsOutput.RTPDepth)
    depth_tex.setWrapU(Texture.WMClamp)
    depth_tex.setWrapV(Texture.WMClamp)
    # Render depth
    buffer_camera = base.makeCamera(output) # Force it to be rendered
    buffer_camera.node().set_camera_mask(mask) # Only render certain objects (not volume)

    # Copy camera properties and parent to base.cam
    buffer_camera.reparent_to(base.cam)
    buffer_camera.node().set_lens(base.cam.node().get_lens())

    return depth_tex


def create_volume(depth_mask):
    """Volume space is (0, 0, 0) to +- (1, 1, 1)"""
    # Create single vertex nodepath
    format = GeomVertexFormat.getV3()
    vdata = GeomVertexData("vertices", format, Geom.UHStatic)
    vdata.setNumRows(1)

    vertex_writer = GeomVertexWriter(vdata, "vertex")
    vertex_writer.addData3f(0, 0, 0)

    points = GeomPoints(Geom.UHStatic)
    points.addVertex(0)
    points.close_primitive()

    points_geom = Geom(vdata)
    points_geom.add_primitive(points)

    points_node = GeomNode("points")
    points_node.addGeom(points_geom)
    nodepath = base.render.attachNewNode(points_node)

    nodepath.set_transparency(TransparencyAttrib.M_alpha)
    nodepath.set_attrib(AlphaTestAttrib.make(AlphaTestAttrib.M_none, 0), 10)
    nodepath.hide(depth_mask)

    return nodepath


def transfer_texture_from_array(arr):
    tex = Texture()
    n = arr.shape[0]
    tex.setup_1d_texture(n, Texture.TFloat, Texture.FRgba)
    tex.set_ram_image(PTAUchar(arr.tostring()))

    tex.set_wrap_u(Texture.WMClamp)
    tex.set_wrap_v(Texture.WMClamp)

    filter = Texture.FTLinear
    tex.set_minfilter(filter)
    tex.set_magfilter(filter)

    return tex


def xyz_n_channel_float_texture_from_array(arr, linear=False):
    """Uses minimum amount of data_array to store texture"""
    tex = Texture()
    if len(arr.shape) == 3:
        nz, ny, nx = arr.shape
        nv = 1

    else:
        nz, ny, nx, nv = arr.shape[:4] # Data is fed in in xyz format, which is opposite to expected zyx, so reverse dimensions here

    assert 0 < nv <= 4

    formats = {1: Texture.FRed, 2: Texture.FRgb, 3: Texture.FRgb, 4: Texture.FRgba}

    tex.setup_3d_texture(nx, ny, nz, Texture.TFloat, formats[nv])
    tex.set_ram_image(PTAUchar(arr.tostring()))

    tex.setWrapU(Texture.WMClamp)
    tex.setWrapV(Texture.WMClamp)

    filter = Texture.FTLinear if linear else Texture.FTNearest
    tex.set_minfilter(filter)
    tex.set_magfilter(filter)

    return tex


def setup_shader(nodepath, data_tex, alpha_tex, transfer_tex, depth_tex, light_pos):
    shader = Shader.load(Shader.SL_GLSL, vertex="shader.vert", fragment="shader.frag", geometry="shader.geom")
    nodepath.set_shader(shader)

    nodepath.set_shader_input("data_tex", data_tex)
    nodepath.set_shader_input("alpha_tex", alpha_tex)
    nodepath.set_shader_input("depth_tex", depth_tex)
    nodepath.set_shader_input("transfer_tex", transfer_tex)
    nodepath.set_shader_input("focal_length", base.cam.node().getLens().get_focal_length())
    nodepath.set_shader_input("absorption", 1)
    nodepath.set_shader_input("light_pos", light_pos)
    nodepath.set_shader_input("light_intensity", (15, 15, 15))

    def update_inputs(task):
        nodepath.set_shader_input("window_size", (base.win.get_x_size(), base.win.get_y_size()))
        return task.cont

    taskMgr.add(update_inputs, "update_inputs")
    nodepath.set_shader_input("window_size", (base.win.get_x_size(), base.win.get_y_size()))



def create_density_texture():
    # tex = loader.load3DTexture("tex/texlayer#.png")
    #
    # wrap = Texture.WM_border_color
    # tex.set_wrap_u(wrap)
    # tex.set_wrap_v(wrap)
    # tex.set_wrap_w(wrap)

    from numpy import empty,uint8
    from itertools import product
    from noise import snoise3, pnoise3
    from math import sqrt

    n = 128
    r = 0.25

    cache_path = "cache.dat"
    import sys

    def print_progressbar(iteration, total, prefix = '', suffix = '', decimals = 2, bar_length = 100):
        filledLength = int(round(bar_length * iteration / float(total)))
        percents = round(100.00 * (iteration / float(total)), decimals)
        bar = '█' * filledLength + '-' * (bar_length - filledLength)
        sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
        sys.stdout.flush()
        if iteration == total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    try:
        with open(cache_path, "rb") as f:
            data = f.read()

    except FileNotFoundError:
        from numpy import zeros
        arr = zeros((n, n, n, 4), uint8)

        frequency = 3.0 / n
        center = n / 2.0 + 0.5
        from panda3d.core import Vec3

        f = lambda p: round(p*255)

        for x, y, z in product(range(n), range(n), range(n)):
            dx = center-x
            dy = center-y
            dz = center-z

            off = abs(pnoise3(x*frequency, y*frequency, z*frequency, 5, 0.5))

            d = sqrt(dx*dx+dy*dy+dz*dz)/(n)
            alpha = 30 if ((d-off) < r) else 0

            col = Vec3(x, y, z)
            col.normalize()

            cr = f(col.x)
            cg = f(col.y)
            cb = f(col.z)

            arr[z][y][x] = (cb, cg, cr, alpha)

            if (y == 0):
                print_progressbar(x, n)

        data = arr.tostring()

        with open(cache_path, "wb") as f:
            f.write(data)

    tex = Texture()

    tex.setup_3d_texture(n, n, n, Texture.T_unsigned_byte, Texture.FRgba)
    tex.setWrapU(Texture.WMClamp)
    tex.setWrapV(Texture.WMClamp)

    filter = Texture.FT_linear
    tex.set_minfilter(filter)
    tex.set_magfilter(filter)

    tex.setRamImage(PTAUchar(data))
    return tex

