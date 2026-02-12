import time

import customtkinter as ctk
from PIL import Image

class App(ctk.CTk):
    instance = None
    counter = 0

    def __init__(self):
        App.instance = self
        super().__init__()
        self.title('NIDS Dashboard')
        self.geometry('1000x600')
        self.configure(fg_color='#120303')
        self.resizable(False, False)
        self.colors = ['#361010', '#360A0A']
        self.coordinates = {'safe':(186, 89),'potential':(364, 89),'likely':(540, 89),'danger':(717, 89)}
        self.level_widgets = []
        self.levels = ['safe', 'potential', 'likely', 'danger']

        self.root = ctk.CTkFrame(self, corner_radius=0)
        self.root.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.bg_image = ctk.CTkImage(light_image=Image.open("resources/Frame.png"), dark_image=Image.open("resources/Frame.png"), size=(1000, 600))
        self.bg_label = ctk.CTkLabel(self.root, image=self.bg_image, text="")
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.safe_img = ctk.CTkImage(light_image=Image.open("resources/safe.png"), dark_image=Image.open("resources/safe.png"), size=(165, 188))
        self.safe_img = ctk.CTkLabel(self.bg_label, image=self.safe_img, text="", bg_color='#765F5F')
        self.level_widgets.append(self.safe_img)

        self.potential_img = ctk.CTkImage(light_image=Image.open("resources/potential_threat.png"), dark_image=Image.open("resources/potential_threat.png"), size=(165, 188))
        self.potential_img = ctk.CTkLabel(self.bg_label, image=self.potential_img, text="", bg_color='#765F5F')
        self.level_widgets.append(self.potential_img)

        self.likely_img = ctk.CTkImage(light_image=Image.open("resources/threat_likely.png"), dark_image=Image.open("resources/threat_likely.png"), size=(165, 188))
        self.likely_img = ctk.CTkLabel(self.bg_label, image=self.likely_img, text="", bg_color='#765F5F')
        self.level_widgets.append(self.likely_img)

        self.danger_img = ctk.CTkImage(light_image=Image.open("resources/danger.png"), dark_image=Image.open("resources/danger.png"), size=(165, 188))
        self.danger_img = ctk.CTkLabel(self.bg_label, image=self.danger_img, text="", bg_color='#765F5F')
        self.level_widgets.append(self.danger_img)

        def toggle_label():
            self.remove_all()
            self.place(self.level_widgets[self.counter], self.levels[self.counter])
            if self.counter == 3:
                self.counter = 0
                return
            self.counter += 1

        self.btn = ctk.CTkButton(self.root, text="Toggle", command=toggle_label)
        self.btn.pack()

    def remove_all(self):
        for widget in self.level_widgets:
            widget.place_forget()

    def place(self, widget, level):
        x, y = self.coordinates[level]
        widget.place(x=x, y=y)

    def rotate(self):
        for _ in range(1000):
            for widget, level in zip(self.level_widgets, self.levels):
                self.place(widget, level)
                time.sleep(10)
                self.remove_all()



app_instance = App()
app_instance.mainloop()

