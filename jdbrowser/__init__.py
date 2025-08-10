__version__ = "1.0.0"

"""Package level state for the UI pages.

``current_page`` holds a reference to the page that is currently visible.
``page_stack`` keeps the previously shown pages so they can be restored without
being reconstructed, allowing faster navigation between pages.
"""

# Global pointer to the currently displayed page instance. This can hold a
# ``JdAreaPage``, ``JdIdPage`` or ``JdExtPage``.
current_page = None

# Stack of previously visited pages to enable reusing them when navigating
# back.  This avoids recreating the heavy Qt widgets each time, reducing the
# perceived slowness when swapping between pages.
page_stack = []
