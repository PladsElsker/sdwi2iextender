import base64
import numpy as np
import gradio as gr
from cv2 import imencode
from gradio.context import Context as GradioContext

from .lib.one_time_callable import one_time_callable


def _find_root_block(block):
    root = block
    while root.parent is not None:
        root = root.parent

    return root


class GradioContextSwitch:
    def __init__(self, block):
        self.block = block
        self.root_block = _find_root_block(block)

    def __enter__(self):
        self.previous_root_block = GradioContext.root_block
        GradioContext.root_block = self.root_block

        self.previous_block = GradioContext.block
        GradioContext.block = self.block
        return self

    def __exit__(self, *args, **kwargs):
        GradioContext.block = self.previous_block
        GradioContext.root_block = self.previous_root_block


@one_time_callable
def hijack_gradio_encode_pil_to_base64():
    # from https://github.com/gradio-app/gradio/issues/2635#issuecomment-1423531319
    def encode_pil_to_base64_new(pil_image):
        image_arr = np.asarray(pil_image)
        if image_arr.ndim == 3:
            image_arr = image_arr[:, :, ::-1]

        _, byte_data = imencode('.png', image_arr)
        base64_data = base64.b64encode(byte_data)
        base64_string_opencv = base64_data.decode("utf-8")
        return "data:image/png;base64," + base64_string_opencv

    gr.processing_utils.encode_pil_to_base64 = encode_pil_to_base64_new
