__version__ = "1.0.0"

"""Package level state for the UI pages.

``current_page`` holds a reference to the page that is currently visible.
``page_stack`` keeps the previously shown pages so they can be restored without
being reconstructed, allowing faster navigation between pages.
``page_cache`` stores previously constructed pages keyed by an identifier so
that descending into a recently visited page can reuse it immediately.
"""

# Global pointer to the currently displayed page instance. This can hold a
# ``JdAreaPage``, ``JdIdPage`` or ``JdExtPage``.
current_page = None

# Stack of previously visited pages to enable reusing them when navigating
# back.  This avoids recreating the heavy Qt widgets each time, reducing the
# perceived slowness when swapping between pages.
page_stack = []

# Cache of instantiated pages keyed by (type, identifier).  This allows
# descending into a previously shown page without reconstructing it.
page_cache = {}
