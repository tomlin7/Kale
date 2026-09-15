from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_pic_remaps_vectors_and_masks_irqs():
    source = (ROOT / "os/kernel/pic.kl").read_text()
    assert "pic_remap" in source
    assert "pic_set_mask" in source
    assert "pic_clear_mask" in source
    assert "master_offset + irq" in source
    assert "slave_offset + (irq - 8)" in source


def test_gdt_encodes_descriptors_and_initializes_tss():
    source = (ROOT / "os/kernel/gdt.kl").read_text()
    assert "gdt_set_entry" in source
    assert "state->tss.rsp0" in source
    assert "state->tss.io_map_base" in source


def test_keyboard_has_set_one_decoder_and_circular_queue():
    source = (ROOT / "os/drivers/kbd.kl").read_text()
    assert "kbd_scancode_to_ascii" in source
    assert "kbd_handle_scancode" in source
    assert "KBD_QUEUE_CAPACITY" in source
    assert "% 64" in source
