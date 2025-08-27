__version__ = "1.0.0"

# Global pointer to the main application window.
main_window = None

# Global pointer to the currently displayed page widget.
# This can hold a JdAreaPage, JdIdPage, JdExtPage, JdDirectoryListPage or JdDirectoryPage.
current_page = None

# Simple in-process navigation history. Pushing happens on navigate_to();
# Backspace should pop via go_back().
_history: list[tuple[str, dict]] = []
_forward: list[tuple[str, dict]] = []

def _describe_page(page) -> tuple[str, dict]:
    name = type(page).__name__
    kw: dict = {}
    try:
        if name == "JdAreaPage":
            kw = {}
        elif name == "JdIdPage":
            kw = {
                "parent_uuid": getattr(page, "parent_uuid", None),
                "jd_area": getattr(page, "current_jd_area", None),
            }
        elif name == "JdExtPage":
            kw = {
                "parent_uuid": getattr(page, "parent_uuid", None),
                "jd_area": getattr(page, "current_jd_area", None),
                "jd_id": getattr(page, "current_jd_id", None),
                "grandparent_uuid": getattr(page, "grandparent_uuid", None),
            }
        elif name == "JdDirectoryListPage":
            kw = {
                "parent_uuid": getattr(page, "parent_uuid", None),
                "jd_area": getattr(page, "current_jd_area", None),
                "jd_id": getattr(page, "current_jd_id", None),
                "jd_ext": getattr(page, "current_jd_ext", None),
                "grandparent_uuid": getattr(page, "grandparent_uuid", None),
                "great_grandparent_uuid": getattr(page, "great_grandparent_uuid", None),
            }
        elif name == "JdDirectoryPage":
            kw = {
                "directory_id": getattr(page, "directory_id", None),
                "parent_uuid": getattr(page, "parent_uuid", None),
                "jd_area": getattr(page, "current_jd_area", None),
                "jd_id": getattr(page, "current_jd_id", None),
                "jd_ext": getattr(page, "current_jd_ext", None),
                "grandparent_uuid": getattr(page, "grandparent_uuid", None),
                "great_grandparent_uuid": getattr(page, "great_grandparent_uuid", None),
                "ext_label": getattr(page, "ext_label", None),
            }
    except Exception:
        kw = {}
    return (name, kw)

def _create_page(desc: tuple[str, dict]):
    name, kw = desc
    # Import locally to avoid circular imports at module load time
    from .jd_area_page import JdAreaPage
    from .jd_id_page import JdIdPage
    from .jd_ext_page import JdExtPage
    from .jd_directory_list_page import JdDirectoryListPage
    from .jd_directory_page import JdDirectoryPage

    if name == "JdAreaPage":
        return JdAreaPage()
    if name == "JdIdPage":
        return JdIdPage(**kw)
    if name == "JdExtPage":
        return JdExtPage(**kw)
    if name == "JdDirectoryListPage":
        return JdDirectoryListPage(**kw)
    if name == "JdDirectoryPage":
        return JdDirectoryPage(**kw)
    # Fallback to area page
    return JdAreaPage()

def navigate_to(page) -> None:
    """Navigate to a new page, preserving the current one in history.

    Uses QMainWindow.takeCentralWidget() to detach the existing page without
    deletion so it can be restored later.
    """
    global current_page
    # Push a descriptor of the current page onto history
    if current_page is not None:
        try:
            _history.append(_describe_page(current_page))
        except Exception:
            pass
    # Navigating to a new page clears the forward stack
    _forward.clear()
    # Detach and delete the existing central widget, then show the new page
    if main_window is not None:
        old = main_window.takeCentralWidget()
        try:
            if old is not None:
                old.deleteLater()
        except Exception:
            pass
        main_window.setCentralWidget(page)
    current_page = page

def go_back() -> None:
    """Go back to the previous page from history.

    Detaches and schedules deletion of the current central widget to avoid
    keeping unused widgets alive indefinitely.
    """
    global current_page
    if main_window is None or not _history:
        return
    cur = main_window.takeCentralWidget()
    try:
        if cur is not None:
            # Push current onto forward stack before deleting
            if current_page is not None:
                try:
                    _forward.append(_describe_page(current_page))
                except Exception:
                    pass
            cur.deleteLater()
    except Exception:
        pass
    desc = _history.pop()
    prev = _create_page(desc)
    main_window.setCentralWidget(prev)
    current_page = prev

def go_forward() -> None:
    global current_page
    if main_window is None or not _forward:
        return
    cur = main_window.takeCentralWidget()
    try:
        if cur is not None:
            # Push current onto back stack before deleting
            if current_page is not None:
                try:
                    _history.append(_describe_page(current_page))
                except Exception:
                    pass
            cur.deleteLater()
    except Exception:
        pass
    desc = _forward.pop()
    nxt = _create_page(desc)
    main_window.setCentralWidget(nxt)
    current_page = nxt
