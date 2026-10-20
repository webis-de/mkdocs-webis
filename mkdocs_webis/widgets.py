"""
Static, disabled HTML for Jupyter widgets (ipywidgets), from the widget state saved in a notebook.

Widgets need a running kernel to be interactive, so the pages show them as they were when the notebook was saved.
Unknown widgets are skipped.
"""

from collections.abc import Callable, Mapping
from html import escape
from math import log
from re import DOTALL, compile as re_compile
from typing import Any, Final

from nbconvert.filters import strip_ansi

WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"
WIDGET_STATE_MIMETYPE = "application/vnd.jupyter.widget-state+json"
_MODEL_PREFIX = "IPY_MODEL_"
_SCOPED_STYLE: Final = re_compile(r"<style scoped>.*?</style>\n?", DOTALL)


def html_output(html: str) -> str:
    """
    Wrap an HTML output, and use the theme's table style for data frames (which only applies to tables without a class).
    """
    html = html.replace(' border="1" class="dataframe"', "")
    # The data frame style (for the class) would apply to all tables, as browsers ignore `scoped`.
    html = _SCOPED_STYLE.sub("", html)
    return f'<div class="jupyter-html">\n{html}\n</div>'


class WidgetRenderer:
    """
    Render widgets from the widget state of a notebook.
    """

    def __init__(self, metadata: Mapping[str, Any]) -> None:
        state = metadata.get("widgets", {}).get(WIDGET_STATE_MIMETYPE, {})
        self._models: Mapping[str, Any] = state.get("state", {})

    def render_view(self, view: Mapping[str, Any]) -> str:
        """
        Render a widget view (output), or return an empty string if the widget is unknown.
        """
        html = self._render(view.get("model_id", ""))
        return f'<div class="jupyter-widgets">\n{html}\n</div>' if html else ""

    def _render(self, model_id: str) -> str:
        model = self._models.get(model_id.removeprefix(_MODEL_PREFIX))
        if model is None:
            return ""
        name = model.get("model_name", "").removesuffix("Model")
        state = model.get("state", {})
        render = self._renderers.get(name)
        if render is None:
            return ""
        return render(self, state)

    def _box(self, state: Mapping[str, Any], direction: str) -> str:
        children = "".join(self._render(child) for child in state.get("children", []))
        return (
            f'<div class="jupyter-widget jupyter-widget--{direction}">{children}</div>'
        )

    def _hbox(self, state: Mapping[str, Any]) -> str:
        return self._box(state, "hbox")

    def _vbox(self, state: Mapping[str, Any]) -> str:
        return self._box(state, "vbox")

    def _slider(self, state: Mapping[str, Any]) -> str:
        value = state.get("value", 0)
        return _control(
            state,
            f'<input type="range" min="{state.get("min", 0)}" max="{state.get("max", 100)}" '
            f'step="{state.get("step") or "any"}" value="{value}" disabled>',
            _readout(state, value),
        )

    def _log_slider(self, state: Mapping[str, Any]) -> str:
        # The slider's range is in exponents of the base.
        value = state.get("value", 1)
        exponent = log(value, state.get("base", 10)) if value > 0 else 0
        return _control(
            state,
            f'<input type="range" min="{state.get("min", 0)}" max="{state.get("max", 4)}" '
            f'step="{state.get("step") or "any"}" value="{exponent}" disabled>',
            _readout(state, value),
        )

    def _range_slider(self, state: Mapping[str, Any]) -> str:
        lower, upper = state.get("value", (0, 0))
        return _control(
            state,
            f'<input type="range" min="{state.get("min", 0)}" max="{state.get("max", 100)}" '
            f'step="{state.get("step") or "any"}" value="{lower}" disabled>',
            f"{_readout(state, lower)}–{_readout(state, upper)}",
        )

    def _progress(self, state: Mapping[str, Any]) -> str:
        minimum = state.get("min", 0)
        maximum = state.get("max", 100) - minimum
        value = state.get("value", 0) - minimum
        style = escape(state.get("bar_style") or "", quote=True)
        return _control(
            state,
            f'<progress class="jupyter-widget__progress--{style}" '
            f'max="{maximum}" value="{value}"></progress>',
        )

    def _text(self, state: Mapping[str, Any]) -> str:
        value = escape(str(state.get("value", "")), quote=True)
        placeholder = escape(state.get("placeholder", ""), quote=True)
        return _control(
            state,
            f'<input type="text" value="{value}" placeholder="{placeholder}" disabled>',
        )

    def _textarea(self, state: Mapping[str, Any]) -> str:
        value = escape(state.get("value", ""))
        return _control(state, f"<textarea disabled>{value}</textarea>")

    def _checkbox(self, state: Mapping[str, Any]) -> str:
        checked = " checked" if state.get("value") else ""
        return (
            '<label class="jupyter-widget jupyter-widget--checkbox">'
            f'<input type="checkbox" disabled{checked}>{_description(state)}</label>'
        )

    def _button(self, state: Mapping[str, Any]) -> str:
        pressed = " jupyter-widget__button--pressed" if state.get("value") else ""
        label = escape(state.get("description", ""))
        return (
            f'<button class="jupyter-widget jupyter-widget__button{pressed}" '
            f'type="button" disabled>{label}</button>'
        )

    def _dropdown(self, state: Mapping[str, Any]) -> str:
        selected = _selected(state)
        options = "".join(
            f"<option{' selected' if index in selected else ''}>{escape(label)}</option>"
            for index, label in enumerate(state.get("_options_labels", []))
        )
        multiple = (
            " multiple" if state.get("_model_name") == "SelectMultipleModel" else ""
        )
        return _control(state, f"<select disabled{multiple}>{options}</select>")

    def _radio_buttons(self, state: Mapping[str, Any]) -> str:
        selected = _selected(state)
        options = "".join(
            f'<label><input type="radio" disabled{" checked" if index in selected else ""}>'
            f"{escape(label)}</label>"
            for index, label in enumerate(state.get("_options_labels", []))
        )
        return _control(state, f'<span class="jupyter-widget--vbox">{options}</span>')

    def _toggle_buttons(self, state: Mapping[str, Any]) -> str:
        selected = _selected(state)
        buttons = "".join(
            '<button class="jupyter-widget__button'
            f'{" jupyter-widget__button--pressed" if index in selected else ""}" '
            f'type="button" disabled>{escape(label)}</button>'
            for index, label in enumerate(state.get("_options_labels", []))
        )
        return _control(state, f'<span class="jupyter-widget--hbox">{buttons}</span>')

    def _html(self, state: Mapping[str, Any]) -> str:
        return _control(state, f"<span>{state.get('value', '')}</span>")

    def _label(self, state: Mapping[str, Any]) -> str:
        return _control(state, f"<span>{escape(state.get('value', ''))}</span>")

    def _output(self, state: Mapping[str, Any]) -> str:
        outputs = "".join(_render_output(output) for output in state.get("outputs", []))
        return f'<div class="jupyter-widget jupyter-widget--output">{outputs}</div>'

    _renderers: Mapping[str, Callable[["WidgetRenderer", Mapping[str, Any]], str]] = {
        "Box": _hbox,
        "HBox": _hbox,
        "VBox": _vbox,
        "GridBox": _hbox,
        "IntSlider": _slider,
        "FloatSlider": _slider,
        "FloatLogSlider": _log_slider,
        "IntRangeSlider": _range_slider,
        "FloatRangeSlider": _range_slider,
        "IntProgress": _progress,
        "FloatProgress": _progress,
        "Text": _text,
        "IntText": _text,
        "FloatText": _text,
        "BoundedIntText": _text,
        "BoundedFloatText": _text,
        "Combobox": _text,
        "Textarea": _textarea,
        "Checkbox": _checkbox,
        "ToggleButton": _button,
        "Button": _button,
        "Dropdown": _dropdown,
        "Select": _dropdown,
        "SelectMultiple": _dropdown,
        "RadioButtons": _radio_buttons,
        "ToggleButtons": _toggle_buttons,
        "HTML": _html,
        "HTMLMath": _html,
        "Label": _label,
        "Output": _output,
    }


def _description(state: Mapping[str, Any]) -> str:
    description = state.get("description", "")
    if not state.get("description_allow_html"):
        description = escape(description)
    return description


def _control(state: Mapping[str, Any], control: str, readout: str | None = None) -> str:
    """
    A control with its description (before) and readout (after), like in Jupyter.
    """
    description = _description(state)
    html = '<span class="jupyter-widget jupyter-widget--control">'
    if description:
        html += f'<span class="jupyter-widget__description">{description}</span>'
    html += control
    if readout is not None and state.get("readout", True):
        html += f'<span class="jupyter-widget__readout">{escape(readout)}</span>'
    return html + "</span>"


def _readout(state: Mapping[str, Any], value: Any) -> str:
    try:
        return format(value, state.get("readout_format", ""))
    except (TypeError, ValueError):
        return str(value)


def _selected(state: Mapping[str, Any]) -> set[int]:
    index = state.get("index")
    if index is None:
        return set()
    return set(index) if isinstance(index, list) else {index}


def _render_output(output: Mapping[str, Any]) -> str:
    """
    Render an output of an output widget as HTML (as it is nested in the widget's HTML).
    """
    if output.get("output_type") == "stream":
        if output.get("name") != "stdout":
            return ""
        return _pre(output.get("text", ""))
    if output.get("output_type") == "error":
        return _pre("\n".join(output.get("traceback", [])))
    data = output.get("data", {})
    if "text/html" in data:
        return html_output(_text_data(data["text/html"]))
    for mimetype in ("image/png", "image/jpeg"):
        if mimetype in data:
            return f'<img src="data:{mimetype};base64,{_text_data(data[mimetype])}">'
    if "text/plain" in data:
        return _pre(_text_data(data["text/plain"]))
    return ""


def _text_data(data: str | list[str]) -> str:
    return data if isinstance(data, str) else "".join(data)


def _pre(text: str) -> str:
    return f"<pre><code>{escape(strip_ansi(text).strip())}</code></pre>"
