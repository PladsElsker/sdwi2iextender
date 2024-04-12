from dataclasses import dataclass
import functools
import gradio as gr

from modules.scripts import script_callbacks
from modules import ui_loadsave

from ..gradio_helpers import GradioContextSwitch, hijack_gradio_encode_pil_to_base64
from .one_time_callable import one_time_callable
from .img2img_component_injector import activate_injector


new_tab_classes = []


def register_operation_mode(tab_class):
    hijack_gradio_encode_pil_to_base64()
    enable_tab_extender()
    new_tab_classes.append(tab_class)


@dataclass
class TabData:
    tab_index: int
    tab_class: type
    tab_object: object
    selected: gr.Checkbox


class Img2imgTabExtender:
    img2img_tabs_block = None
    inpaint_params_block = None
    amount_of_default_tabs = None
    tab_data_list = []

    @classmethod
    def on_after_component(cls, component, **kwargs):
        elem_id = kwargs.get('elem_id', None)

        if elem_id == 'img2img_batch_inpaint_mask_dir':
            cls.register_img2img_tabs_block(component)

        if elem_id == 'img2img_mask_blur':
            cls.register_inpaint_params_block(component)

        cls.register_requested_elem_ids(component, elem_id)

    @classmethod
    def register_img2img_tabs_block(cls, component):
        cls.img2img_tabs_block = component.parent.parent

    @classmethod
    def register_inpaint_params_block(cls, component):
        cls.inpaint_params_block = component.parent.parent

    @classmethod
    def register_requested_elem_ids(cls, component, elem_id):
        if elem_id is None:
            return

        for tab_class in new_tab_classes:
            if not hasattr(tab_class, '_registered_elem_ids'):
                tab_class._registered_elem_ids = dict()

            if not hasattr(tab_class, 'requested_elem_ids'):
                continue

            if elem_id in tab_class.requested_elem_ids:
                tab_class._registered_elem_ids[elem_id] = component

    @classmethod
    def create_custom_tab_objects(cls, selected_tab_index_component):
        cls.selected_tab_index_component = selected_tab_index_component
        
        cls.tab_data_list = []
        for tab_class in new_tab_classes:
            custom_tab_object = tab_class()
            cls.register_custom_tab_data(-1, tab_class, custom_tab_object, gr.Checkbox(visible=False))

    @classmethod
    def instantiate_custom_tabs(cls):
        cls.register_default_amount_of_tabs()
        for custom_tab in cls.tab_data_list:
            tab_class = custom_tab.tab_class
            custom_tab_object = custom_tab.tab_object
            tab_index = cls._get_current_amount_of_tabs()
            custom_tab.tab_index = tab_index
            
            with GradioContextSwitch(cls.img2img_tabs_block):
                custom_tab_object.tab()
            with GradioContextSwitch(cls.inpaint_params_block):
                custom_tab_object.section(tab_class._registered_elem_ids)

        with GradioContextSwitch(cls.inpaint_params_block):
            img2img_tabs = cls._get_img2img_tabs()
            cls.setup_navigation_events(img2img_tabs)
            for tab_data in cls.tab_data_list:
                tab_data.tab_object.gradio_events(tab_data.selected)

    @classmethod
    def register_default_amount_of_tabs(cls):
        cls.amount_of_default_tabs = cls._get_current_amount_of_tabs()

    @classmethod
    def register_custom_tab_data(cls, tab_index, tab_class, tab_object, selected):
        cls.tab_data_list.append(TabData(tab_index, tab_class, tab_object, selected))

    @classmethod
    def setup_navigation_events(cls, img2img_tabs):
        padded_tab_data_list = [None] * cls.amount_of_default_tabs + cls.tab_data_list
        block_data_iterator = zip(img2img_tabs, padded_tab_data_list, strict=True)

        def update_func(custom_tab):
            tab_class = getattr(custom_tab, 'tab_class', None)
            should_show_inpaint_params = getattr(tab_class, 'show_inpaint_params', True)
            update_inpaint_params = gr.update(visible=should_show_inpaint_params) if custom_tab is not None else gr.update()
            offset = cls.amount_of_default_tabs
            update_selected = [
                gr.update(value=custom_tab is not None and (i + offset)==custom_tab.tab_index) 
                for i in range(len(cls.tab_data_list))
            ]
            return update_inpaint_params, *update_selected
        
        for tab_block, custom_tab in block_data_iterator:
            func_dict = dict(
                fn=functools.partial(update_func, custom_tab=custom_tab),
                inputs=[],
                outputs=[
                    cls.inpaint_params_block,
                    *[tab_data.selected for tab_data in cls.tab_data_list],
                ]
            )

            tab_block.select(**func_dict)
            tab_block.select(
                fn=None,
                inputs=[],
                outputs=[cls.selected_tab_index_component],
                _js="(...args) => [get_tab_index('mode_img2img')]",
            )

    @classmethod
    def _get_current_amount_of_tabs(cls):
        return len(cls._get_img2img_tabs())

    @classmethod
    def _get_img2img_tabs(cls):
        return [
            child
            for child in cls.img2img_tabs_block.children
            if isinstance(child, gr.TabItem)
        ]


@one_time_callable
def enable_tab_extender():
    activate_injector()

    script_callbacks.on_after_component(Img2imgTabExtender.on_after_component)

    original_ui_settings__init__ = ui_loadsave.UiLoadsave.__init__

    def hijack__init__(*args, **kwargs):
        Img2imgTabExtender.instantiate_custom_tabs()
        return original_ui_settings__init__(*args, **kwargs)

    ui_loadsave.UiLoadsave.__init__ = hijack__init__
