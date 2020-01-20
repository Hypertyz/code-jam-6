from datetime import datetime
import pickle

from geopy.geocoders import Nominatim

import kivy
import requests
from kivy.animation import Animation
from kivy.app import App
from kivy.graphics import *
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager

from suntime import Sun, SunTimeException

from config import GEOLOCATION_KEY

kivy.require('1.11.1')


# Widget element things #
class DialWidget(FloatLayout):
    """
    Speed will become a fixed value of 86400 once completed.
    Image should, i suppose, be a fixed image?
    At some point we'll need to add a tuple(?) for sunrise / sunset times.
    """
    angle = NumericProperty(0)

    def __init__(self, day_length, dial_image, dial_size, suntimes, **kwargs):
        super(DialWidget, self).__init__(**kwargs)

        self.dial_file = dial_image
        self.dial_size = dial_size      # X / Y tuple.

        # Duration is how long it takes to perform the overall animation
        anim = Animation(angle=360, duration=day_length)
        anim += Animation(angle=360, duration=day_length)
        anim.repeat = True
        anim.start(self)

        # Split suntime tuple into named variables
        sunrise = suntimes[0]
        sunset = suntimes[1]

        # Add icons that can be arbitrarily rotated on canvas.
        self.add_widget(SunRiseMarker(sunrise))
        self.add_widget(SunSetMarker(sunset))

    def on_angle(self, item, angle):
        if angle == 360:
            item.angle = 0


class NowMarker(FloatLayout):
    pass


class SunRiseMarker(FloatLayout):
    def __init__(self, rot_angle, **kwargs):
        super(SunRiseMarker, self).__init__(**kwargs)
        self.rot_angle = rot_angle


class SunSetMarker(FloatLayout):
    def __init__(self, rot_angle, **kwargs):
        super(SunSetMarker, self).__init__(**kwargs)
        self.rot_angle = rot_angle


class SunShading(FloatLayout):
    def __init__(self, suntimes, **kwargs):
        super(SunShading, self).__init__(**kwargs)

        # Split suntime tuple into named variables
        sunrise = suntimes[0]
        sunset = suntimes[1]

        sunstart = 360 - sunrise
        sunend = 360 - sunset

        with self.canvas:
            Color(0, 0.2, 0.40)
            Ellipse(pos=(self.width / 2 + 20, self.height / 2), angle_start=180, angle_end=360,
                    size=(500, 500))
            Color(252 / 255, 212 / 255, 64 / 255)
            Ellipse(pos=(self.width / 2 + 20, self.height / 2), angle_start=0, angle_end=180,
                    size=(500, 500))

        self.opacity = 0.5


class DialEffectWidget(EffectWidget):
    def __init__(self, **kwargs):
        super(DialEffectWidget, self).__init__(**kwargs)
        self.add_widget(SunShading((124.75, 1.25)))
        self.effects = [HorizontalBlurEffect(size=20.0), VerticalBlurEffect(size=20.0)]


class DialTestScreen(Screen):
    def __init__(self, **kwargs):
        super(DialTestScreen, self).__init__(**kwargs)
        self.add_widget(DialEffectWidget())


# Screens in the App #
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.add_widget(DialWidget(86400, 'assets/dial.png', (0.8, 0.8), self.suntimes()))
        self.add_widget(DialEffectWidget())
        self.add_widget(NowMarker())
        self.suntimes()

    def settings_button(self):
        # SettingsScreen()
        DialTestScreen()

    def ipgeolocate(self):
        r = requests.get(f'https://api.ipgeolocation.io/ipgeo?apiKey={GEOLOCATION_KEY}')
        resp = r.json()
        city = resp['city']
        state_prov = resp['state_prov']

        geolocate = Nominatim(user_agent="Code Jam 6: SunClock")
        location = geolocate.geocode(f"{city} {state_prov}")

        # pickle the object for testing purposes
        temp_latlong = [location.latitude, location.longitude]
        with open('latlong.tmp', 'wb') as f:
            pickle.dump(temp_latlong, f)

        return location.latitude, location.longitude

    def suntimes(self):
        # lat_long = self.ipgeolocate()

        # pickled object for testing purposes
        with open('latlong.tmp', 'rb') as f:
            lat_long = pickle.load(f)

        sun_time = Sun(lat_long[0], lat_long[1])

        try:
            today_sunrise = sun_time.get_sunrise_time()
        except SunTimeException:
            raise ValueError("AINT NO SUNSHINE WHEN SHE'S GONE")

        try:
            today_sunset = sun_time.get_sunset_time()
        except SunTimeException:
            raise ValueError("HOLY SHIT TOO MUCH SUNSHINE WHEN SHE'S HERE")

        # This is *super* ugly, I'm sure we can find a more elegant way to do this
        now = datetime.now()
        today_sunrise = today_sunrise.replace(tzinfo=None)
        today_sunset = today_sunset.replace(tzinfo=None)

        if now > today_sunrise and today_sunset:
            # Don't need TZInfo to perform this operation
            today_sunrise = now - today_sunrise.replace(tzinfo=None)
            today_sunset = now - today_sunset.replace(tzinfo=None)

            # Convert timedelta into minutes and round
            today_sunrise = round(today_sunrise.seconds / 60)
            today_sunset = round(today_sunset.seconds / 60)

            # Since icons are in the "past" (to the left) keep the angles positive
            # After Sunrise, after Sunset
            today_sunrise = today_sunrise * 0.25
            today_sunset = today_sunset * 0.25

        elif now < today_sunrise and today_sunset:
            today_sunrise = today_sunrise.replace(tzinfo=None) - now
            today_sunset = today_sunset.replace(tzinfo=None) - now

            today_sunrise = round(today_sunrise.seconds / 60)
            today_sunset = round(today_sunset.seconds / 60)

            # Since icons are in the "future" (to the right) keep angles negative
            # Before Sunrise, after Sunset
            today_sunrise = today_sunrise * 0.25 * -1
            today_sunset = today_sunset * 0.25 * -1

        else:
            today_sunrise = now - today_sunrise.replace(tzinfo=None)
            today_sunset = today_sunset.replace(tzinfo=None) - now

            today_sunrise = round(today_sunrise.seconds / 60)
            today_sunset = round(today_sunset.seconds / 60)

            # After Sunrise, before Sunset
            today_sunrise = today_sunrise * 0.25
            today_sunset = today_sunset * 0.25 * -1

        print(today_sunrise, today_sunset)
        return today_sunrise, today_sunset


# Settings panel #
class SettingsScreen(Popup):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)

        r = requests.get(f'https://api.ipgeolocation.io/ipgeo?apiKey={GEOLOCATION_KEY}')
        resp = r.json()
        city = resp['city']
        state_prov = resp['state_prov']
        country = resp['country_name']
        zipcode = resp['zipcode']

        settings_popup = Popup(title="Settings",
                               content=Label(
                                   text=f'Currently in {city}, {state_prov}, {country} {zipcode}'
                               ),
                               size_hint=(None, None), size=(500, 200))
        settings_popup.open()


class WindowManager(ScreenManager):
    pass


class SunClock(App):
    """
    Core class.
    """
    def build(self):
        Builder.load_file('main.kv')
        sm = WindowManager()

        screens = [MainScreen(name='main'), DialTestScreen(name='test')]
        for screen in screens:
            sm.add_widget(screen)

        # Don't forget to change this shit back.
        sm.current = 'main'

        return sm


if __name__ == '__main__':
    SunClock().run()
