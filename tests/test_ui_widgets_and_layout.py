from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_widget_surface_contains_interactive_controls():
    source = (ROOT / "libs/ui/widgets.kl").read_text()
    for symbol in ("ui_text_input", "ui_checkbox", "ui_scrollbar"):
        assert f"fn " in source and symbol in source
    assert "max_scroll" in source
    assert "mouse_released" in source


def test_layout_row_and_column_keep_padding_and_spacing():
    source = (ROOT / "libs/ui/layout.kl").read_text()
    assert "UILayoutDirection" in source
    assert "layout_begin_row" in source
    assert "layout_begin_column" in source
    assert "layout->cursor_x = layout->cursor_x + requested_width + layout->spacing" in source
    assert "layout->cursor_y = layout->cursor_y + requested_height + layout->spacing" in source

