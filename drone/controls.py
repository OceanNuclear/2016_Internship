from panda3d.core import Vec3, NodePath
from direct.showbase.DirectObject import DirectObject


class CameraController(DirectObject):

    def __init__(self, cam, root=None, height=10, radius=1, dr=0.35, da=2):
        super().__init__()

        if root is None:
            root = base.render

        self.root = root

        self.orbit = NodePath('orbit')
        self.orbit.reparent_to(self.root)
        self.orbit.set_pos(0, 0, height)

        self.cam = cam
        cam.reparent_to(self.orbit)
        cam.set_pos(0, -radius, 0)

        self.dr = dr
        self.da = da

        self.dpos = Vec3()
        self.dhpr = Vec3()

        for e in ("arrow_up", "arrow_down", "arrow_left", "arrow_right"):
            self.accept(e, self.on_key, [e])
            self.accept("{}-up".format(e),self.on_key,["{}-up".format(e)])

        taskMgr.add(self, "update-cam")

    def on_key(self, key):
        dpos = self.dpos
        dhpr = self.dhpr

        if key in {"arrow_up", "arrow_down-up"}:
            dpos.y += self.dr

        elif key in {"arrow_down", "arrow_up-up"}:
            dpos.y -= self.dr

        elif key in {"arrow_left", "arrow_right-up"}:
            dhpr.x += self.da

        elif key in {"arrow_right", "arrow_left-up"}:
            dhpr.x -= self.da

    def __call__(self, task):
        self.cam.set_pos(self.cam.get_pos() + self.dpos)
        self.orbit.set_hpr(self.orbit.get_hpr() + self.dhpr)
        self.cam.look_at(self.root)

        return task.cont
