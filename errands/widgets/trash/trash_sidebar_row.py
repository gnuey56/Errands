# Copyright 2024 Vlad Krupinskii <mrvladus@yandex.ru>
# SPDX-License-Identifier: MIT

from __future__ import annotations


from gi.repository import Gio, Gtk, Gdk  # type:ignore

from errands.lib.gsettings import GSettings
from errands.lib.logging import Log
from errands.state import State
from errands.widgets.shared.components.boxes import ErrandsBox
from errands.widgets.task.task import Task


class TrashSidebarRow(Gtk.ListBoxRow):
    def __init__(self) -> None:
        super().__init__()
        self.name = "errands_trash_page"
        State.trash_sidebar_row = self
        self.__add_actions()
        self.__build_ui()

    def __build_ui(self) -> None:
        self.props.height_request = 50
        self.add_css_class("sidebar-item")
        self.add_css_class("sidebar-item-trash")
        self.connect("activate", self._on_row_activated)

        # Drop controller
        drop_ctrl: Gtk.DropTarget = Gtk.DropTarget.new(
            type=Task, actions=Gdk.DragAction.MOVE
        )
        drop_ctrl.connect("drop", self._on_task_drop)
        self.add_controller(drop_ctrl)

        # Icon
        self.icon = Gtk.Image(icon_name="errands-trash-symbolic")

        # Title
        self.label: Gtk.Label = Gtk.Label(
            hexpand=True, halign=Gtk.Align.START, label=_("Trash")
        )

        # Counter
        self.size_counter = Gtk.Label(css_classes=["dim-label", "caption"])

        # Menu
        menu: Gio.Menu = Gio.Menu()
        menu.append(label=_("Clear"), detailed_action="trash_row.rename")
        menu.append(label=_("Restore"), detailed_action="trash_row.restore")
        menu_btn: Gtk.MenuButton = Gtk.MenuButton(
            menu_model=menu,
            icon_name="errands-more-symbolic",
            css_classes=["flat"],
            valign=Gtk.Align.CENTER,
        )

        self.set_child(
            ErrandsBox(
                spacing=12,
                margin_start=6,
                children=[self.label, self.size_counter, menu_btn],
            )
        )

    def __add_actions(self) -> None:
        self.group: Gio.SimpleActionGroup = Gio.SimpleActionGroup()
        self.insert_action_group(name="trash_row", group=self.group)

        def __create_action(name: str, callback: callable) -> None:
            action: Gio.SimpleAction = Gio.SimpleAction(name=name)
            action.connect("activate", callback)
            self.group.add_action(action)

        __create_action("clear", lambda *_: State.trash_page.on_trash_clear())
        __create_action("restore", lambda *_: State.trash_page.on_trash_restore())

    def update_ui(self) -> None:
        # Update trash
        State.trash_page.update_ui()

        # Get trash size
        size: int = len(State.trash_page.trash_items)

        # Update actions state
        self.group.lookup_action("clear").set_enabled(size > 0)
        self.group.lookup_action("restore").set_enabled(size > 0)

        # Update icon name
        self.icon.set_from_icon_name(
            f"errands-trash{'-full' if size > 0 else ''}-symbolic"
        )

        # Update subtitle
        self.size_counter.set_label("" if size == 0 else str(size))

    def _on_row_activated(self, *args) -> None:
        Log.debug("Sidebar: Open Trash")

        State.view_stack.set_visible_child_name("errands_trash_page")
        State.split_view.set_show_content(True)
        GSettings.set("last-open-list", "s", "errands_trash_page")

    def _on_task_drop(self, _d, task: Task, _x, _y) -> None:
        task.delete()
