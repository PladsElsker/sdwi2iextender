import os
import sys
import gradio as gr
import inspect

import modules.scripts as scripts
from modules.scripts import ScriptClassData, scripts_data
from modules import img2img

from .one_time_callable import one_time_callable


IMG2IMG_MODE_INDEX = 0
IMG2IMG_INPAINT_OPERATION_MODE_INDEX = 2
IMG2IMG_INIT_IMG_WITH_MASK_INDEX = 6


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

        return self.get_tab_id(*args) >= Img2imgTabExtender.amount_of_default_tabs

    def get_image_mask_dict(self, *args):
        from .img2img_tab_extender import Img2imgTabExtender

        image_components = self.get_image_components(*args)
        tab_id = self.get_tab_id(*args)

        init_images_index = (tab_id - Img2imgTabExtender.amount_of_default_tabs) * 2
        mask_index = init_images_index + 1

        return {
            "image": image_components[init_images_index],
            "mask": image_components[mask_index],
        }

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
    IMG2IMG_ARGUMENT_COUNT = len(inspect.signature(img2img.img2img).parameters)
    IMG2IMG_HIJACK_ARGUMENT_OFFSET = IMG2IMG_ARGUMENT_COUNT - 3

    original_img2img = img2img.img2img

    def hijack_img2img(id_task: str, request: gr.Request, *args):
        args = list(args)
        all_scripts_args = args[IMG2IMG_HIJACK_ARGUMENT_OFFSET:]

        script_instance = SdwI2iExtenderScript.img2img_instance
        script_args = all_scripts_args[script_instance.args_from:script_instance.args_to]
        if script_instance.should_intercept_generation(*script_args):
            args[IMG2IMG_MODE_INDEX] = IMG2IMG_INPAINT_OPERATION_MODE_INDEX
            args[IMG2IMG_INIT_IMG_WITH_MASK_INDEX] = script_instance.get_image_mask_dict(*script_args)
        
        return original_img2img(id_task, request, *args)

    img2img.img2img = hijack_img2img
