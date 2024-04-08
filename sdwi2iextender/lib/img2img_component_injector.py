import os
import sys
import gradio as gr
import inspect
import ast

import modules.scripts as scripts
from modules.scripts import ScriptClassData, scripts_data
from modules import img2img

from .one_time_callable import one_time_callable


@one_time_callable
def activate_injector():
    register_SdwI2iExtenderScript()
    activate_generation_component_injector()


class SdwI2iExtenderScript(scripts.Script):
    img2img_instance = None

    def __init__(self):
        self.__ui_args = None
        self.__image_components_start_at = 0

        self.intercept_generation = False
        self.size_override = None
        self.init_images_override = None
        self.mask_override = None

    def title(self):
        return "Stable Diffusion Webui Img2img Extender Library"

    def ui(self, is_img2img):
        if is_img2img:
            SdwI2iExtenderScript.img2img_instance = self
        return self.create_or_get_ui_args()

    def create_or_get_ui_args(self):
        if self.__ui_args is not None:
            return self.__ui_args
        
        self.__ui_args = self.create_ui()

        return self.__ui_args
    
    def create_ui(self):
        from .img2img_tab_extender import Img2imgTabExtender

        selected_tab_index_component = gr.Number(visible=False, elem_id="selected_img2img_tab_index_sdwi2iextender")
        Img2imgTabExtender.create_custom_tab_objects(selected_tab_index_component)

        process_args = []
        for custom_tab in Img2imgTabExtender.tab_data_list:
            image_components = custom_tab.tab_object.image_components()
            assert len(image_components) == 2, f'Expected 2 image components, got {len(image_components)}.'

            process_args += image_components

        data_components = [
            selected_tab_index_component,
        ]

        self.__image_components_start_at = len(data_components)

        return *data_components, *process_args

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else False
    
    def should_intercept_generation(self, *args):
        from .img2img_tab_extender import Img2imgTabExtender

        tab_id = self.get_tab_id(*args)
        self.intercept_generation = tab_id >= Img2imgTabExtender.amount_of_default_tabs

        return self.intercept_generation

    def resolve_image_and_mask(self, *args):
        from .img2img_tab_extender import Img2imgTabExtender

        image_components = self.get_image_components(*args)
        tab_id = self.get_tab_id(*args)

        init_images_index = (tab_id - Img2imgTabExtender.amount_of_default_tabs) * 2
        mask_index = init_images_index + 1

        self.image = image_components[init_images_index]
        self.mask = image_components[mask_index]

    def get_data_components(self, *args):
        return args[:self.__image_components_start_at]

    def get_image_components(self, *args):
        return args[self.__image_components_start_at:]
    
    def get_tab_id(self, *args):
        return int(self.get_data_components(*args)[0])


@one_time_callable
def register_SdwI2iExtenderScript():
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    script_module = sys.modules[__name__]
    scripts_data.append(ScriptClassData(SdwI2iExtenderScript, script_path, script_dir, script_module))


@one_time_callable
def activate_generation_component_injector():
    add_nasty_patches()


def add_nasty_patches():
    print("[sdwi2iextender]", "Applying img2img patch")
    import_patch = "import sdwi2iextender"
    code_patch = f"""
if (script_instance := sdwi2iextender.get_script_class().img2img_instance) and (script_args := args[script_instance.args_from:script_instance.args_to]) and script_instance.should_intercept_generation(*script_args):
    script_instance.resolve_image_and_mask(*script_args)
    image = script_instance.image
    mask = script_instance.mask
else:
    image = None
    mask = None
"""
    parsed_module = ast.parse(inspect.getsource(img2img))
    parsed_module.body[0:0] = ast.parse(import_patch).body[0:1]

    parsed_function = get_ast_function(parsed_module, "img2img")
    ast_if = get_ast_if_mode(parsed_function)
    last_ast_if = get_last_ast_if(ast_if)
    last_ast_if.orelse[:] = ast.parse(code_patch).body[0:1]
    exec(compile(parsed_module, '<string>', 'exec'), img2img.__dict__)


def get_ast_function(parsed_object, function_name):
    res = [exp for exp in parsed_object.body if getattr(exp, 'name', None) == function_name]
    if not res:
        raise RuntimeError(f'Cannot find function {function_name} in parsed ast')

    return res[0]


def get_ast_if_mode(parsed_img2img_function):
    for node in parsed_img2img_function.body:
        if not hasattr(node, "test"):
            continue
        
        if not hasattr(node.test, "left"):
            continue

        if not hasattr(node.test.left, "id"):
            continue

        if node.test.left.id == "mode":
            return node


def get_last_ast_if(ast_if):
    while(hasattr(ast_if, "orelse") and len(ast_if.orelse) == 1):
        ast_if = ast_if.orelse[0]
    
    return ast_if
