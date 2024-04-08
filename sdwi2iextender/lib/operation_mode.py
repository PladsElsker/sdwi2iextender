import gradio as gr


class OperationMode:
    show_inpaint_params = True
    requested_elem_ids = []

    def __init__(self):
        pass

    def image_components(self):
        return gr.Image(visible=False), gr.Image(visible=False)

    def tab(self):
        gr.TabItem(label="", visible=False)

    def section(self, components: list):
        pass

    def gradio_events(self, img2img_tabs: list):
        pass
