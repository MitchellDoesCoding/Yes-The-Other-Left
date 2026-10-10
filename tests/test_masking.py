from PIL import Image

from yes_other_left.skindeep_masking import MaskSpec, apply_mask


def test_bottom_mask_is_applied_to_copy():
    source = Image.new("RGB", (100, 100), "red")
    output = apply_mask(source, MaskSpec("DLB_TEST", mask_preset="bottom", bottom_mask_pct=20))
    assert source.getpixel((50, 90)) == (255, 0, 0)
    assert output.getpixel((50, 90)) == (128, 128, 128)
    assert output.getpixel((50, 10)) == (255, 0, 0)


def test_right_mask():
    source = Image.new("RGB", (100, 100), "white")
    output = apply_mask(source, MaskSpec("DLB_TEST", mask_preset="right", right_mask_pct=18, mask_color="black"))
    assert output.getpixel((90, 50)) == (0, 0, 0)
    assert output.getpixel((10, 50)) == (255, 255, 255)
