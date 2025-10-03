# main.py - NaughtyNicOMeter with needle return and smooth crossfade soft reset
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.graphics import Rectangle, PushMatrix, PopMatrix, Rotate, Scale, Color
from kivy.uix.widget import Widget
import random

# --- Sound loader helper ---
def load_sound(path, volume=0.95):
    sound = SoundLoader.load(path)
    if sound:
        sound.volume = volume
        print(f"[DEBUG] Sound loaded: {path} (volume set to {volume})")
    else:
        print(f"[DEBUG] Sound failed to load: {path}")
    return sound

click_sound = load_sound('assets/sounds/click.wav')

def play_click(button_source):
    if 'result-scanning.png' in button_source:
        return
    if click_sound:
        Clock.schedule_once(lambda dt: click_sound.play(), 0.1)

# --- Result mapping ---
result_map = {
    "naughty": {"angle": -70, "sound": "naughty.wav", "image": "result-naughty.png"},
    "naughtyish": {"angle": -20, "sound": "naughty.wav", "image": "result-naughtyish.png"},
    "ontheline": {"angle": 0, "sound": "ontheline.wav", "image": "result-ontheline.png"},
    "nice": {"angle": 20, "sound": "nice-bell.wav", "image": "result-nice.png"},
    "wow": {"angle": 70, "sound": "nice-bell.wav", "image": "result-wow.png"},
}

# --- Needle Widget ---
class RotatingNeedle(KivyImage):
    angle = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rot = Rotate()
        self.bind(pos=self.update_transform, size=self.update_transform, angle=self.update_transform)

    def update_transform(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            center_x = self.x + self.width / 2
            center_y = self.y + self.height / 2
            self.rot = Rotate(origin=(center_x, center_y), angle=-self.angle)
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()

    def start_full_animation(self, result_angle):
        Clock.schedule_once(lambda dt: self.animate_wild_sweeps(result_angle), 1.0)

    def animate_wild_sweeps(self, result_angle):
        sweep_duration = 6.417
        interval = 0.3
        sweeps = int(sweep_duration / interval)
        self.sweep_count = 0
        self.result_angle = result_angle

        def sweep_step(dt):
            if self.sweep_count >= sweeps:
                self.prepare_final_swing()
                return
            angle = random.randint(-70, 70)
            Animation(angle=angle, duration=interval).start(self)
            self.sweep_count += 1
            Clock.schedule_once(sweep_step, interval)

        sweep_step(0)

    def prepare_final_swing(self):
        current_angle = self.angle
        target_angle = self.result_angle
        distance = abs(current_angle - target_angle)
        if target_angle == 0:
            dramatic_angle = random.choice([-35, 35])
            Animation(angle=dramatic_angle, duration=0.4).start(self)
            Clock.schedule_once(lambda dt: self.final_swing_with_oscillation(target_angle), 0.5)
        elif distance < 30:
            opposite = -target_angle if target_angle != 0 else random.choice([-60, 60])
            Animation(angle=opposite, duration=0.4).start(self)
            Clock.schedule_once(lambda dt: self.final_swing_with_oscillation(target_angle), 0.5)
        else:
            self.final_swing_with_oscillation(target_angle)

    def final_swing_with_oscillation(self, target_angle):
        overshoot = -target_angle * 0.6
        settle = Animation(angle=overshoot, duration=0.5, t='out_quad') + \
                 Animation(angle=target_angle, duration=0.6, t='out_back') + \
                 Animation(angle=target_angle + 6, duration=0.3) + \
                 Animation(angle=target_angle - 4, duration=0.3) + \
                 Animation(angle=target_angle + 2, duration=0.2) + \
                 Animation(angle=target_angle, duration=0.2)
        settle.start(self)

# --- Pressed Image Button ---
class PressedImageButton(ButtonBehavior, KivyImage):
    scale = NumericProperty(1.0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(scale=self.on_scale)
        self.bind(pos=self.update_rect, size=self.update_rect, texture=self.update_rect)
        with self.canvas:
            self.rect = Rectangle(texture=self.texture, pos=self.pos, size=self.size)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.rect.texture = self.texture

    def on_press(self):
        Animation.cancel_all(self)
        Animation(scale=0.92, duration=0.05).start(self)

    def on_release(self):
        Animation.cancel_all(self)
        Animation(scale=1.0, duration=0.1).start(self)

    def on_scale(self, instance, value):
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            Scale(x=value, y=value, z=1, origin=self.center)
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()

# --- Buttons ---
class ResetButton(PressedImageButton):
    def __init__(self, needle_ref, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.needle = needle_ref
        self.app = app_ref

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            if self.app.result_displayed or self.app.scanning:
                print("[DEBUG] ResetButton triggers soft reset")
                self.app.soft_reset()
                return True
            if not self.app.scanning:
                play_click(self.source)
                local_x = touch.pos[0] - self.x
                percent = local_x / self.width
                if percent < 0.2: self.app.selected_result = "naughty"
                elif percent < 0.4: self.app.selected_result = "naughtyish"
                elif percent < 0.6: self.app.selected_result = "ontheline"
                elif percent < 0.8: self.app.selected_result = "nice"
                else: self.app.selected_result = "wow"
                return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True if self.collide_point(*touch.pos) else False

class StartButton(PressedImageButton):
    def __init__(self, needle_ref, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.needle = needle_ref
        self.app = app_ref

    def on_press(self):
        super().on_press()
        if self.app.scanning or not self.app.selected_result:
            return
        play_click(self.source)
        self.app.start_scan_sequence()

class ResultButton(PressedImageButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.disabled = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.opacity > 0:
            parent = self.parent
            if hasattr(parent, "soft_reset"):
                print("[DEBUG] ResultButton tapped -> soft reset")
                if hasattr(parent, "needle"):
                    # Animate needle back to 0° first
                    Animation(angle=0, duration=0.5, t='out_quad').start(parent.needle)
                    Clock.schedule_once(lambda dt: parent.soft_reset(), 0.55)
                else:
                    parent.soft_reset()
                return True
        return super().on_touch_down(touch)

# --- Main Scanner Layout ---
class NaughtyNicOMeter(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_result = None
        self.scanning = False
        self.result_displayed = False

        with self.canvas.before:
            Color(0,0,0,1)
            self.bg_rect = Rectangle(pos=(0,0), size=Window.size)
        Window.bind(on_resize=self.update_bg)

        screen_width, screen_height = Window.size
        aspect_ratio = 16 / 9
        target_height = screen_height
        target_width = target_height * aspect_ratio
        horizontal_offset = (screen_width - target_width) / 2
        center_x = horizontal_offset + target_width / 2

        layer1 = Widget(size=(target_width, target_height), pos=(horizontal_offset, 0))
        with layer1.canvas:
            Color(0,0,0,1)
            Rectangle(pos=layer1.pos, size=layer1.size)
        self.add_widget(layer1)

        gauge_width = screen_width * 0.48
        gauge_height = screen_height * 0.20
        self.add_widget(KivyImage(
            source="scanner-layer2.png",
            size_hint=(None, None),
            size=(gauge_width, gauge_height),
            pos=(center_x - gauge_width/2, screen_height * 0.72)
        ))

        needle_width = gauge_width * 1.35
        needle_height = gauge_height * 1.35
        self.needle = RotatingNeedle(
            source="scanner-layer3.png",
            size_hint=(None, None),
            size=(needle_width, needle_height),
            pos=(center_x - needle_width/2, screen_height * 0.6)
        )
        self.add_widget(self.needle)

        reset_width = screen_width * 0.345
        reset_height = screen_height * 0.145
        touch_width = reset_width * 0.6 + 55
        touch_height = reset_height * 0.6 + 10
        touch_x = center_x - touch_width/2
        touch_y = screen_height*0.35 + (reset_height - touch_height)/2

        self.result_images = {}
        for key in ["scanning","naughty","naughtyish","ontheline","nice","wow"]:
            img = ResultButton(
                source=f"result-{key}.png",
                size_hint=(None, None),
                size=(touch_width, touch_height),
                pos=(touch_x, touch_y),
                opacity=0
            )
            self.result_images[key] = img
            self.add_widget(img)

        self.add_widget(KivyImage(
            source="scanner-layer4.png",
            size_hint=(None, None),
            size=(target_width, target_height),
            pos=(horizontal_offset, 0)
        ))

        self.reset_button = ResetButton(
            needle_ref=self.needle,
            app_ref=self,
            source="button-reset.png",
            size_hint=(None, None),
            size=(touch_width, touch_height),
            pos=(touch_x, touch_y)
        )
        self.add_widget(self.reset_button)

        start_width = screen_width * 0.25 * 0.92
        start_height = screen_height * 0.1 * 0.94
        start_touch_w = start_width*0.5+8
        start_touch_h = start_height*0.6+18
        start_x = center_x - start_touch_w/2
        start_y = screen_height*0.1 + 70 + (start_height - start_touch_h)/2

        self.start_button = StartButton(
            needle_ref=self.needle,
            app_ref=self,
            source="button-start.png",
            size_hint=(None, None),
            size=(start_touch_w, start_touch_h),
            pos=(start_x, start_y)
        )
        self.add_widget(self.start_button)

    def update_bg(self, instance, width, height):
        self.bg_rect.size = (width, height)

    def start_scan_sequence(self):
        self.scanning = True
        Animation(opacity=0, duration=0.5).start(self.reset_button)
        Animation(opacity=1, duration=0.5).start(self.result_images["scanning"])
        scan_sound = load_sound("assets/sounds/scan.wav")
        if scan_sound: scan_sound.play()
        self.needle.start_full_animation(result_map[self.selected_result]["angle"])
        Clock.schedule_once(lambda dt: self.reveal_result(), 10.417)

    def reveal_result(self):
        self.scanning = False
        Animation(opacity=0, duration=0.3).start(self.result_images["scanning"])
        for img in self.result_images.values(): img.opacity = 0
        result_key = self.selected_result
        result_img = self.result_images[result_key]
        Animation(opacity=1, duration=0.5).start(result_img)
        result_sound = load_sound(f"assets/sounds/{result_map[result_key]['sound']}")
        if result_sound: result_sound.play()
        self.result_displayed = True

    def reset_app(self):
        print("[DEBUG] reset_app -> soft_reset")
        self.soft_reset()

    def soft_reset(self):
        """
        Crossfade current meter into a fresh instance.
        Needle must return to center first.
        """
        print("[DEBUG] Performing smooth crossfade soft reset with needle return")
        try:
            Animation.cancel_all(self.needle)
        except Exception:
            pass

        parent = self.parent
        if parent is None:
            print("[WARN] soft_reset fallback: no parent found, re-init in place")
            try:
                self.__init__()
            except Exception as e:
                print("[ERROR] soft_reset fallback failed:", e)
            return

        # Animate needle back to 0° first
        needle_anim = Animation(angle=0, duration=0.5, t='out_quad')

        def start_crossfade(*args):
            new_meter = NaughtyNicOMeter()
            new_meter.opacity = 0
            parent.add_widget(new_meter)

            anim_duration = 1.25  # crossfade duration
            Animation(opacity=0, duration=anim_duration).start(self)
            Animation(opacity=1, duration=anim_duration).start(new_meter)

            def remove_old_meter(*a):
                try:
                    parent.remove_widget(self)
                    print("[DEBUG] Crossfade complete: old meter removed")
                except Exception as e:
                    print("[WARN] Could not remove old meter after crossfade:", e)

            Clock.schedule_once(remove_old_meter, anim_duration)

        needle_anim.bind(on_complete=start_crossfade)
        needle_anim.start(self.needle)

# --- Title Overlay ---
class TitleOverlay(KivyImage):
    def __init__(self, target_widget, **kwargs):
        super().__init__(**kwargs)
        self.source = "title.png"
        self.size_hint = (None,None)
        self.size = Window.size
        self.opacity = 0
        self.target_widget = target_widget
        self.target_widget.opacity = 0
        Clock.schedule_once(self.start_sequence, 0.5)

    def start_sequence(self, dt):
        fade_in = Animation(opacity=1, duration=0.5)
        fade_in.bind(on_complete=lambda *a: Clock.schedule_once(self.fade_out_sequence, 3))
        fade_in.start(self)

    def fade_out_sequence(self, dt):
        fade_out = Animation(opacity=0, duration=0.5)
        fade_out.bind(on_complete=lambda *a: self.reveal_main_app())
        fade_out.start(self)

    def reveal_main_app(self):
        Animation(opacity=1, duration=0.5).start(self.target_widget)
        if self.parent:
            try:
                self.parent.remove_widget(self)
            except Exception:
                pass

# --- App ---
class MeterApp(App):
    def build(self):
        root = FloatLayout()
        meter = NaughtyNicOMeter()
        root.add_widget(meter)
        root.add_widget(TitleOverlay(target_widget=meter))
        return root

if __name__ == "__main__":
    MeterApp().run()
