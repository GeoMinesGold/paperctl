from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
import subprocess
import threading

class FileSorterGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # File selection
        self.file_chooser = FileChooserIconView()
        self.add_widget(self.file_chooser)
        
        # Output directory selection
        self.output_label = Label(text='Output Directory:')
        self.add_widget(self.output_label)
        self.output_input = TextInput(hint_text='Select output directory')
        self.add_widget(self.output_input)
        self.select_output_btn = Button(text='Browse')
        self.select_output_btn.bind(on_release=self.select_output)
        self.add_widget(self.select_output_btn)
        
        # Options
        self.options_layout = BoxLayout(orientation='horizontal')
        self.verbose_check = CheckBox()
        self.options_layout.add_widget(Label(text='Verbose Mode'))
        self.options_layout.add_widget(self.verbose_check)
        self.dry_run_check = CheckBox()
        self.options_layout.add_widget(Label(text='Dry Run'))
        self.options_layout.add_widget(self.dry_run_check)
        self.manual_check = CheckBox()
        self.options_layout.add_widget(Label(text='Manual Input'))
        self.options_layout.add_widget(self.manual_check)
        self.add_widget(self.options_layout)
        
        # Start Button
        self.start_btn = Button(text='Start Sorting')
        self.start_btn.bind(on_release=self.start_sorting)
        self.add_widget(self.start_btn)
        
        # Log Output
        self.log_view = ScrollView()
        self.log_label = Label(text='', size_hint_y=None)
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_view.add_widget(self.log_label)
        self.add_widget(self.log_view)
    
    def select_output(self, instance):
        popup = Popup(title='Select Output Directory', size_hint=(0.9, 0.9))
        file_chooser = FileChooserIconView()
        def choose_dir(instance):
            self.output_input.text = file_chooser.path
            popup.dismiss()
        select_btn = Button(text='Select', on_release=choose_dir)
        popup_box = BoxLayout(orientation='vertical')
        popup_box.add_widget(file_chooser)
        popup_box.add_widget(select_btn)
        popup.content = popup_box
        popup.open()
    
    def start_sorting(self, instance):
        selected_files = self.file_chooser.selection
        output_dir = self.output_input.text
        verbose = '--verbose' if self.verbose_check.active else ''
        dry_run = '--dry-run' if self.dry_run_check.active else ''
        manual = '--manual' if self.manual_check.active else ''
        
        if not selected_files or not output_dir:
            self.log_label.text = 'Error: Select files and output directory!'
            return
        
        cmd = ['python3', 'main.py', *selected_files, '-o', output_dir, verbose, dry_run, manual]
        cmd = [arg for arg in cmd if arg]
        
        def run_command():
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in process.stdout:
                self.log_label.text += line
            for err in process.stderr:
                self.log_label.text += err
        
        threading.Thread(target=run_command, daemon=True).start()
        self.log_label.text += '\nSorting started...\n'

class FileSorterApp(App):
    def build(self):
        return FileSorterGUI()

if __name__ == '__main__':
    FileSorterApp().run()
