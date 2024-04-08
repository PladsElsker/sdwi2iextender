from .lib.img2img_tab_extender import register_operation_mode
from .lib.operation_mode import OperationMode


def get_script_class():
    from .lib.img2img_component_injector import SdwI2iExtenderScript
    return SdwI2iExtenderScript
