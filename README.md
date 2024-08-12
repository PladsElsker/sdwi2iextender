# sdwi2iextender
A python library to help create custom img2img operation modes in A1111.  

## Context
Conflicts can easily arise between different A1111 extensions when creating new operation modes in the img2img section.  
This library suggests an implementation that uniformalizes the creation of new operation modes.  

## Release notes
### 0.2.3
- **Changes:**
    - Added the updated version to the install logs when the Webui updates the library. 
### 0.2.2
- **Changes:**
    - Added a common install script to normalize the install and update procedure of the library. Using the new common install script is optional, but is strongly recommended. Updates to the library are relatively frequent (once every few months). Updating all the extensions that use the library to ensure they are using the latest version was time consuming. Another issue was that it was creating unnecessary commits and issues in the extension repositories, even though the issues are actually related the library itself because the API for custom operation modes has mostly remained unchanged for a while now. The new install script now checks if the library is installed, and forces an update if a new version is available. Forcing an update is probably not the best way to fix this. Custom cli args may be added to the Webui in a future update to allow the user to select a specific version of the library if needed. 
### 0.2.1
- **Bug fixes:**
    - Fixed issue in A1111 `v1.10.1` where the `img2img > img2img` and `img2img > inpaint` operation modes would raise errors due to the script arguments not being passed to the pipeline. 
### 0.2.0
- **Bug fixes:**
    - Fixed issue in A1111 `v1.10` where an anchor component was relocated, preventing custom tabs from being populated.
    - Dropped support for Forge. Starting from this version, sdwi2iextender will no longer support Forge. The reason is that Forge is no longer maintained to closely follow A1111 releases, making it increasingly demanding to maintain support. Forge may still work fine with `v0.1.3` for now, but it will not be actively maintained. 
### 0.1.3
- **Bug fixes:**
    - Added a re-compilation patch that re-compiles the `img2img.py/img2img` function to support both A1111 `v1.8` and `v1.9`. As a side effect, this patch supports Forge as well. The developpment of Forge is in an uncertain state, so the next release of sdwi2iextender may drop Forge support. The next release of A1111, `v1.10`, will add many optimizations akin to Forge, making it less useful to support both UIs at the same time. 

## Install
As of `0.2.2`, the intended way to install the library is to enforce the latest version from `install.py` scripts in extensions:
```py
import launch

if not launch.is_installed("sdwi2iextender"):
    launch.run_pip(f"install sdwi2iextender", f"sdwi2iextender")

from sdwi2iextender import sdwi2iextender_version_manager
sdwi2iextender_version_manager.ensure_latest()
```

Alternatively, you can install it manually for testing purposes:
```
pip install sdwi2iextender
```

# Usage

## Registering a new operation mode
Before creating any UI or behavior, we need to register the operation mode.  
This is done in 2 steps for each new tab that we want to create.  

### Step 1
First, we need to extend the `OperationMode` class:
```py
from sdwi2iextender import OperationMode

class MyOperationMode(OperationMode):
    pass
```

### Step 2
Then, we can add the new operation mode to the list of operation modes by calling the `register_operation_mode` function:
```py
from sdwi2iextender import OperationMode, register_operation_mode

class MyOperationMode(OperationMode):
    pass

register_operation_mode(MyOperationMode)
```

That's it! The new operation mode is now registered with the Webui.  
This won't do anything yet, though. We still need to populate our class with the behavior that we want.  

## Populating an operation mode
There are a few methods that can be overriden, let's look at them one by one.  

### tab
The `tab` method is called with the Gradio context of the img2img tab group.  
This means that you can create a gradio tab in it, and it will be rendered with the other img2img operation tabs:  
```py
class MyOperationTab(OperationMode):
    def tab(self):
        self.tab = gr.TabItem(label='My new tab')

```

> As of version 0.0.1, you need exactly one `gr.TabItem` per operation mode. 
> Adding more than one tab per operation mode in the `tab()` method will result in an error. 
> Not defining the tab in the `tab()` method will result in an error.  

### section
The `section` method is called with the Gradio context of the inpaint parameters.  
You tipically use it to modify the inpaint parameters, add new ones, hide them, etc.  
```py
class MyInpaintParams(OperationMode):
    def section(self, components: list):
        pass
```

Ignore the `components` list for now, we'll look at it later for more complex examples.  
For now, here is how you can add a slider to the inpaint parameters:  
```py
class MyInpaintParams(OperationMode):
    def section(self, components: list):
        self.slider = gr.Slider(label="New slider")
```

### gradio_events
The `gradio_events` method is called when all the new operation modes are finished being created in the UI.  
This is useful to setup any new event you want between Gradio components. The `selected: gr.Checkbox` argument is a special component that changes to `True` when this operation mode's tab is selected in he UI, and `False` otherwise.  
You can use it to display/hide components related to your new operation mode if the tab is selected in the UI. 
```py
class MyOperationMode(OperationMode):
    def tab(self):
        self.tab = gr.TabItem(label='My new tab')

    def section(self, components: list):
        self.slider = gr.Slider(label="New slider")

    def gradio_events(self, selected: gr.Checkbox):
        selected.change(
            fn=lambda show_slider: gr.update(visible=show_slider),
            inputs=[selected],
            outputs=[self.slider],
        )
```

## Sending an image-mask pair to the img2img diffusion pipeline
So far, we've only been looking at how to create a new operation mode's UI.  
How do we actually inject new image and mask components into the inpaint pipeline to generate images when our tab is selected?  

For technical reasons that go beyond this documentation, the creation of the image and mask components used for inpainting needs to be done earlier than the actual creation of the operation mode's UI (so before calling `tab` and `section`).  

This is why the `image_components` method exists. We can return the image and mask components that the img2img processing pipeline will use when our tab is selected:  

```py
class MyOperationMode(OperationMode):
    def image_components(self) -> tuple[gr.Image]:
        self.image_component = gr.Image(label="my_image_component", source="upload", interactive=True, type="pil")
        self.mask_component = gr.Image(label="my_mask_component", source="upload", interactive=True, type="pil")
        self.image_component.unrender()
        self.mask_component.unrender()
        return self.image_component, self.mask_component

    def tab(self):
        with gr.TabItem(label='My new tab') as self.tab:
            gr.Row():
                self.image_component.render()

            gr.Row():
                self.mask_component.render()
```
> Note that the `image_components` method **expects 2 gradio components to be returned**: `image, mask`.  
> The first one should be the initial image, and the second one should be the inpainting mask.  
> For example, if you don't need a mask for your operation mode, you will still need to provide a black image component for the second return value.  

As shown in this code snipet, the `unrender` and `render` gradio functions can be used to make sure the image and mask components are displayed at the correct location in the UI, even though they are being created earlier in the pipeline.  

## This documentation is a WIP
I encourage you to look at the source code if you want to learn more about how to use this library!  

You can also look at these extensions that use sdwi2iextender:
- [Inpaint difference](https://github.com/John-WL/sd-webui-inpaint-difference)
- [Inpaint background](https://github.com/John-WL/sd-webui-inpaint-background)
