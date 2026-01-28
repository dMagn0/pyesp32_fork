import os
from kivy.lang.builder import Builder

def build_strings():
    main_directory = os.path.dirname(os.path.abspath(__file__))

    Builder.load_string(open(os.path.join(main_directory, "interface_base.kv"), encoding="utf-8").read(),rulesonly=True)
    
    pass