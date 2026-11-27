"""Which GTK 3 CSS nodes are which XP control: selectors shared by the XP themes' generators.

`boost` is the theme's always-true filter string (gtkcss.boost), which the selectors carry to
out-rank base themes' long selectors.
"""


def push_buttons(boost):
    """Push buttons only: not caption buttons, flat (toolbar/inline) buttons, combo box buttons
    (drop-down fields) or the arrows inside spin buttons and scrollbars (.up/.down).

    GTK 3 marks a button .text-button (label only) or .image-button (icon only); one with an
    icon *and* a label gets neither class, nor do file, font, colour and popup-menu buttons. The
    third selector catches those, with fewer filters so all three rank the same. Tree view column
    headers are class-less too: a theme's header rule must out-rank this one."""
    filters = [f + ")" for f in boost.split(")") if f]
    fewer = "".join(filters[:-3])
    return (f"button.text-button:not(.flat):not(.titlebutton):not(.combo){boost}, "
            f"button.image-button:not(.flat):not(.titlebutton):not(.combo){boost}, "
            f"button:not(.text-button):not(.image-button):not(.flat):not(.titlebutton):not(.combo):not(.up):not(.down)"
            f"{fewer}")
