import math

from TLOA.core.constants import ATLAS_PATH, IMAGES_PATH, LIGHT_FOCUS_OFFSET
from TLOA.entities import BrownShip

from kivy.uix.image import Image
from kivy.uix.widget import Widget

HP_BAR_X_OFFSET = 75
HP_BAR_Y_OFFSET = 150

FIRE_X_OFFSET = 75
FIRE_Y_OFFSET = 20


class ShipView(Widget):
    def __init__(self, ship: BrownShip, source, pos, **kwargs):
        super().__init__(pos=pos, **kwargs)

        health = round(ship.health / 10) * 10
        x, y = self.pos
        self._hp_bar = Image(pos=(x + HP_BAR_X_OFFSET, y + HP_BAR_Y_OFFSET),
                             source=ATLAS_PATH.format(health))

        self._ship_image = Image(source=source, pos=self.pos)
        self._ship_image.size = self._ship_image.texture_size
        self._fire = Image(source=IMAGES_PATH.format('fire.zip'), anim_delay=0.1)
        self._fire.opacity = 0

        self.add_widget(self._hp_bar)
        self.add_widget(self._ship_image)
        self.add_widget(self._fire)

        ship.bind(health=self.on_health_change)
        self.bind(pos=self.on_pos_changed)

    def on_health_change(self, _ship: BrownShip, value: float):
        health = math.ceil(value / 10) * 10
        self._hp_bar.source = ATLAS_PATH.format(health)
        # burn the ship if health < 50
        if health <=80:
            self._fire.opacity = 100
        # destroy it if health is 0

    def on_pos_changed(self, _ship_view, pos):
        x, y = self._ship_image.pos = pos
        self._hp_bar.pos = (x + HP_BAR_X_OFFSET, y + HP_BAR_Y_OFFSET)
        self._fire.pos = (x + FIRE_X_OFFSET, y + FIRE_Y_OFFSET)
        # TODO for burning effect
