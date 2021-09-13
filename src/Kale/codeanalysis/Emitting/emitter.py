import os
import subprocess
import platform


class Emitter:
    def __init__(self, path):
        self.path = f"{path}.c"
        self.header = ""
        self.code = ""

    def __int__(self):
        self.code = ""

    def emit(self, code):
        self.code += code

    def emit_line(self, code):
        self.code += code + '\n'

    def add_header(self, code):
        self.header += code + '\n'

    def output(self):
        with open(self.path, 'w') as output_file:
            output_file.write(self.header + self.code)

    @staticmethod
    def build(file="out"):
        # while True:
        #     if os.path.isfile(f"{file}.c"):
        if platform.system() == 'Windows':
            try:
                subprocess.call(["gcc", f"-o{file}.exe", f"{file}.c"])
            except:
                subprocess.call(["cl", f"-o{file}.exe", f"{file}.c"])
        else:
            subprocess.call(["gcc", f"{file}.c -o {file}.o"])

    @staticmethod
    def run(file="out"):
        if platform.system() == 'Windows':
            subprocess.call([f"{file}.exe"])
        else:
            subprocess.call([f"{file}.o"])
    
    @staticmethod
    def clean(file="out"):
        if platform.system() == 'Windows':
            subprocess.call(["del", f"{file}.exe"])
        else:
            subprocess.call(["rm", f"{file}.o"])
