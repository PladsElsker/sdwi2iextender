import gradio as gr


class OperationMode:
    """Operation mode base class for creating custom operation modes in the UI.
    You may create a class that inherits this class to create a custom operation mode. 
    Once created, operation modes need to be manually registered using the register_operation_mode() function. 
    """
    
    show_inpaint_params = True
    """Set to false to hide generation parameters like the img2img or sketch tabs"""

    requested_elem_ids = []
    """List of gradio components to pass to the OperationMode.section() method to customize their behavior"""

    def __init__(self):
        pass
    
    def image_components(self):
        """Method to instantiate the image-mask pair for image generation. 
        This method must return a tuple of gradio image components (image, mask). 
        It is recommended to unrender and re-render the image components in the OperationMode.tab() method. 
        """
        return gr.Image(visible=False), gr.Image(visible=False)

    def tab(self):
        """Method to create the tab component in the UI. Exactly one tab must be created in this function."""
        gr.TabItem(label="", visible=False)

    def section(self, components: list):
        """Method to create the inpaint parameters UI of the operation mode.
        
        Arguments:
        components -- a list of gradio components that were requested using the "requested_elem_ids" class attribute
        """
        pass

    def gradio_events(self, selected: gr.Checkbox):
        """Method to setup the gradio callbacks of all the components related to the operation mode.
        
        Arguments:
        selected -- a hidden gradio checkbox that checks itself when the current operation mode is selected

        You may use the checkbox events to manage the state of the new gradio components depending on if the operation mode is selected or not. 
        """
        pass
