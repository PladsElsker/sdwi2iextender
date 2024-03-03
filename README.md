# sdwi2iextender
A python library to help create custom img2img operation modes in A1111. 

# Context
Conflicts can easily arise between different A1111 extensions when creating new operation modes in the img2img section.  
This library suggests an implementation that uniformalizes the creation of new operation modes.  

# Install
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
    def tab(self, ):
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
This is useful to setup any new event you want between Gradio components:  
```py
class MyOperationMode(OperationMode):
    def tab(self):
        self.tab = gr.TabItem(label='My new tab')

    def section(self, components: list):
        self.slider = gr.Slider(label="New slider")

    def gradio_events(self, img2img_tabs: list):
        self.tab.select(fn=lambda slider_value: setattr(self, "slider_value", slider_value), inputs=[self.slider], outputs=[])
```

### This documentation is a WIP
I encourage you to look at the source code if you want to learn more about how to use this library!  
