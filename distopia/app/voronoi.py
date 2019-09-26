"""
Voronoi Kivy App
===================

Runs the voronoi GUI app.
"""

from kivy.support import install_twisted_reactor

install_twisted_reactor()

from itertools import cycle, product
import logging
import os
import numpy as np
import json
import csv
import math
from functools import cmp_to_key
from argparse import ArgumentParser

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.app import App
from kivy.graphics.vertex_instructions import Line, Point, Mesh, Ellipse, \
    Rectangle
from kivy.graphics.tesselator import Tesselator, WINDING_ODD, TYPE_POLYGONS
from kivy.graphics import Color
import matplotlib.pyplot as plt
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import Metrics, dp
from kivy.properties import NumericProperty
from kivy.graphics.context_instructions import \
    PushMatrix, PopMatrix, Rotate, Translate, Scale, MatrixInstruction
from kivy.uix.spinner import Spinner
from kivy.uix.scatter import Scatter
from kivy.resources import resource_find, resource_add_path

import distopia
from distopia.app.voronoi_data import GeoDataCounty, GeoDataPrecinct2017
from distopia.precinct import Precinct
from distopia.mapping.voronoi import VoronoiMapping
from distopia.app.ros import RosBridge
from distopia.app.tasks import TaskSwitcher

__all__ = ('VoronoiWidget', 'VoronoiApp')


class VoronoiWidget(Widget):
    """The widget through which we interact with the precincts and districts.
    """

    voronoi_mapping = None

    fiducial_graphics = {}

    district_graphics = []

    precinct_graphics = {}

    colors = []

    fiducials_color = {}

    table_mode = False

    align_mat = None

    screen_offset = 0, 0

    touches = {}

    ros_bridge = None

    district_blocks_fid = []

    focus_block_fid = 8

    focus_block_logical_id = 8

    _has_focus = False

    district_metrics_fn = None

    state_metrics_fn = None

    show_voronoi_boundaries = False

    current_fid_id = None

    focus_gui_pos = None

    focus_metrics = []

    focus_metric_width = 100

    focus_metric_height = 100

    screen_size = (1920, 1080)

    focus_region_width = 0

    n_focus_rows = 0

    n_focus_cols = 0

    gui_touch_focus_buttons = None

    current_focus_metric = ''

    max_fiducials_per_district = 5

    visualize_metric_data = True

    task_arr = None

    task_features = ['population', 'pvi', 'compactness']

    task_description = StringProperty("Welcome to Distopia.\n\nPlease place 8 district markers on the map.\n\nWhen you are ready, hit 'New Task'.\n\n")

    task_time = NumericProperty(0)

    task_timer = None

    task_time_str = StringProperty('delete this')

    def __init__(
            self, voronoi_mapping=None, table_mode=False, align_mat=None,
            screen_offset=(0, 0), ros_bridge=None, district_blocks_fid=None,
            focus_block_fid=0, focus_block_logical_id=0, district_metrics_fn=None,
            state_metrics_fn=None,
            show_voronoi_boundaries=False, focus_metrics=[],
            focus_metric_width=100, focus_metric_height=100,
            screen_size=(1920, 1080), max_fiducials_per_district=5,
            visualize_metric_data=True, task_start=0, task_seed=0, **kwargs):
        super(VoronoiWidget, self).__init__(**kwargs)
        self.voronoi_mapping = voronoi_mapping
        self.ros_bridge = ros_bridge
        self.district_blocks_fid = district_blocks_fid
        self.focus_block_fid = focus_block_fid
        self.focus_block_logical_id = focus_block_logical_id
        self.show_voronoi_boundaries = show_voronoi_boundaries
        self.max_fiducials_per_district = max_fiducials_per_district
        self.visualize_metric_data = visualize_metric_data

        self.focus_metrics = focus_metrics
        self.focus_metric_width = focus_metric_width
        self.focus_metric_height = focus_metric_height
        self.screen_size = screen_size
        self.n_focus_rows = rows = int(screen_size[1] // focus_metric_height)
        self.n_focus_cols = cols = int(math.ceil(len(focus_metrics) / rows))
        self.focus_region_width = cols * focus_metric_width
        self.show_district_selection()
        self.show_focus_region()

        self.fiducial_graphics = {}
        self.fiducials_color = {}
        self.colors = cycle(plt.get_cmap('tab10').colors)

        self.table_mode = table_mode
        self.align_mat = align_mat
        self.district_graphics = []
        self.district_metrics_fn = district_metrics_fn
        self.state_metrics_fn = state_metrics_fn
        self.screen_offset = screen_offset
        self.touches = {}

        with self.canvas.before:
            PushMatrix()
            Translate(*[v * Metrics.density for v in screen_offset])
        with self.canvas.after:
            PopMatrix()
        self.task_header = Label(text="Your Task (intro):", halign="left", font_size='40sp', x=1300, y=550)
        with self.canvas:
            self.task_container = Line(points=(1100,550,1700,550,1700,400,1100,400,1100,550))
        self.task_counter = 0
        self.task_generator = self.generate_tasks(3, start_idx = task_start, seed = task_seed)
        self.task_box = Label(text=self.task_description, halign="left", valign="top", font_size='20sp', x=1350, y=400)
        self.task_timer_clock = Label(text=self.task_time_str, halign="left", font_size='20sp', x=1300, y=225)
        self.reset_task_timer_button = Button(text="Reset Timer",x=1250,y=200, size_hint=(None,None),size=(100,50))
        #self.reset_task_timer_button.bind(on_press=self.reset_task_timer)
        self.advance_task_button = Button(text="New Task",x=1350,y=200, size_hint=(None,None),size=(100,50))
        #self.advance_task_button.bind(on_press=self.update_task)

        self.add_widget(self.task_header)
        self.add_widget(self.task_box)
        self.add_widget(self.task_timer_clock)
        self.add_widget(self.advance_task_button)
        self.add_widget(self.reset_task_timer_button)
        self.show_precincts()
        self.task_switcher = TaskSwitcher(self.task_features)
        # self.task_timer = Clock.create_trigger(self.update_task, 60 * 5)
        self.reset_task_timer()
        self.task_clock = Clock.schedule_interval(self.update_task_clock, 1)

    def advance_task_press(self):
        self.update_task(None)
        self.advance_task_button.trigger_action()

    def advance_task_release(self):
        self.advance_task_button.on_release()

    def reset_task_press(self):
        self.reset_task_timer()
        self.reset_task_timer_button.trigger_action()

    def reset_task_release(self):
        self.reset_task_timer_button.on_release()

    def update_task_clock(self, dt):
        self.task_time -= 1
        self.task_timer_clock.text = "Time Remaining: {} s".format(self.task_time)

    def reset_task_timer(self, set_time=60*5):
        if self.task_timer is not None:
            self.task_timer.cancel()
        self.task_timer = Clock.create_trigger(self.update_task, set_time)
        self.task_time = set_time
        self.task_timer()

    def generate_tasks(self, n_features, task_list=None, start_idx=0, seed=0):
        self.task_start_idx = start_idx
        self.task_seed = seed
        if task_list is None:
            # generate a new set of tasks using n_features
            task_pool = [[-1.,0.,1.] for feature in range(n_features)]
            task_list = list(product(*task_pool))
            task_list = [list(task) for task in task_list[start_idx:] if not np.array_equal(task, np.zeros(3))]
            if seed > 0:
                np.random.seed(seed)
                np.random.shuffle(task_list)
            logging.info("N_Tasks: {}".format(len(task_list)))
            logging.info(task_list)
        while len(task_list) > 0:
            yield task_list.pop(0) # pop from the head so the start index makes sense
        while True:
            yield [0.0, 0.0, 0.0]

    def update_task(self, dt):
        logging.info("updating")
        max_n_tasks = 3
        # self.task_arr = [np.random.choice([-1.0, 0.0, 1.0]) for i in range(len(self.task_features))]
        self.task_arr = next(self.task_generator)
        # choose two indices to zero out; this will keep the tasks <= 3
        # n_nonzeroes = np.linalg.norm(self.task_arr, 1)  # number of nonzero indices
        # if n_nonzeroes == 0:
        #     # don't allow empty tasks
        #     idx = np.random.randint(len(self.task_arr))
        #     self.task_arr[idx] = np.random.choice([-1.0, 1.0])
        # else:
        #     n_to_zero = int(n_nonzeroes - max_n_tasks)
        #     if n_to_zero > 0:
        #         zero_indices = np.random.choice(len(self.task_arr), 5-max_n_tasks, replace=False)
        #         for zi in zero_indices:
        #             self.task_arr[zi] = 0.0
        # self.task_arr = [-1.0, 0.0, 0.0, 0.0, 0.0]
        logging.info("next task: {}".format(self.task_arr))
        self.task_description = self.task_switcher.get_task_text(self.task_arr)
        self.task_header.text = "Your Task (idx:{} seed:{}):".format(self.task_start_idx + self.task_counter, self.task_seed)
        self.task_box.text = self.task_description
        self.task_counter += 1
        if self.ros_bridge is not None:
            self.ros_bridge.update_task(self.task_arr)
        self.reset_task_timer()

    def show_district_selection(self):
        if not self.table_mode:
            h = 34 * len(self.district_blocks_fid) + 5 * (
                    len(self.district_blocks_fid) - 1)
            box = self.gui_touch_focus_buttons = BoxLayout(
                orientation='vertical', size=(dp(100), dp(h)),
                spacing=dp(5), pos=(self.focus_region_width, 0))

            for i, val in enumerate(self.district_blocks_fid):
                btn = ToggleButton(
                    text='District {}'.format(i + 1), group='focus',
                    allow_no_selection=False)
                box.add_widget(btn)

                def update_current_fid(*largs, button=btn, value=val):
                    if button.state == 'down':
                        self.current_fid_id = value

                btn.fbind('state', update_current_fid)
            box.children[-1].state = 'down'
            self.add_widget(box)

    def show_focus_region(self):
        focus_metrics = self.focus_metrics
        if not focus_metrics:
            return

        if not self.table_mode:
            btn = ToggleButton(
                text='Focus', group='focus', allow_no_selection=False)
            self.gui_touch_focus_buttons.add_widget(btn)

            def update_current_fid(*largs, button=btn):
                if button.state == 'down':
                    self.current_fid_id = self.focus_block_logical_id

            btn.fbind('state', update_current_fid)

        i = 0
        focus_metric_width = self.focus_metric_width
        focus_metric_height = self.focus_metric_height
        for col in range(self.n_focus_cols):
            for row in range(self.n_focus_rows):
                name = focus_metrics[i]
                x0 = col * focus_metric_width
                x1 = x0 + focus_metric_width
                y0 = row * focus_metric_height
                y1 = y0 + focus_metric_height

                self.add_widget(
                    Factory.SizedLabel(text=name, pos=(x0, y0)))
                with self.canvas:
                    Line(points=[x0, y0, x1, y0, x1, y1, x0, y1], width=2)

                i += 1
                if i >= len(focus_metrics):
                    break
            if i >= len(focus_metrics):
                break

    def show_precincts(self):
        precinct_graphics = self.precinct_graphics = {}
        with self.canvas:
            PushMatrix()
            Translate(self.focus_region_width, 0)
            Scale(Metrics.density)
            for precinct in self.voronoi_mapping.precincts:
                assert len(precinct.boundary) >= 6
                tess = Tesselator()
                tess.add_contour(precinct.boundary)
                tess.tesselate(WINDING_ODD, TYPE_POLYGONS)

                graphics = [
                    Color(rgba=(0, 0, 0, 1))]
                for vertices, indices in tess.meshes:
                    graphics.append(
                        Mesh(
                            vertices=vertices, indices=indices,
                            mode="triangle_fan"))

                graphics.append(Color(rgba=(0, 1, 0, 1)))
                graphics.append(Line(points=precinct.boundary, width=1))
                precinct_graphics[precinct] = graphics
            PopMatrix()

    def on_touch_down(self, touch):
        if not self.table_mode:
            if self.gui_touch_focus_buttons.collide_point(*touch.pos):
                return self.gui_touch_focus_buttons.on_touch_down(touch)
            elif self.advance_task_button.collide_point(*touch.pos):
                return self.advance_task_press()
            elif self.reset_task_timer_button.collide_point(*touch.pos):
                return self.reset_task_press()
            return self.gui_touch_down(touch)
        return self.fiducial_down(touch)

    def on_touch_move(self, touch):
        if not self.table_mode:
            if self.gui_touch_focus_buttons.collide_point(*touch.pos):
                return self.gui_touch_focus_buttons.on_touch_down(touch)
            elif self.advance_task_button.collide_point(*touch.pos):
                return
            elif self.reset_task_timer_button.collide_point(*touch.pos):
                return

        if touch.uid not in self.touches:
            return False

        if self.table_mode:
            return self.fiducial_move(touch)
        return self.gui_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.table_mode:
            if self.gui_touch_focus_buttons.collide_point(*touch.pos):
                return self.gui_touch_focus_buttons.on_touch_down(touch)
            elif self.advance_task_button.collide_point(*touch.pos):
                return
            elif self.reset_task_timer_button.collide_point(*touch.pos):
                return
        if touch.uid not in self.touches:
            return False

        if self.table_mode:
            return self.fiducial_up(touch)
        return self.gui_touch_up(touch)

    def align_touch(self, pos):
        if self.align_mat is not None:
            pos = tuple(
                np.dot(self.align_mat, np.array([pos[0], pos[1], 1]))[:2])

        x0, y0 = self.screen_offset
        pos = pos[0] - x0, pos[1] - y0
        return pos

    def handle_focus_block(self, pos):
        assert self.focus_metrics

        if pos is None:
            self.current_focus_metric = ''
            if self.visualize_metric_data:
                self.paint_precinct_by_district(clear_error=False)
            if self.ros_bridge is not None:
                self.ros_bridge.update_tuio_focus(False, '')
            return

        x, y = pos
        x_ = (x - self.focus_region_width) / Metrics.density
        y_ = y / Metrics.density
        if x < self.focus_region_width:
            rows = self.n_focus_rows

            metric = ''
            if y < len(self.focus_metrics) * self.focus_metric_height:
                row = int(y / self.focus_metric_height)
                col = int(x / self.focus_metric_width)
                metric = self.focus_metrics[col * rows + row]

            self.current_focus_metric = metric
            if self.visualize_metric_data:
                if metric:
                    self.paint_precinct_by_metric()
                else:
                    self.paint_precinct_by_district(clear_error=False)

            if self.ros_bridge is not None:
                self.ros_bridge.update_tuio_focus(False, metric)
        else:
            self.current_focus_metric = ''
            if self.visualize_metric_data:
                self.paint_precinct_by_district(clear_error=False)

            try:
                district = self.voronoi_mapping.get_pos_district(
                    (x_, y_))
            except (IndexError, TypeError):
                district = None

            if self.ros_bridge is not None:
                # it's not on any district, send a no block present signal
                if district is None:
                    self.ros_bridge.update_tuio_focus(False, '')
                else:
                    self.ros_bridge.update_tuio_focus(True, district.identity)

    def focus_block_down(self, touch, pos):
        # there's already a focus block on the table
        if self._has_focus or not self.focus_metrics:
            return True
        self._has_focus = touch

        with self.canvas:
            color = Color(rgba=(1, 0, 1, 1))
            point = Point(points=pos, pointsize=7)

        info = {'fid': touch.fid, 'last_pos': pos, 'graphics': (color, point),
                'focus': True}
        self.touches[touch.uid] = info

        self.handle_focus_block(pos)
        return True

    def focus_block_move(self, touch, pos):
        """Only called in table mode and if the touch has been seen before
        and it is a focus block.
        """
        assert self.focus_metrics
        info = self.touches[touch.uid]
        info['last_pos'] = pos
        info['graphics'][1].points = pos

        self.handle_focus_block(pos)
        return True

    def focus_block_up(self, touch):
        """Only called in table mode and if the touch has been seen before
        and it is a focus block.
        """
        assert self.focus_metrics
        info = self.touches[touch.uid]
        for item in info['graphics']:
            self.canvas.remove(item)

        del self.touches[touch.uid]
        self._has_focus = None

        self.handle_focus_block(None)
        return True

    def fiducial_down(self, touch):
        focus_id = self.focus_block_logical_id
        blocks_fid = self.district_blocks_fid
        if 'markerid' not in touch.profile or (
                touch.fid not in blocks_fid and touch.fid != focus_id):
            return False

        x, y = pos = self.align_touch(touch.pos)

        # handle focus block
        if touch.fid == focus_id:
            return self.focus_block_down(touch, pos)
        if x < self.focus_region_width:
            return True

        with self.canvas:
            color = Color(rgba=(1, 1, 1, 1))
            point = Point(points=pos, pointsize=7)

        logical_id = blocks_fid.index(touch.fid)
        key = self.add_fiducial((x - self.focus_region_width, y), logical_id)

        info = {'fid': touch.fid, 'fiducial_key': key, 'last_pos': pos,
                'graphics': (color, point), 'logical_id': logical_id}
        self.touches[touch.uid] = info

        self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def fiducial_move(self, touch):
        """Only called in table mode and if the touch has been seen before.
        """
        info = self.touches[touch.uid]
        x, y = pos = self.align_touch(touch.pos)
        if info['last_pos'] == pos:
            return True

        if 'focus' in info:
            return self.focus_block_move(touch, pos)

        info['last_pos'] = pos
        info['graphics'][1].points = pos

        self.voronoi_mapping.move_fiducial(
            info['fiducial_key'], (x - self.focus_region_width, y))
        self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def fiducial_up(self, touch):
        """Only called in table mode and if the touch has been seen before.
        """
        info = self.touches[touch.uid]
        if 'focus' in info:
            return self.focus_block_up(touch)

        del self.touches[touch.uid]
        for item in info['graphics']:
            self.canvas.remove(item)

        x, y = self.align_touch(touch.pos)
        self.remove_fiducial(
            info['fiducial_key'], (x - self.focus_region_width, y))
        self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def gui_touch_down(self, touch):
        x, y = pos = self.align_touch(touch.pos)
        info = {'moved': False, 'fiducial_key': None}

        # are we near a voronoi touch?
        x_ = (x - self.focus_region_width) / Metrics.density
        y_ = y / Metrics.density
        for key, (x2, y2) in self.voronoi_mapping.get_fiducials().items():
            if ((x_ - x2) ** 2 + (y_ - y2) ** 2) ** .5 < 10:
                info['fiducial_key'] = key
                self.touches[touch.uid] = info
                return True

        # are we near the focus touch?
        if self.focus_gui_pos:
            assert self.focus_metrics
            x2, y2 = self.focus_gui_pos
            if ((x - x2) ** 2 + (y - y2) ** 2) ** .5 < 10:
                info['focus'] = True
                self.touches[touch.uid] = info
                return True

        # handle focus down
        if self.current_fid_id is self.focus_block_logical_id:
            if self.focus_gui_pos or not self.focus_metrics:
                return True
            self.focus_gui_pos = pos

            with self.canvas:
                color = Color(rgba=(1, 0, 1, 1))
                point = Point(points=pos, pointsize=7)
            self.fiducial_graphics['focus'] = color, point
            info['focus'] = True
            info['moved'] = True

            self.touches[touch.uid] = info
            self.handle_focus_block(pos)
            return True

        if x_ < 0:
            return True

        # with self.canvas:
        #     color = Color(rgba=(1, 1, 1, 1))
        #     point = Point(points=pos, pointsize=7)

        current_id = self.current_fid_id
        if len(
                [1 for val in self.voronoi_mapping.get_fiducial_ids().values()
                 if val == current_id]) >= self.max_fiducials_per_district:
            return True

        key = self.add_fiducial((x_, y_), current_id)

        label = self.fiducial_graphics[key] = Label(
            text=str(self.current_fid_id + 1),
            center=tuple(map(float, pos)),
            font_size='20dp')
        self.add_widget(label)
        info['fiducial_key'] = key
        info['moved'] = True
        self.touches[touch.uid] = info

        self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def gui_touch_move(self, touch):
        """Only called when not in table mode and if the touch has been seen
        before.
        """
        x, y = pos = self.align_touch(touch.pos)
        x_ = (x - self.focus_region_width) / Metrics.density
        y_ = y / Metrics.density
        info = self.touches[touch.uid]
        info['moved'] = True

        if 'focus' in info:
            if self.focus_gui_pos != pos:
                self.handle_focus_block(pos)
            self.focus_gui_pos = self.fiducial_graphics['focus'][1].points = pos
            return True

        key = info['fiducial_key']
        pos_ = (x_, y_)
        if self.voronoi_mapping.get_fiducials()[key] != pos_:
            self.fiducial_graphics[key].center = tuple(map(float, pos))
            self.voronoi_mapping.move_fiducial(key, pos_)
            self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def gui_touch_up(self, touch):
        """Only called when not in table mode and if the touch has been seen
        before.
        """
        x, y = pos = self.align_touch(touch.pos)
        x_ = (x - self.focus_region_width) / Metrics.density
        y_ = y / Metrics.density

        info = self.touches.pop(touch.uid)
        if 'focus' in info:
            # if moved, we leave point on gui
            if info['moved']:
                if self.focus_gui_pos != pos:
                    self.handle_focus_block(pos)
                self.focus_gui_pos = self.fiducial_graphics['focus'][1].points = pos
                return True
            # if it didn't move, we remove the point
            for item in self.fiducial_graphics['focus']:
                self.canvas.remove(item)
            del self.fiducial_graphics['focus']

            self.focus_gui_pos = None
            self.handle_focus_block(None)
            return True

        key = info['fiducial_key']
        pos_ = (x_, y_)
        if info['moved']:
            if self.voronoi_mapping.get_fiducials()[key] != pos_:
                self.fiducial_graphics[key].center = tuple(map(float, pos))
                self.voronoi_mapping.move_fiducial(key, pos_)
                self.voronoi_mapping.request_reassignment(self.voronoi_callback)
            return True

        self.remove_widget(self.fiducial_graphics[key])
        # for item in self.fiducial_graphics[key]:
        #     self.canvas.remove(item)
        del self.fiducial_graphics[key]

        self.remove_fiducial(key, pos_)
        self.voronoi_mapping.request_reassignment(self.voronoi_callback)
        return True

    def add_fiducial(self, location, identity):
        fiducial = self.voronoi_mapping.add_fiducial(location, identity)
        if identity not in self.fiducials_color:
            self.fiducials_color[identity] = list(next(self.colors))
        return fiducial

    def remove_fiducial(self, fiducial, location):
        self.voronoi_mapping.remove_fiducial(fiducial)

    def voronoi_callback(self, *largs):
        def _callback(dt):
            self.process_voronoi_output(*largs)

        Clock.schedule_once(_callback)

    def clear_voronoi(self):
        for graphics in self.precinct_graphics.values():
            graphics[0].rgba = 0, 0, 0, 1

        for item in self.district_graphics:
            self.canvas.remove(item)
        self.district_graphics = []

    def paint_precinct_by_district(self, clear_error=True):
        colors = self.fiducials_color
        if not self.voronoi_mapping.districts:
            if clear_error:
                for graphics in self.precinct_graphics.values():
                    graphics[0].rgba = 0, 0, 0, 1
            else:
                for graphics in self.precinct_graphics.values():
                    graphics[0].rgba = 0, 0, 0, graphics[0].a
            return

        for district in self.voronoi_mapping.districts:
            color = colors[district.identity]
            for precinct in district.precincts:
                p_color = self.precinct_graphics[precinct][0]
                if clear_error:
                    p_color.rgba = color + [1., ]
                else:
                    p_color.rgba = color + [p_color.a]

    def paint_precinct_by_metric(self):
        metric_name = self.current_focus_metric
        assert metric_name
        assert self.visualize_metric_data
        metrics = [
            precinct.metrics[metric_name].scalar_value for
            precinct in self.voronoi_mapping.precincts]
        min_ = min(metrics)
        range_ = max(metrics) - min_

        graphics = self.precinct_graphics
        for precinct, metric in zip(self.voronoi_mapping.precincts, metrics):
            val = (metric - min_) / range_
            color = graphics[precinct][0]
            color.rgba = 0, val * .333 + .176, val * .314 + .392, color.a

    def process_voronoi_output(
            self, districts, fiducial_identity, fiducial_pos, error=[],
            post_callback=None, largs=(),
            data_is_old=False):
        if data_is_old:
            return

        if post_callback is not None:
            post_callback(*largs)

        if not error:
            fid_ids = [self.district_blocks_fid[i] for i in fiducial_identity]
            if self.ros_bridge is not None:
                self.ros_bridge.update_voronoi(
                    fiducial_pos, fid_ids, fiducial_identity, districts,
                    self.district_metrics_fn, self.state_metrics_fn)

        if self.visualize_metric_data and self.current_focus_metric:
            for graphics in self.precinct_graphics.values():
                graphics[0].a = 1.  # undo possible previous error display
        else:
            if not districts:
                self.clear_voronoi()
            else:
                self.paint_precinct_by_district()

        if error:
            for precinct in error:
                self.precinct_graphics[precinct][0].a = 0

        for item in self.district_graphics:
            self.canvas.remove(item)
        self.district_graphics = []

        if self.show_voronoi_boundaries:
            with self.canvas:
                PushMatrix()
                Translate(self.focus_region_width, 0)
                Scale(Metrics.density)
                self.district_graphics.append(Color(1, 1, 0, 1))
                for district in districts:
                    if not district.boundary:
                        continue

                    self.district_graphics.append(
                        Line(points=district.boundary + district.boundary[:2],
                             width=2))
                PopMatrix()


class VoronoiApp(App):
    """The Kivy application that creates the GUI.
    """

    voronoi_mapping = None

    ros_bridge = None

    use_county_dataset = True

    geo_data = None

    precincts = []

    screen_size = (1900, 800)

    table_mode = False

    alignment_filename = 'alignment.txt'

    screen_offset = 0, 0

    show_precinct_id = False

    district_blocks_fid = [0, 1, 2, 3, 4, 5, 6, 7]

    focus_block_fid = 8

    focus_block_logical_id = 8

    use_ros = False

    metrics = ['demographics', ]

    ros_host = 'localhost'

    ros_port = 9090

    show_voronoi_boundaries = False

    focus_metrics = []

    focus_metric_width = 100

    focus_metric_height = 100

    metric_data = None

    log_data = False

    max_fiducials_per_district = 5

    scale = 1.

    county_containing_rect = [0, 0, 0, 0]

    precinct_2017_containing_rect = [0, 0, 0, 0]

    display_landmarks = True

    visualize_metric_data = True

    def load_data_create_voronoi(self):
        """Loads and initializes all the data and voronoi mapping.
        """
        if self.use_county_dataset:
            geo_data = self.geo_data = GeoDataCounty()
            geo_data.containing_rect = self.county_containing_rect
        else:
            geo_data = self.geo_data = GeoDataPrecinct2017()
            geo_data.containing_rect = self.precinct_2017_containing_rect

        geo_data.screen_size = self.screen_size
        try:
            geo_data.load_npz_data()
        except FileNotFoundError:
            geo_data.load_data()
            geo_data.generate_polygons()
            geo_data.scale_to_screen()
            geo_data.smooth_vertices()

        self.voronoi_mapping = vor = VoronoiMapping()
        vor.start_processing_thread()
        vor.screen_size = self.screen_size
        self.precincts = precincts = []

        for i, (name, polygons) in enumerate(
                zip(geo_data.get_ordered_record_names(), geo_data.polygons)):
            precinct = Precinct(
                name=name, boundary=polygons[0].reshape(-1).tolist(),
                identity=i, location=polygons[0].mean(axis=0).tolist())
            precincts.append(precinct)

        vor.set_precincts(precincts)

    def show_landmarks(self, widget):
        if not self.display_landmarks:
            return

        offset = widget.focus_region_width
        landmarks = self.geo_data.landmarks
        if not landmarks:
            return

        with widget.canvas:
            for x, y, size, name, label in landmarks:
                x, y = dp(x), dp(y)
                size = dp(size)
                x += offset

                if name:
                    Color(1, 1, 1, .6)
                    Rectangle(
                        pos=(x - size / 2., y - size / 2.), size=(size, size),
                        source=resource_find('{}.png'.format(name)))
                if label:
                    label_wid = Label(
                        text=label, pos=(x - size / 2., y + size / 2.),
                        font_size=dp(15))
                    widget.add_widget(label_wid)

                    def set_size(*largs, obj=label_wid, center=x):
                        obj.size = obj.texture_size
                        obj.center_x = center

                    label_wid.fbind('texture_size', set_size)

    def show_precinct_labels(self, widget):
        offset = widget.focus_region_width
        for i, precinct in enumerate(self.precincts):
            x, y = map(dp, precinct.location)
            x += offset
            label = Label(
                text=str(precinct.identity), center=(x, y),
                font_size='20dp')
            widget.add_widget(label)

    def load_config(self):
        keys = [
            'use_county_dataset', 'screen_size',
            'table_mode', 'alignment_filename', 'screen_offset',
            'show_precinct_id', 'focus_block_fid',
            'focus_block_logical_id', 'district_blocks_fid', 'use_ros',
            'metrics', 'ros_host', 'ros_port', 'show_voronoi_boundaries',
            'focus_metrics', 'focus_metric_width', 'focus_metric_height',
            'log_data', 'max_fiducials_per_district', 'scale',
            'county_containing_rect', 'precinct_2017_containing_rect',
            'display_landmarks', 'visualize_metric_data',
            'task_start_idx', 'task_seed'
        ]

        fname = os.path.join(
            os.path.dirname(distopia.__file__), 'data', 'config.json')
        if not os.path.exists(fname):
            config = {key: getattr(self, key) for key in keys}
            with open(fname, 'w') as fp:
                json.dump(config, fp, indent=2, sort_keys=True)

        with open(fname, 'r') as fp:
            for key, val in json.load(fp).items():
                setattr(self, key, val)

        config = {key: getattr(self, key) for key in keys}
        with open(fname, 'w') as fp:
            json.dump(config, fp, indent=2, sort_keys=True)

        for metric in self.focus_metrics:
            if metric not in self.metrics:
                raise ValueError(
                    'Cannot enable focus metric "{}" because it\'s not in '
                    'metrics "{}"'.format(metric, self.metrics))

    def build(self):
        """Builds the GUI.
        """
        resource_add_path(
            os.path.join(os.path.dirname(distopia.__file__), 'data', 'media'))
        self.load_config()

        mat = None
        if self.alignment_filename:
            fname = os.path.join(
                os.path.dirname(distopia.__file__), 'data',
                self.alignment_filename)
            try:
                mat = np.loadtxt(fname, delimiter=',', skiprows=3)
            except Exception as e:
                logging.exception("Not using alignment: {}".format(e))

        self.load_data_create_voronoi()
        self.metric_data = self.geo_data.load_metrics(
            self.metrics, self.precincts)
        self.voronoi_mapping.verify_adjacency = \
            self.geo_data.set_precinct_adjacency(self.precincts)
        self.geo_data.load_landmarks()

        widget = VoronoiWidget(
            voronoi_mapping=self.voronoi_mapping,
            table_mode=self.table_mode, align_mat=mat,
            screen_offset=list(map(dp, self.screen_offset)),
            ros_bridge=self.ros_bridge,
            district_blocks_fid=self.district_blocks_fid,
            focus_block_fid=self.focus_block_fid,
            focus_block_logical_id=self.focus_block_logical_id,
            district_metrics_fn=self.metric_data.compute_district_metrics,
            state_metrics_fn=self.metric_data.create_state_metrics,
            show_voronoi_boundaries=self.show_voronoi_boundaries,
            focus_metrics=self.focus_metrics,
            screen_size=list(map(dp, self.screen_size)),
            focus_metric_height=dp(self.focus_metric_height),
            focus_metric_width=dp(self.focus_metric_width),
            max_fiducials_per_district=self.max_fiducials_per_district,
            visualize_metric_data=self.visualize_metric_data,
            task_start = self.task_start_idx,
            task_seed = self.task_seed
        )

        if self.use_ros:
            box = BoxLayout()
            voronoi_widget = widget
            err = Label(text='No ROS bridge. Please set use_ros to False')
            widget = box
            box.add_widget(err)

            def enable_widget(*largs):
                box.remove_widget(err)
                box.add_widget(voronoi_widget)
                voronoi_widget.ros_bridge = self.ros_bridge
                if self.show_precinct_id:
                    self.show_precinct_labels(voronoi_widget)
                self.show_landmarks(voronoi_widget)

            self.ros_bridge = RosBridge(
                host=self.ros_host, port=self.ros_port,
                ready_callback=Clock.create_trigger(enable_widget),
                log_data=self.log_data)
        else:
            if self.show_precinct_id:
                self.show_precinct_labels(widget)
            self.show_landmarks(widget)

        size = list(map(dp, self.screen_size))
        size = [v / self.scale for v in size]

        scatter = Scatter(
            do_rotation=False, do_scale=False, do_translation_y=False,
            do_translation_x=False, scale=self.scale,
            do_collide_after_children=False)
        scatter.add_widget(widget)

        widget.size_hint = None, None
        scatter.size_hint = None, None
        scatter.fbind('pos', lambda *l: setattr(scatter, 'pos', (0, 0)))
        scatter.pos = 0, 0
        scatter.size = size
        widget.size = size
        return scatter
    # def set_task_config(self,start,seed):
    #     self.target_start = start
    #     self.target_seed = seed

Builder.load_string("""
<SizedLabel@Label>:
    size: self.texture_size
""")

if __name__ == '__main__':
    # argparser = ArgumentParser(description="Run the Distopia Application.")
    # argparser.add_argument('-s','--start', type=int, default=0)
    # argparser.add_argument('-r','--randomseed', type=int, default = 0)
    # args = argparser.parse_args()
    app = VoronoiApp()
    # app.set_task_config(task_start=args.start, task_seed=args.randomseed)
    try:
        app.run()
    finally:
        app.voronoi_mapping.stop_thread()
        if app.ros_bridge:
            app.ros_bridge.stop_threads()
