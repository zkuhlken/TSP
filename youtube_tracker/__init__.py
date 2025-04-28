import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "youtube_tracker",
    path=os.path.dirname(__file__)
)

def youtube_tracker():
    return _component_func(default={"time": 0})
