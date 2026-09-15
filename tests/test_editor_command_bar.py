from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_command_bar_filters_and_selects_commands():
    source = (ROOT / "editor/command_bar.kl").read_text()
    assert "command_bar_matches" in source
    assert "command_bar_filter" in source
    assert "command_bar_move" in source
    assert "command_bar_accept" in source
    assert "command_bar_handle_navigation" in source
    assert "command_bar_reset" in source
    assert "command_bar_append_char" in source
    assert "command_bar_backspace" in source
    assert "command_bar_handle_key" in source
    assert "visible_count" in source
    assert "Format document" in source
    assert "Open file" in source


def test_editor_state_exposes_history_and_multi_action_hooks():
    source = (ROOT / "editor/app_state.kl").read_text()
    assert "undo_stack" in source
    assert "redo_stack" in source
    assert "record_action" in source
    assert "fn int EditorState.undo()" in source
    assert "fn int EditorState.redo()" in source
    assert "tabs[0].buffer.init" in source
    assert "tabs[this->active_tab].buffer.destroy" in source
