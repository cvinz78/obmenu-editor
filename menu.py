#!/usr/bin/env python3

# Obmenu-Editor (PyQt6 Edition)
# Copyright (C) 2026 [cvinz78]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import configparser
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PyQt6.QtCore import Qt, QItemSelectionModel
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QHeaderView,
    QAbstractItemView, QTextEdit
)

APP_NAME = "Obmenu-Editor"
DEFAULT_MENU = "menu.xml"

OPENBOX_CONFIG = Path.home() / ".config" / "openbox"
DEFAULT_MENU_PATH = OPENBOX_CONFIG / DEFAULT_MENU

OBM_CONFIG_DIR = Path.home() / ".config" / "obmenu-editor"
OBM_CONFIG_FILE = OBM_CONFIG_DIR / "settings.ini"
OBM_HELP_FILE = OBM_CONFIG_DIR / "hilfe.txt"

OPENBOX_NS = "http://openbox.org/"
ET.register_namespace("", OPENBOX_NS)

DEFAULT_HELP_TEXT = """=== OBMENU-EDITOR HILFE & ANLEITUNG ===

Dienste und Funktionen dieses Editors:

1. ELEMENTE EINFÜGEN:
   - Neue Menüs, Apps, Trenner oder Starter (.desktop) werden exakt an der 
     aktuellen Position des Cursors eingefügt.
   - Wenn ein Untermenü markiert ist, wird das Element darin eingeordnet.

2. ELEMENTE VERSCHIEBEN:
   - Mit den Buttons ▲ und ▼ können einzelne ausgewählte Einträge für die Feinjustierung verschoben werden (nur für jeweils einen Eintrag wirksam).
   - Per Drag & Drop können Elemente direkt per Maus an neue Positionen gezogen werden.
   - Es können mehrere Elemente gleichzeitig markiert werden (Strg + Klick oder Shift + Klick).

3. THEMES UND SPRACHEN:
   - Wähle zwischen den Themes Creamy, Darkmode und BlueMoon.
   - Wechsel jederzeit zwischen Deutsch (DE) und Englisch (EN).
   - Speichere deine bevorzugten Einstellungen dauerhaft über das Einstellungen-Menü.

4. WERKZEUGE:
   - XML validieren: Prüft die menu.xml auf Validität (mittels xmllint).
   - Openbox neu laden: Wendet die Speicherung direkt auf den Openbox-WM an.
"""

DEFAULT_HELP_TEXT_EN = """=== OBMENU-EDITOR HELP & MANUAL ===

Services and features of this editor:

1. INSERTING ELEMENTS:
   - New menus, apps, separators, or starters (.desktop) are inserted exactly at the current cursor position.
   - If a sub-menu is selected, the element is placed inside it.

2. MOVING ELEMENTS:
   - Using the ▲ and ▼ buttons, individual selected items can be moved for fine-tuning (effective for a single item only).
   - Via Drag & Drop, elements can be dragged directly to new positions using the mouse.
   - Multiple items can be selected simultaneously (Ctrl + Click or Shift + Click).

3. THEMES AND LANGUAGES:
   - Choose between Creamy, Darkmode, and BlueMoon themes.
   - Switch between German (DE) and English (EN) at any time.
   - Save your preferred settings permanently via the Settings menu.

4. TOOLS:
   - Validate XML: Checks menu.xml for validity (using xmllint).
   - Reload Openbox: Applies storage directly to the Openbox window manager.
"""

STYLES = {
    "creamy": """
        QMainWindow, QDialog { background-color: #e6decc; color: #111111; }
        QWidget { background-color: #e6decc; color: #111111; }
        QTreeWidget, QLineEdit, QComboBox, QTextEdit { background-color: #ffffff; color: #111111; border: 1px solid #aaaaaa; }
        QPushButton { background-color: #dddddd; color: #111111; border: 1px solid #aaaaaa; padding: 6px; border-radius: 3px; }
        QPushButton:hover { background-color: #4a78a8; color: #ffffff; }
        QHeaderView::section { background-color: #e7e7e7; color: #111111; border: 1px solid #aaaaaa; padding: 4px; }
        QStatusBar { background-color: #dddddd; color: #111111; }
        QMenuBar, QMenu { background-color: #ffffff; color: #111111; border: 1px solid #aaaaaa; }
        QMenuBar::item:selected, QMenu::item:selected { background-color: #4a78a8; color: #ffffff; }
    """,
    "dark": """
        QMainWindow, QDialog { background-color: #151515; color: #9cff9c; }
        QWidget { background-color: #151515; color: #9cff9c; }
        QTreeWidget, QLineEdit, QComboBox, QTextEdit { background-color: #181818; color: #9cff9c; border: 1px solid #3c3c3c; }
        QPushButton { background-color: #292929; color: #9cff9c; border: 1px solid #3c3c3c; padding: 6px; border-radius: 3px; }
        QPushButton:hover { background-color: #2d4a3e; color: #9cff9c; }
        QHeaderView::section { background-color: #202020; color: #9cff9c; border: 1px solid #3c3c3c; padding: 4px; }
        QStatusBar { background-color: #202020; color: #9cff9c; }
        QMenuBar, QMenu { background-color: #202020; color: #9cff9c; border: 1px solid #3c3c3c; }
        QMenuBar::item:selected, QMenu::item:selected { background-color: #2d4a3e; color: #9cff9c; }
    """,
    "bluemoon": """
        QMainWindow, QDialog { background-color: #071a33; color: #fff3a6; }
        QWidget { background-color: #071a33; color: #fff3a6; }
        QTreeWidget, QLineEdit, QComboBox, QTextEdit { background-color: #081d38; color: #fff3a6; border: 1px solid #24517e; }
        QPushButton { background-color: #12345e; color: #fff3a6; border: 1px solid #24517e; padding: 6px; border-radius: 3px; }
        QPushButton:hover { background-color: #1a3d61; color: #fff3a6; }
        QHeaderView::section { background-color: #0b2447; color: #fff3a6; border: 1px solid #24517e; padding: 4px; }
        QStatusBar { background-color: #0b2447; color: #fff3a6; }
        QMenuBar, QMenu { background-color: #0b2447; color: #fff3a6; border: 1px solid #24517e; }
        QMenuBar::item:selected, QMenu::item:selected { background-color: #1a3d61; color: #fff3a6; }
    """
}

TEXTS = {
    "de": {
        "file": "Datei", "new_menu": "Neue Menü.xml", "open": "Öffnen...", "save": "Speichern", "save_as": "Speichern Unter...", "exit": "Beenden",
        "tools": "Werkzeuge", "validate": "XML validieren", "reload": "Openbox neu laden",
        "view": "Themes", "creamy": "Creamy", "dark": "Darkmode", "bluemoon": "BlueMoon",
        "settings": "Einstellungen", "save_settings": "Einstellungen speichern", "language": "Sprache", "german": "DE", "english": "EN",
        "help": "Hilfe", "about": "Über", "help_doc": "Anleitung (hilfe.txt)",
        "menu": "Menü", "app": "App", "separator": "Trenner", "edit": "Bearbeiten", "delete": "Löschen",
        "up": "▲", "down": "▼", "starter": "Starter", "tree_title": "Openbox Menü",
        "ready": "Bereit", "loaded": "Geladen: {0}", "saved": "Gespeichert",
        "saved_menu": "Menüdatei gespeichert", "saved_config": "Einstellungen (inkl. Fenstergröße 600x400) gespeichert",
        "error": "Fehler", "menu_name": "Menüname:", "app_name": "App-Name:", "command": "Befehl:", "icon": "Icon (optional):", "choose": "Auswählen...",
        "unsaved": "Ungespeicherte Änderungen. Vorher speichern?",
        "valid_xml": "Die XML-Datei ist gültig.", "invalid_xml": "Die XML-Datei ist ungültig:\n{0}",
        "tt_menu": "Ein neues leeres Untermenü an der Cursor-Position einfügen",
        "tt_app": "Einen neuen App-Eintrag direkt an der Cursor-Position einfügen",
        "tt_separator": "Einen Trennstrich an der Cursor-Position einfügen",
        "tt_edit": "Den ausgewählten Eintrag bearbeiten",
        "tt_delete": "Die ausgewählten Einträge löschen",
        "tt_up": "Den einzelnen ausgewählten Eintrag für die Feinjustierung nach oben verschieben (nur für 1 Eintrag)",
        "tt_down": "Den einzelnen ausgewählten Eintrag für die Feinjustierung nach unten verschieben (nur für 1 Eintrag)",
        "tt_starter": "Eine .desktop-Datei als Starter an Cursor-Position importieren",
        "tt_save": "Das aktuelle Menü in der Datei speichern",
        "tt_save_settings": "Aktuelle Konfiguration inklusive der Fenstergröße (600x400) in der settings.ini speichern",
        "side_info_title": "<b>Bedienungshinweise:</b>",
        "side_info": "• <b>Drag & Drop:</b> Ziehe Elemente per Maus an eine andere Stelle.<br>"
                     "• <b>Pfeiltasten (▲/▼):</b> Feinjustierung für jeweils nur einen einzelnen Eintrag.<br>"
                     "• <b>Mehrfachauswahl:</b> Halte Strg oder Shift gedrückt, um mehrere Einträge auszuwählen.<br>"
                     "• <b>Cursor-Position:</b> Neue Einträge werden direkt an der aktuellen Auswahl eingefügt.<br>"
                     "• <b>Doppelklick:</b> Öffnet das Bearbeiten-Fenster für das Element.",
        "help_title": "Anleitung (hilfe.txt)",
        "close": "Schließen",
        "about_text": (
            f"<b>{APP_NAME}</b><br>"
            "Openbox Menu Editor (PyQt6 Edition)<br><br>"
            "<b>Funktionen:</b><br>"
            "• Erstellen & Bearbeiten von Openbox Menüs (menu.xml)<br>"
            "• Einfügen at Cursor-Position & Multi-Drag & Drop Support<br>"
            "• Importieren von .desktop Starter-Dateien<br>"
            "• XML-Validierung und Openbox Reconfigure<br><br>"
            "<b>GitHub:</b> <a href='https://github.com/cvinz78/obmenu-editor'>https://github.com/cvinz78/obmenu-editor</a><br><br>"
            "Lizenz: GNU General Public License v3<br>"
            "Copyright (C) 2026 [cvinz78]"
        )
    },
    "en": {
        "file": "File", "new_menu": "New Menu.xml", "open": "Open...", "save": "Save", "save_as": "Save As...", "exit": "Exit",
        "tools": "Tools", "validate": "Validate XML", "reload": "Reload Openbox",
        "view": "Themes", "creamy": "Creamy", "dark": "Darkmode", "bluemoon": "BlueMoon",
        "settings": "Settings", "save_settings": "Save Settings", "language": "Language", "german": "DE", "english": "EN",
        "help": "Help", "about": "About", "help_doc": "Manual (hilfe.txt)",
        "menu": "Menu", "app": "App", "separator": "Separator", "edit": "Edit", "delete": "Delete",
        "up": "▲", "down": "▼", "starter": "Starter", "tree_title": "Openbox Menu",
        "ready": "Ready", "loaded": "Loaded: {0}", "saved": "Saved",
        "saved_menu": "Menu file saved",
        "saved_config": "Settings (incl. window size 600x400) saved",
        "error": "Error", "menu_name": "Menu name:", "app_name": "App name:", "command": "Command:", "icon": "Icon (optional):", "choose": "Choose...",
        "unsaved": "Unsaved changes. Save first?",
        "valid_xml": "The XML document is valid.", "invalid_xml": "The XML document is invalid:\n{0}",
        "tt_menu": "Insert a new empty sub-menu at cursor position",
        "tt_app": "Insert a new app entry directly at cursor position",
        "tt_separator": "Insert a separator line at cursor position",
        "tt_edit": "Edit the selected item",
        "tt_delete": "Delete selected items",
        "tt_up": "Fine-tune and move the single selected item up (single item only)",
        "tt_down": "Fine-tune and move the single selected item down (single item only)",
        "tt_starter": "Import a .desktop file as launcher at cursor position",
        "tt_save": "Save the current menu to file",
        "tt_save_settings": "Save current configuration including window size (600x400) to settings.ini",
        "side_info_title": "<b>Usage Hints:</b>",
        "side_info": "• <b>Drag & Drop:</b> Drag items using your mouse.<br>"
                     "• <b>Arrow Buttons (▲/▼):</b> Fine-tuning for a single item only.<br>"
                     "• <b>Multi-Select:</b> Hold Ctrl or Shift to select multiple items.<br>"
                     "• <b>Cursor Position:</b> New elements insert at current selection.<br>"
                     "• <b>Double Click:</b> Opens the edit dialog.",
        "help_title": "Manual (hilfe.txt)",
        "close": "Close",
        "about_text": (
            f"<b>{APP_NAME}</b><br>"
            "Openbox Menu Editor (PyQt6 Edition)<br><br>"
            "<b>Features:</b><br>"
            "• Create & Edit Openbox Menus (menu.xml)<br>"
            "• Insert at Cursor Position & Multi-Drag & Drop Support<br>"
            "• Import .desktop Launcher Files<br>"
            "• XML Validation and Openbox Reconfigure<br><br>"
            "<b>GitHub:</b> <a href='https://github.com/cvinz78/obmenu-editor'>https://github.com/cvinz78/obmenu-editor</a><br><br>"
            "License: GNU General Public License v3<br>"
            "Copyright (C) 2026 [cvinz78]"
        )
    }
}

def tag_name(element):
    return element.tag.split("}")[-1]

def qname(name):
    return f"{{{OPENBOX_NS}}}{name}"

def safe_id(text):
    value = str(text).lower().strip()
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value)
    value = value.strip("-")
    return value or "menu"

def find_desktop_icon(icon_name):
    if not icon_name:
        return ""
    if os.path.isabs(icon_name) and os.path.exists(icon_name):
        return icon_name
    
    icon_paths = [
        Path.home() / ".local" / "share" / "icons",
        Path.home() / ".icons",
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps")
    ]
    
    extensions = [".png", ".svg", ".xpm", ".jpg"]
    
    for base_path in icon_paths:
        if not base_path.exists():
            continue
        for root, dirs, files in os.walk(base_path):
            for file in files:
                p = Path(root) / file
                if p.stem == icon_name and p.suffix.lower() in extensions:
                    return str(p)
                    
    for ext in extensions:
        p = Path(f"/usr/share/pixmaps/{icon_name}{ext}")
        if p.exists():
            return str(p)
            
    return icon_name

class CustomTreeWidget(QTreeWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor

    def dropEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is not None:
            node = item.data(0, Qt.ItemDataRole.UserRole)
            if node is not None and tag_name(node) == "separator":
                if self.dropIndicatorPosition() == QTreeWidget.DropIndicatorPosition.OnItem:
                    event.ignore()
                    return
        super().dropEvent(event)
        self.editor.sync_tree_to_xml()

class ConfigManager:
    def __init__(self):
        self.path = OBM_CONFIG_FILE
        self.ensure_files()

    def ensure_files(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not OBM_HELP_FILE.exists():
            try:
                with open(OBM_HELP_FILE, "w", encoding="utf-8") as f:
                    f.write(DEFAULT_HELP_TEXT)
            except OSError:
                pass

    def load_setting(self, section, key, fallback):
        if not self.path.is_file():
            return fallback
        config = configparser.ConfigParser()
        try:
            config.read(self.path, encoding="utf-8")
            return config.get(section, key, fallback=fallback)
        except Exception:
            return fallback

    def save_settings(self, theme, language, width, height, menu_path=""):
        self.ensure_files()
        config = configparser.ConfigParser()
        config["Appearance"] = {
            "theme": theme, 
            "language": language,
            "window_width": str(width),
            "window_height": str(height),
            "menu_path": str(menu_path)
        }
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                config.write(f)
            return True
        except OSError:
            return False

class MenuDocument:
    def __init__(self):
        self.tree = None
        self.root = None
        self.filename = None

    def create_empty(self):
        root = ET.Element(qname("openbox_menu"), {"xmlns": OPENBOX_NS})
        menu = ET.SubElement(root, qname("menu"), {"id": "root-menu", "label": "Openbox"})
        self.tree = ET.ElementTree(root)
        self.root = menu
        self.filename = None

    def load(self, filename):
        self.filename = Path(filename)
        self.tree = ET.parse(filename)
        root = self.tree.getroot()
        
        def find_root_menu(element):
            if tag_name(element) == "menu" and element.get("id") == "root-menu":
                return element
            for child in element:
                res = find_root_menu(child)
                if res is not None:
                    return res
            return None

        menus = find_root_menu(root)
        if menus is None:
            all_menus = [x for x in root.iter() if tag_name(x) == "menu"]
            if all_menus:
                menus = all_menus[0]
            else:
                raise ValueError('Kein <menu> gefunden.')
        self.root = menus

    def save(self, filename=None):
        if filename:
            self.filename = Path(filename)
        if not self.filename:
            return
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.indent(self.tree.getroot())
        self.tree.write(self.filename, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def indent(elem, level=0):
        indent = "\n" + level * "    "
        child_indent = "\n" + (level + 1) * "    "
        children = list(elem)
        if children:
            if not elem.text or not elem.text.strip():
                elem.text = child_indent
            for child in children:
                MenuDocument.indent(child, level + 1)
                if not child.tail or not child.tail.strip():
                    child.tail = child_indent
            if not children[-1].tail or not children[-1].tail.strip():
                children[-1].tail = indent

class ItemDialog(QDialog):
    def __init__(self, parent, title, label="", command="", icon=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(450, 150)
        layout = QFormLayout(self)
        
        self.label_edit = QLineEdit(label)
        self.cmd_edit = QLineEdit(command)
        self.icon_edit = QLineEdit(icon)
        
        btn_browse = QPushButton(parent.t("choose"))
        btn_browse.clicked.connect(self.browse_icon)
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(btn_browse)
        
        layout.addRow(parent.t("app_name"), self.label_edit)
        layout.addRow(parent.t("command"), self.cmd_edit)
        layout.addRow(parent.t("icon"), icon_layout)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addRow(btn_ok)

    def browse_icon(self):
        file, _ = QFileDialog.getOpenFileName(self, "Icon wählen", "", "Bilder (*.png *.svg *.xpm *.jpg);;Alle Dateien (*)")
        if file:
            self.icon_edit.setText(file)

    def get_data(self):
        return self.label_edit.text().strip(), self.cmd_edit.text().strip(), self.icon_edit.text().strip()

class MenuDialog(QDialog):
    def __init__(self, parent, title, label="", icon=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 120)
        layout = QFormLayout(self)
        
        self.label_edit = QLineEdit(label)
        self.icon_edit = QLineEdit(icon)
        
        btn_browse = QPushButton(parent.t("choose"))
        btn_browse.clicked.connect(self.browse_icon)
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(btn_browse)
        
        layout.addRow(parent.t("menu_name"), self.label_edit)
        layout.addRow(parent.t("icon"), icon_layout)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addRow(btn_ok)

    def browse_icon(self):
        file, _ = QFileDialog.getOpenFileName(self, "Icon wählen", "", "Bilder (*.png *.svg *.xpm *.jpg);;Alle Dateien (*)")
        if file:
            self.icon_edit.setText(file)

    def get_data(self):
        return self.label_edit.text().strip(), self.icon_edit.text().strip()

class HelpDialog(QDialog):
    def __init__(self, parent, text, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        btn_close = QPushButton(parent.t("close"))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class MenuEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        
        self.config_manager = ConfigManager()
        self.theme_name = self.config_manager.load_setting("Appearance", "theme", "creamy")
        self.language = self.config_manager.load_setting("Appearance", "language", "de")
        
        configured_path = self.config_manager.load_setting("Appearance", "menu_path", "")
        if configured_path:
            self.custom_menu_path = Path(configured_path)
        else:
            self.custom_menu_path = DEFAULT_MENU_PATH
        
        try:
            w_val = int(self.config_manager.load_setting("Appearance", "window_width", "600"))
            h_val = int(self.config_manager.load_setting("Appearance", "window_height", "400"))
        except ValueError:
            w_val, h_val = 600, 400
            
        self.resize(w_val, h_val)
        
        self.document = MenuDocument()
        self.dirty = False
        
        self.init_ui()
        self.apply_theme()
        
        if self.custom_menu_path.exists():
            try:
                self.document.load(self.custom_menu_path)
            except Exception:
                self.document.create_empty()
        else:
            self.document.create_empty()
            
        self.refresh_tree()

    def t(self, key):
        return TEXTS[self.language].get(key, key)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        tb_layout = QHBoxLayout()
        self.btn_menu = QPushButton()
        self.btn_menu.clicked.connect(self.add_menu)
        
        self.btn_app = QPushButton()
        self.btn_app.clicked.connect(self.add_item)
        
        self.btn_separator = QPushButton()
        self.btn_separator.clicked.connect(self.add_separator)
        
        self.btn_edit = QPushButton()
        self.btn_edit.clicked.connect(self.edit_selected)
        
        self.btn_delete = QPushButton()
        self.btn_delete.clicked.connect(self.delete_item)
        
        self.btn_up = QPushButton()
        self.btn_up.clicked.connect(lambda: self.move_item(-1))
        
        self.btn_down = QPushButton()
        self.btn_down.clicked.connect(lambda: self.move_item(1))
        
        self.btn_starter = QPushButton()
        self.btn_starter.clicked.connect(self.import_desktop)
        
        self.btn_save = QPushButton()
        self.btn_save.clicked.connect(self.save_file)

        for btn in [self.btn_menu, self.btn_app, self.btn_separator, self.btn_edit, 
                    self.btn_delete, self.btn_up, self.btn_down, self.btn_starter, self.btn_save]:
            tb_layout.addWidget(btn)
            
        tb_layout.addStretch()
        main_layout.addLayout(tb_layout)

        content_layout = QHBoxLayout()

        self.tree = CustomTreeWidget(self)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setStretchLastSection(False)

        self.tree.itemDoubleClicked.connect(self.edit_selected)
        
        self.side_info_widget = QWidget()
        side_layout = QVBoxLayout(self.side_info_widget)
        side_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_info_title = QLabel()
        self.lbl_info_text = QLabel()
        self.lbl_info_text.setWordWrap(True)
        self.lbl_info_text.setTextFormat(Qt.TextFormat.RichText)
        
        side_layout.addWidget(self.lbl_info_title)
        side_layout.addWidget(self.lbl_info_text)
        side_layout.addStretch()

        content_layout.addWidget(self.tree, stretch=3)
        content_layout.addWidget(self.side_info_widget, stretch=1)
        
        main_layout.addLayout(content_layout)

        self.update_ui_texts()
        self.statusBar().showMessage(self.t("ready"))

    def update_ui_texts(self):
        self.btn_menu.setText(self.t("menu"))
        self.btn_menu.setToolTip(self.t("tt_menu"))
        
        self.btn_app.setText(self.t("app"))
        self.btn_app.setToolTip(self.t("tt_app"))
        
        self.btn_separator.setText(self.t("separator"))
        self.btn_separator.setToolTip(self.t("tt_separator"))
        
        self.btn_edit.setText(self.t("edit"))
        self.btn_edit.setToolTip(self.t("tt_edit"))
        
        self.btn_delete.setText(self.t("delete"))
        self.btn_delete.setToolTip(self.t("tt_delete"))
        
        self.btn_up.setText(self.t("up"))
        self.btn_up.setToolTip(self.t("tt_up"))
        
        self.btn_down.setText(self.t("down"))
        self.btn_down.setToolTip(self.t("tt_down"))
        
        self.btn_starter.setText(self.t("starter"))
        self.btn_starter.setToolTip(self.t("tt_starter"))
        
        self.btn_save.setText(self.t("save"))
        self.btn_save.setToolTip(self.t("tt_save"))

        self.lbl_info_title.setText(self.t("side_info_title"))
        self.lbl_info_text.setText(self.t("side_info"))

        self.tree.setHeaderLabels([self.t("tree_title"), "Typ", "Befehl"])
        self.create_menu_bar()

    def create_menu_bar(self):
        mb = self.menuBar()
        mb.clear()

        file_menu = mb.addMenu(self.t("file"))
        file_menu.addAction(self.t("new_menu"), self.new_file)
        file_menu.addAction(self.t("open"), self.choose_open)
        file_menu.addAction(self.t("save_as"), self.save_file_as)
        file_menu.addSeparator()
        file_menu.addAction(self.t("exit"), self.close)

        tools_menu = mb.addMenu(self.t("tools"))
        tools_menu.addAction(self.t("validate"), self.validate_xml)
        tools_menu.addAction(self.t("reload"), self.reload_openbox)

        view_menu = mb.addMenu(self.t("view"))
        view_menu.addAction(self.t("creamy"), lambda: self.set_theme("creamy"))
        view_menu.addAction(self.t("dark"), lambda: self.set_theme("dark"))
        view_menu.addAction(self.t("bluemoon"), lambda: self.set_theme("bluemoon"))

        config_menu = mb.addMenu(self.t("settings"))
        save_settings_action = config_menu.addAction(self.t("save_settings"), self.manual_save_settings)
        save_settings_action.setToolTip(self.t("tt_save_settings"))
        
        lang_menu = config_menu.addMenu(self.t("language"))
        lang_menu.addAction(self.t("german"), lambda: self.set_language("de"))
        lang_menu.addAction(self.t("english"), lambda: self.set_language("en"))

        help_menu = mb.addMenu(self.t("help"))
        help_menu.addAction(self.t("help_doc"), self.show_help_doc)
        help_menu.addAction(self.t("about"), self.show_about)

    def manual_save_settings(self):
        size = self.size()
        current_p = str(self.custom_menu_path) if self.custom_menu_path else ""
        if self.config_manager.save_settings(self.theme_name, self.language, size.width(), size.height(), current_p):
            self.statusBar().showMessage(f"✓ {self.t('saved_config')}")

    def apply_theme(self):
        self.setStyleSheet(STYLES.get(self.theme_name, STYLES["creamy"]))

    def set_theme(self, theme):
        self.theme_name = theme
        self.apply_theme()

    def set_language(self, lang):
        self.language = lang
        self.update_ui_texts()
        self.refresh_tree()

    def refresh_tree(self, selected_nodes=None):
        self.tree.blockSignals(True)
        self.tree.clear()
        if self.document.root is None:
            self.tree.blockSignals(False)
            return
        
        root_item = QTreeWidgetItem(self.tree, [self.document.root.get("label", "Openbox"), self.t("menu"), ""])
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.document.root)
        
        icon = self.document.root.get("icon")
        if icon and os.path.exists(icon):
            root_item.setIcon(0, QIcon(icon))
            
        node_map = {}
        node_map[self.document.root] = root_item
        self.populate_node(root_item, self.document.root, node_map)
        self.tree.expandAll()
        
        self.tree.resizeColumnToContents(0)
        
        if selected_nodes is not None:
            self.tree.clearSelection()
            sel_model = self.tree.selectionModel()
            first_item = None
            for node in selected_nodes:
                if node in node_map:
                    item = node_map[node]
                    index = self.tree.indexFromItem(item)
                    sel_model.select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
                    if first_item is None:
                        first_item = item
            if first_item is not None:
                self.tree.setCurrentItem(first_item)

        self.tree.blockSignals(False)
        filename = self.document.filename or self.custom_menu_path
        self.statusBar().showMessage(self.t("loaded").format(str(filename)))

    def populate_node(self, parent_item, xml_node, node_map):
        for child in xml_node:
            tag = tag_name(child)
            if tag == "item":
                cmd = ""
                action = child.find(qname("action"))
                if action is not None:
                    exec_tag = action.find(qname("execute"))
                    if exec_tag is not None and exec_tag.text:
                        cmd = exec_tag.text
                
                item = QTreeWidgetItem(parent_item, [child.get("label", ""), self.t("app"), cmd])
                item.setData(0, Qt.ItemDataRole.UserRole, child)
                node_map[child] = item
                
                icon = child.get("icon")
                if icon and os.path.exists(icon):
                    item.setIcon(0, QIcon(icon))
                    
            elif tag == "menu":
                item = QTreeWidgetItem(parent_item, [child.get("label", ""), self.t("menu"), ""])
                item.setData(0, Qt.ItemDataRole.UserRole, child)
                node_map[child] = item
                
                icon = child.get("icon")
                if icon and os.path.exists(icon):
                    item.setIcon(0, QIcon(icon))
                    
                self.populate_node(item, child, node_map)
            elif tag == "separator":
                item = QTreeWidgetItem(parent_item, ["─── Trenner ───", self.t("separator"), ""])
                item.setData(0, Qt.ItemDataRole.UserRole, child)
                node_map[child] = item

    def sync_tree_to_xml(self):
        def reconstruct(item):
            xml_node = item.data(0, Qt.ItemDataRole.UserRole)
            if xml_node is None:
                return None
            
            tag = tag_name(xml_node)
            if tag == "menu":
                for child_node in list(xml_node):
                    xml_node.remove(child_node)
                for i in range(item.childCount()):
                    child_xml = reconstruct(item.child(i))
                    if child_xml is not None:
                        xml_node.append(child_xml)
            elif tag == "separator":
                for child_node in list(xml_node):
                    xml_node.remove(child_node)
            return xml_node

        root_item = self.tree.topLevelItem(0)
        if root_item is not None:
            reconstruct(root_item)
            self.dirty = True

    def insert_element_at_cursor(self, new_element):
        selected = self.tree.selectedItems()
        if not selected:
            self.document.root.append(new_element)
            return

        item = selected[0]
        node = item.data(0, Qt.ItemDataRole.UserRole)

        if node is None:
            self.document.root.append(new_element)
            return

        if tag_name(node) == "separator":
            parent_item = item.parent()
            if parent_item is None:
                self.document.root.append(new_element)
                return
            parent_node = parent_item.data(0, Qt.ItemDataRole.UserRole)
            if parent_node is None:
                self.document.root.append(new_element)
                return
            children = list(parent_node)
            if node in children:
                idx = children.index(node)
                parent_node.insert(idx + 1, new_element)
            else:
                parent_node.append(new_element)
            return

        if tag_name(node) == "menu":
            node.insert(0, new_element)
        else:
            parent_item = item.parent()
            if parent_item is None:
                self.document.root.append(new_element)
                return
            parent_node = parent_item.data(0, Qt.ItemDataRole.UserRole)
            if parent_node is None:
                self.document.root.append(new_element)
                return
            children = list(parent_node)
            if node in children:
                idx = children.index(node)
                parent_node.insert(idx + 1, new_element)
            else:
                parent_node.append(new_element)

    def add_item(self):
        dialog = ItemDialog(self, self.t("app"), "", "", "")
        if dialog.exec():
            label, cmd, icon = dialog.get_data()
            if not label:
                return
            
            item_xml = ET.Element(qname("item"), {"label": label})
            if icon:
                item_xml.set("icon", icon)
                
            action = ET.SubElement(item_xml, qname("action"), {"name": "Execute"})
            exec_tag = ET.SubElement(action, qname("execute"))
            exec_tag.text = cmd

            self.insert_element_at_cursor(item_xml)
            self.dirty = True
            self.refresh_tree([item_xml])

    def add_menu(self):
        dialog = MenuDialog(self, self.t("menu"), "", "")
        if dialog.exec():
            label, icon = dialog.get_data()
            if not label:
                return

            menu_id = safe_id(label)
            menu_xml = ET.Element(qname("menu"), {"id": menu_id, "label": label})
            if icon:
                menu_xml.set("icon", icon)
            
            item_xml = ET.Element(qname("item"), {"label": "Dummy App"})
            action = ET.SubElement(item_xml, qname("action"), {"name": "Execute"})
            exec_tag = ET.SubElement(action, qname("execute"))
            exec_tag.text = "echo 'Dummy'"
            menu_xml.append(item_xml)

            self.insert_element_at_cursor(menu_xml)
            self.dirty = True
            self.refresh_tree([menu_xml])

    def add_separator(self):
        sep_xml = ET.Element(qname("separator"))
        self.insert_element_at_cursor(sep_xml)
        self.dirty = True
        self.refresh_tree([sep_xml])

    def edit_selected(self):
        selected = self.tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        xml_node = item.data(0, Qt.ItemDataRole.UserRole)
        if xml_node is None:
            return
        tag = tag_name(xml_node)

        if tag == "item":
            cmd = ""
            action = xml_node.find(qname("action"))
            if action is not None:
                exec_tag = action.find(qname("execute"))
                if exec_tag is not None and exec_tag.text:
                    cmd = exec_tag.text
                    
            dialog = ItemDialog(self, self.t("edit"), xml_node.get("label", ""), cmd, xml_node.get("icon", ""))
            if dialog.exec():
                label, cmd, icon = dialog.get_data()
                if not label:
                    return
                xml_node.set("label", label)
                if icon:
                    xml_node.set("icon", icon)
                elif "icon" in xml_node.attrib:
                    del xml_node.attrib["icon"]
                    
                if action is None:
                    action = ET.SubElement(xml_node, qname("action"), {"name": "Execute"})
                exec_tag = action.find(qname("execute"))
                if exec_tag is None:
                    exec_tag = ET.SubElement(action, qname("execute"))
                exec_tag.text = cmd
                
                self.dirty = True
                self.refresh_tree([xml_node])

        elif tag == "menu":
            dialog = MenuDialog(self, self.t("edit"), xml_node.get("label", ""), xml_node.get("icon", ""))
            if dialog.exec():
                label, icon = dialog.get_data()
                if not label:
                    return
                xml_node.set("label", label)
                xml_node.set("id", safe_id(label))
                if icon:
                    xml_node.set("icon", icon)
                elif "icon" in xml_node.attrib:
                    del xml_node.attrib["icon"]
                    
                self.dirty = True
                self.refresh_tree([xml_node])

    def delete_item(self):
        selected = self.tree.selectedItems()
        if not selected:
            return

        for item in selected:
            xml_node = item.data(0, Qt.ItemDataRole.UserRole)
            if xml_node is None or xml_node == self.document.root:
                continue
                
            parent_item = item.parent()
            parent_node = parent_item.data(0, Qt.ItemDataRole.UserRole) if parent_item is not None else self.document.root
            if parent_node is not None and xml_node in list(parent_node):
                parent_node.remove(xml_node)
            
        self.dirty = True
        self.refresh_tree()

    def move_item(self, direction):
        selected_items = self.tree.selectedItems()
        if len(selected_items) != 1:
            return

        item = selected_items[0]
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if node is None or node == self.document.root:
            return

        parent_item = item.parent()
        parent_node = parent_item.data(0, Qt.ItemDataRole.UserRole) if parent_item is not None else self.document.root
        if parent_node is None:
            return
        children = list(parent_node)
        
        if node not in children:
            return

        idx = children.index(node)
        new_idx = idx + direction

        if 0 <= new_idx < len(children):
            parent_node.remove(node)
            parent_node.insert(new_idx, node)
            self.dirty = True
            self.refresh_tree([node])

    def import_desktop(self):
        file, _ = QFileDialog.getOpenFileName(self, "Starter Datei wählen", "/usr/share/applications", "Desktop (*.desktop)")
        if not file:
            return
            
        data = {}
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        data[k] = v
        except OSError:
            return
            
        label = data.get("Name", Path(file).stem)
        cmd = re.sub(r"\s+%[fFuUdDnNickvm]", "", data.get("Exec", "")).strip()
        raw_icon = data.get("Icon", "").strip()
        icon = find_desktop_icon(raw_icon)
        
        if not cmd:
            return
            
        item_xml = ET.Element(qname("item"), {"label": label})
        if icon:
            item_xml.set("icon", icon)
            
        action = ET.SubElement(item_xml, qname("action"), {"name": "Execute"})
        exec_tag = ET.SubElement(action, qname("execute"))
        exec_tag.text = cmd
        
        self.insert_element_at_cursor(item_xml)
        self.dirty = True
        self.refresh_tree([item_xml])

    def new_file(self):
        if self.custom_menu_path.exists():
            backup_path = self.custom_menu_path.with_name("menu.xml.bak")
            try:
                shutil.copy2(self.custom_menu_path, backup_path)
            except Exception as e:
                QMessageBox.warning(self, self.t("error"), f"Backup konnte nicht erstellt werden:\n{e}")

        target_path = None
        if self.custom_menu_path.exists():
            res = QMessageBox.question(
                self, 
                APP_NAME, 
                f"Die Datei {self.custom_menu_path} existiert bereits.\nEin Backup wurde unter menu.xml.bak angelegt.\nSoll sie überschrieben werden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if res == QMessageBox.StandardButton.Yes:
                target_path = self.custom_menu_path
            else:
                return
        else:
            res = QMessageBox.question(
                self,
                APP_NAME,
                f"Es wurde keine Menüdatei unter dem Standardverzeichnis gefunden.\nSoll das Standardverzeichnis ({OPENBOX_CONFIG}) oder ein anderes Verzeichnis verwendet werden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if res == QMessageBox.StandardButton.Yes:
                OPENBOX_CONFIG.mkdir(parents=True, exist_ok=True)
                target_path = DEFAULT_MENU_PATH
            else:
                dir_path = QFileDialog.getExistingDirectory(self, "Verzeichnis auswählen", str(Path.home()))
                if not dir_path:
                    return
                target_path = Path(dir_path) / DEFAULT_MENU

        self.custom_menu_path = target_path
        self.document.create_empty()
        self.document.filename = self.custom_menu_path
        self.dirty = True
        self.save_file()
        self.refresh_tree()

    def choose_open(self):
        start_dir = str(OPENBOX_CONFIG) if OPENBOX_CONFIG.exists() else str(Path.home())
        file, _ = QFileDialog.getOpenFileName(self, "Menu Öffnen", start_dir, "XML (*.xml);;Alle Dateien (*)")
        if file:
            try:
                self.document.load(file)
                self.custom_menu_path = Path(file)
                self.dirty = False
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, self.t("error"), str(e))

    def save_file(self):
        if not self.document.filename:
            self.document.filename = self.custom_menu_path
            
        try:
            self.document.save()
            self.dirty = False
            self.reload_openbox()
            self.statusBar().showMessage(f"✓ {self.t('saved_menu')}")
            return True
        except Exception as e:
            QMessageBox.critical(self, self.t("error"), str(e))
            return False

    def save_file_as(self):
        start_dir = str(OPENBOX_CONFIG) if OPENBOX_CONFIG.exists() else str(Path.home())
        file, _ = QFileDialog.getSaveFileName(self, "Menü speichern unter", start_dir, "XML (*.xml)")
        if file:
            self.custom_menu_path = Path(file)
            self.document.filename = self.custom_menu_path
            return self.save_file()
        return False

    def validate_xml(self):
        if not self.document.filename or not self.document.filename.exists():
            QMessageBox.warning(self, self.t("error"), "Bitte speichern Sie die Datei zuerst.")
            return

        xmllint = shutil.which("xmllint")
        if not xmllint:
            QMessageBox.warning(self, self.t("error"), "xmllint ist nicht installiert.")
            return

        res = subprocess.run([xmllint, "--noout", str(self.document.filename)], capture_output=True, text=True)
        if res.returncode == 0:
            QMessageBox.information(self, "XML Validierung", self.t("valid_xml"))
        else:
            QMessageBox.critical(self, self.t("error"), self.t("invalid_xml").format(res.stderr))

    def reload_openbox(self):
        try:
            subprocess.run(["openbox", "--reconfigure"], check=True)
            self.statusBar().showMessage("Openbox neu geladen.")
        except Exception:
            pass

    def show_help_doc(self):
        if self.language == "en":
            text = DEFAULT_HELP_TEXT_EN
        else:
            text = DEFAULT_HELP_TEXT

        if OBM_HELP_FILE.exists() and self.language == "de":
            try:
                with open(OBM_HELP_FILE, "r", encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                pass
        dialog = HelpDialog(self, text, self.t("help_title"))
        dialog.exec()

    def show_about(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"{self.t('about')} {APP_NAME}")
        msg_box.setText(self.t("about_text"))
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.exec()

    def closeEvent(self, event):
        if self.dirty:
            res = QMessageBox.question(self, APP_NAME, self.t("unsaved"),
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No | 
                                       QMessageBox.StandardButton.Cancel)
            if res == QMessageBox.StandardButton.Yes:
                if self.save_file():
                    event.accept()
                else:
                    event.ignore()
            elif res == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    window = MenuEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()