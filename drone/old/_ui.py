import sys
from os import chdir
from bge import logic
sys.path.append(logic.expandPath("//../../GIT/bgui"))
chdir(logic.expandPath("//"))

import bgui
import bgui.bge_utils
import bge


class Checkbox(bgui.Image):

	def __init__(self, parent, active_img, inactive_img, checked=False, *args, **kwargs):
		self._active_img = active_img
		self._inactive_img = inactive_img
		self._checked = checked

		self.on_toggled = None

		super().__init__(parent, *args, img=(active_img if checked else inactive_img), **kwargs)

	@property
	def checked(self):
		return self._checked

	@checked.setter
	def checked(self, is_checked):
		self._checked = is_checked

		self._update_state()

	def _handle_click(self):
		self.checked = not self.checked
		super()._handle_click()

	def _update_state(self):
		if self._checked:
			self.update_image(self._active_img)
		else:
			self.update_image(self._inactive_img)

		if callable(self.on_toggled):
			self.on_toggled(self)

class SimpleLayout(bgui.bge_utils.Layout):
	"""A layout showcasing various Bgui features"""

	def __init__(self, sys, data):
		super().__init__(sys, data)

		# Use a frame to store all of our widgets
		self.frame = bgui.Frame(self, border=0)
		self.frame.colors = [(0, 0, 0, 0) for i in range(4)]

		# A themed frame
		self.layout = bgui.FlowLayout(self.frame)
		self.layout.separator(0.92)

		time_layout = self.layout.row(1.0)
		time_layout.colors = [(0, 0, 0, 1) for i in range(4)]
		self.time_scrollbar = time_layout.widget(bgui.Scrollbar, name="Time", direction=bgui.BGUI_HORIZONTAL_SCROLLBAR, size=0.75, slider_size=0.05)
		#time_layout.separator(0.01)
		self.time_label = time_layout.widget(bgui.Label, name="Time Text", size=0.1, text="Time")
		time_layout.separator(0.05)
		#self.auto_advance_checkbox = time_layout.column(.1).widget(Checkbox, active_img="theme/checked.png", inactive_img="theme/box.png", size=.1, alternate_size=0.01, aspect=1)
		#self.auto_label = time_layout.widget(bgui.Label, name="Auto Text", size=0.1, text="Auto")


def init():
		# Create our system and show the mouse
	system = bgui.bge_utils.System('theme')
	system.load_layout(SimpleLayout, None)

	return system
