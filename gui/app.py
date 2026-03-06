import customtkinter as ctk
from PIL import Image

from pathlib import Path
BASE_DIR = Path(__file__).parent

ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

class App(ctk.CTk):
    instance = None
    counter = 0

    def __init__(self, results_queue):
        App.instance = self
        super().__init__()
        self.title('NIDS Dashboard')
        self.geometry('900x500')
        self.configure(fg_color='#120303')
        self.resizable(False, False)
        self.colors = ['#361010', '#360A0A']
        self.rf_widgets = []
        self.rf_levels = ['safe', 'potential', 'likely', 'danger']
        self.rf_coordinates = {'safe':(62, 92),'potential':(231, 92),'likely':(438, 93),'danger':(614, 92)}
        self.ae_widgets = []
        self.digit_coordinates = [(84, 290), (103, 290), (123, 290)]
        self.digit_widgets = []
        self.text_coordinates = [(105, 290), (124, 290), (145, 290)]
        self.text_widgets = []
        self.results_queue = results_queue

        self.root = ctk.CTkFrame(self, corner_radius=0)
        self.root.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.bg_image = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'Frame.png'), dark_image=Image.open(BASE_DIR/'resources'/'Frame.png'), size=(900, 500))
        self.bg_label = ctk.CTkLabel(self.root, image=self.bg_image, text="", bg_color='#483941')
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.start_anomaly_bar = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'start_anomaly_bar.png'), dark_image=Image.open(BASE_DIR/'resources'/'start_anomaly_bar.png'), size=(22, 30))
        self.start_anomaly_bar = ctk.CTkLabel(self.bg_label, image=self.start_anomaly_bar, text="", bg_color='#483941')

        self.anomaly_bar = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'anomaly_bar.png'), dark_image=Image.open(BASE_DIR/'resources'/'anomaly_bar.png'), size=(1, 30))
        self.anomaly_bar = ctk.CTkLabel(self.root, image=self.anomaly_bar, text="")

        self.safe_img = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'safe.png'), dark_image=Image.open(BASE_DIR/'resources'/'safe.png'), size=(240, 160))
        self.safe_img = ctk.CTkLabel(self.bg_label, image=self.safe_img, text="", bg_color='#483941')
        self.rf_widgets.append(self.safe_img)

        self.potential_img = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'potential_threat.png'), dark_image=Image.open(BASE_DIR/'resources'/'potential_threat.png'), size=(280, 160))
        self.potential_img = ctk.CTkLabel(self.bg_label, image=self.potential_img, text="", bg_color='#483941')
        self.rf_widgets.append(self.potential_img)

        self.likely_img = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'threat_likely.png'), dark_image=Image.open(BASE_DIR/'resources'/'threat_likely.png'), size=(241, 160))
        self.likely_img = ctk.CTkLabel(self.bg_label, image=self.likely_img, text="", bg_color='#483941')
        self.rf_widgets.append(self.likely_img)

        self.danger_img = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'danger.png'), dark_image=Image.open(BASE_DIR/'resources'/'danger.png'), size=(240, 160))
        self.danger_img = ctk.CTkLabel(self.bg_label, image=self.danger_img, text="", bg_color='#483941')
        self.rf_widgets.append(self.danger_img)

        for _ in range(3):
            for i in range(10):
                number_img = ctk.CTkImage(light_image=Image.open(f"{BASE_DIR}/resources/{i}.png"), dark_image=Image.open(f"{BASE_DIR}/resources/{i}.png"), size=(20, 39))
                number_img = ctk.CTkLabel(self.bg_label, image=number_img, text="", bg_color='#483941')
                self.ae_widgets.append(number_img)

        self.normal_text = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'normal.png'), dark_image=Image.open(BASE_DIR/'resources'/'normal.png'), size=(161, 39))
        self.normal_text = ctk.CTkLabel(self.bg_label, image=self.normal_text, text="", bg_color='#483941')
        self.text_widgets.append(self.normal_text)

        self.elevated_text = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'elevated.png'), dark_image=Image.open(BASE_DIR/'resources'/'elevated.png'), size=(179, 39))
        self.elevated_text = ctk.CTkLabel(self.bg_label, image=self.elevated_text, text="", bg_color='#483941')
        self.text_widgets.append(self.elevated_text)

        self.suspicious_text = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'suspicious.png'), dark_image=Image.open(BASE_DIR/'resources'/'suspicious.png'), size=(209, 44))
        self.suspicious_text = ctk.CTkLabel(self.bg_label, image=self.suspicious_text, text="", bg_color='#483941')
        self.text_widgets.append(self.suspicious_text)

        self.severe_text = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'severe.png'), dark_image=Image.open(BASE_DIR/'resources'/'severe.png'), size=(153, 39))
        self.severe_text = ctk.CTkLabel(self.bg_label, image=self.severe_text, text="", bg_color='#483941')
        self.text_widgets.append(self.severe_text)

        self.btn = ctk.CTkButton(self.root, text="Start capture/inference", command=self.start)
        self.btn.pack()

    def start(self):
        self.poll_results()

    def poll_results(self):
        try:
            while not self.results_queue.empty():
                result = self.results_queue.get_nowait()
                if result is None:
                    return
                ae_percent, ae_score, rf_score = result

                self.remove_all()
                self.place_rf(self.rf_widgets[rf_score], self.rf_levels[rf_score])
                self.display_ae(ae_score, ae_percent)
        except:
            pass

        self.after(100, self.poll_results)

    def remove_all(self):
        for widget in self.rf_widgets:
            widget.place_forget()

        for widget in self.ae_widgets:
            widget.place_forget()

        for widget in self.text_widgets:
            widget.place_forget()

        self.start_anomaly_bar.place_forget()
        self.anomaly_bar.place_forget()

    def place_rf(self, widget, level):
        x, y = self.rf_coordinates[level]
        widget.place(x=x, y=y)

    def display_ae(self, guess, score):
        width = max(1, int(680 * (score / 100)))

        score = list(str(score))
        n = min(len(score), 3)
        for i in range(n):
            score[i] = int(score[i])

        def place_digit(digit, pos):
            x, y = self.digit_coordinates[pos]
            self.ae_widgets[digit+pos*10].place(x=x, y=y)

        for i in range(n):
            place_digit(score[i], i)

        text_x, text_y = self.text_coordinates[n-1]
        self.text_widgets[guess].place(x=text_x, y=text_y)

        self.start_anomaly_bar.place(x=65, y=345)

        self.anomaly_bar = ctk.CTkImage(light_image=Image.open(BASE_DIR/'resources'/'anomaly_bar.png'), dark_image=Image.open(BASE_DIR/'resources'/'anomaly_bar.png'), size=(width, 30))
        self.anomaly_bar = ctk.CTkLabel(self.bg_label, image=self.anomaly_bar, text="", bg_color='#483941')
        self.anomaly_bar.place(x=85, y=345)

def dashboard_process(results_queue):
    app_instance = App(results_queue)
    app_instance.mainloop()

