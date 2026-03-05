import sys
import urllib.parse
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Adw, Gio, Gdk, GLib

GLib.set_prgname('Appme')
GLib.set_application_name('Appme')

from src.desktop_entry import DesktopEntry

def show_about_dialog(parent):
    about = Adw.AboutDialog(
        application_name="Appme",
        application_icon="io.github.rohankp1.Appme",
        version="1.0.0",
        developer_name="RohanKP1",
        license_type=Gtk.License.GPL_3_0,
        website="https://github.com/RohanKP1/Appme",
        comments="A simple tool to create web applications on Linux, inspired by Linux Mint's Webapp Manager."
    )
    
    about.add_credit_section("Developer", ["RohanKP1\nhttps://github.com/RohanKP1"])
    about.add_credit_section("Inspired by", ["Linux Mint Webapp Manager\nhttps://github.com/linuxmint/webapp-manager"])
    
    about.present(parent)

class IconPickerWindow(Adw.Window):
    def __init__(self, parent, on_icon_selected_cb):
        super().__init__(transient_for=parent, modal=True, title="Choose an Icon")
        self.set_default_size(450, 500)
        self.on_icon_selected_cb = on_icon_selected_cb
        
        self.icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        self.all_system_icons = self.icon_theme.get_icon_names()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(box)

        header = Adw.HeaderBar()
        box.append(header)

        search_box = Gtk.Box(margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        self.search_entry = Gtk.SearchEntry(hexpand=True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.append(self.search_entry)
        box.append(search_box)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        box.append(scrolled)

        self.flowbox = Gtk.FlowBox(valign=Gtk.Align.START, margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.flowbox)

        self.common_icons = [
            "facebook", "github", "gmail", "slack", "todoist", "youtube", "twitter", 
            "whatsapp", "telegram", "discord", "spotify", "netflix", "amazon",
            "applications-internet-symbolic", "web-browser", "applications-games"
        ]
        self.populate_icons(self.common_icons)

    def populate_icons(self, icon_list):
        self.flowbox.remove_all()
        for icon_name in icon_list:
            if self.icon_theme.has_icon(icon_name):
                btn = Gtk.Button()
                img = Gtk.Image.new_from_icon_name(icon_name)
                img.set_pixel_size(48)
                btn.set_child(img)
                btn.add_css_class("flat")
                
                btn.connect("clicked", self.on_icon_button_clicked, icon_name)
                self.flowbox.insert(btn, -1)

    def on_search_changed(self, entry):
        query = entry.get_text().lower().strip()
        if not query:
            self.populate_icons(self.common_icons)
            return
            
        matches = [icon for icon in self.all_system_icons if query in icon.lower()][:150]
        self.populate_icons(matches)

    def on_icon_button_clicked(self, button, icon_name):
        self.on_icon_selected_cb(icon_name)
        self.close()


class AddWebAppWindow(Adw.Window):
    def __init__(self, parent=None, edit_data=None):
        title = "Edit Web App" if edit_data else "Add a New Web App"
        super().__init__(transient_for=parent, modal=True, title=title)
        self.set_default_size(450, 550)
        self.parent_window = parent
        self.edit_data = edit_data
        self.user_edited_name = False 
        
        self.icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        self.selected_icon = "applications-internet-symbolic"

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(box)

        header = Adw.HeaderBar()
        box.append(header)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda x: self.close())
        header.pack_start(cancel_btn)

        self.save_btn = Gtk.Button(label="Save" if self.edit_data else "Add")
        self.save_btn.add_css_class("suggested-action") 
        self.save_btn.connect("clicked", self.on_ok_clicked)
        if not self.edit_data:
            self.save_btn.set_sensitive(False)
        header.pack_end(self.save_btn)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        box.append(scrolled)

        page = Adw.PreferencesPage()
        scrolled.set_child(page)

        group = Adw.PreferencesGroup()
        page.add(group)

        self.address_row = Adw.EntryRow(title="Address")
        self.address_row.connect("changed", self.on_input_changed)
        group.add(self.address_row)

        self.name_row = Adw.EntryRow(title="Name")
        self.name_row.connect("changed", self.on_name_changed)
        group.add(self.name_row)

        self.icon_row = Adw.ActionRow(title="Icon")
        self.icon_preview = Gtk.Image.new_from_icon_name(self.selected_icon)
        self.icon_preview.set_pixel_size(32)
        
        icon_btn = Gtk.Button(valign=Gtk.Align.CENTER)
        icon_btn.set_child(self.icon_preview)
        icon_btn.connect("clicked", self.open_icon_picker)
        self.icon_row.add_suffix(icon_btn)
        group.add(self.icon_row)

        self.categories = [
            "Network", "AudioVideo", "Audio", "Video", "Development", 
            "Education", "Game", "Graphics", "Office", "Science", 
            "Settings", "System", "Utility"
        ]
        cat_model = Gtk.StringList.new(self.categories)
        self.category_row = Adw.ComboRow(title="Category", model=cat_model)
        group.add(self.category_row)

        self.browser_data = [] 
        browser_strings = []
        browsers_dict = DesktopEntry.get_browsers_robust()
        
        for medium, app_list in browsers_dict.items():
            for app in app_list:
                self.browser_data.append((medium, app["id"], app["name"]))
                browser_strings.append(f"{app['name']} ({medium})")
                
        if not browser_strings:
            browser_strings = ["Default System Browser"]
            self.browser_data.append(("System", "xdg-open", "System Browser"))

        browser_model = Gtk.StringList.new(browser_strings)
        self.browser_row = Adw.ComboRow(title="Browser", model=browser_model)
        group.add(self.browser_row)

        self.isolate_row = Adw.SwitchRow(
            title="Isolate Profile",
            subtitle="Run in a separate, clean browser profile"
        )
        group.add(self.isolate_row)

        if self.edit_data:
            self.user_edited_name = True
            self.name_row.set_text(self.edit_data.get('name', ''))
            self.address_row.set_text(self.edit_data.get('url', ''))
            self.update_icon(self.edit_data.get('icon', 'applications-internet-symbolic'))
            self.isolate_row.set_active(self.edit_data.get('isolated', False)) 
            
            try:
                cat_idx = self.categories.index(self.edit_data.get('category'))
                self.category_row.set_selected(cat_idx)
            except ValueError:
                pass
                
            for i, b_tuple in enumerate(self.browser_data):
                if b_tuple[1] == self.edit_data.get('browser_id'):
                    self.browser_row.set_selected(i)
                    break

            delete_group = Adw.PreferencesGroup()
            page.add(delete_group)
            
            delete_btn = Gtk.Button(label="Delete Web App", margin_top=24)
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", self.on_delete_clicked)
            
            clamp = Adw.Clamp(maximum_size=300)
            clamp.set_child(delete_btn)
            delete_group.add(clamp)

    def validate_inputs(self):
        name = self.name_row.get_text().strip()
        url = self.address_row.get_text().strip()
        self.save_btn.set_sensitive(bool(name and url))

    def on_input_changed(self, entry):
        self.validate_inputs()
        
        if self.edit_data or self.user_edited_name: 
            return 
        
        url = entry.get_text().strip()
        if not url: return
        
        clean_url = url if "://" in url else f"http://{url}"
        parsed = urllib.parse.urlparse(clean_url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        if domain.startswith("www."):
            domain = domain[4:]
            
        domain_name = domain.split('.')[0]
        if domain_name:
            self.name_row.handler_block_by_func(self.on_name_changed)
            self.name_row.set_text(domain_name.capitalize())
            self.name_row.handler_unblock_by_func(self.on_name_changed)
            
            if self.icon_theme.has_icon(domain_name.lower()):
                self.update_icon(domain_name.lower())
        self.validate_inputs()

    def on_name_changed(self, entry):
        if not self.edit_data:
            self.user_edited_name = True
            
        name = entry.get_text().lower().strip().replace(' ', '-')
        if name and self.icon_theme.has_icon(name):
            self.update_icon(name)
        self.validate_inputs()

    def open_icon_picker(self, button):
        picker = IconPickerWindow(parent=self, on_icon_selected_cb=self.update_icon)
        picker.present()

    def update_icon(self, icon_name):
        self.selected_icon = icon_name
        self.icon_preview.set_from_icon_name(icon_name)

    def on_delete_clicked(self, button):
        if self.edit_data:
            DesktopEntry.delete_webapp(self.edit_data['filepath'], name=self.edit_data['name'])
            
            if self.parent_window and hasattr(self.parent_window, 'load_user_webapps'):
                self.parent_window.load_user_webapps()
                
        self.close()

    def on_ok_clicked(self, button):
        name = self.name_row.get_text()
        url = self.address_row.get_text().strip()
        
        if not name or not url:
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        category = self.categories[self.category_row.get_selected()]
        selected_idx = self.browser_row.get_selected()
        browser_medium, browser_id, browser_name = self.browser_data[selected_idx]
        isolated = self.isolate_row.get_active()

        if self.edit_data:
            name_changed = self.edit_data['name'] != name
            browser_changed = self.edit_data['browser_id'] != browser_id
            
            if name_changed or browser_changed:
                DesktopEntry.delete_webapp(self.edit_data['filepath'], name=self.edit_data['name'])

        exec_cmd = DesktopEntry.generate_exec_command(browser_medium, browser_id, url, name, isolated)
        
        app = DesktopEntry(
            name=name,
            comment=f"Web application for {name}",
            exec_command=exec_cmd,
            icon=self.selected_icon, 
            terminal=False,
            categories=["WebApp", category],
            url=url,
            browser_medium=browser_medium,
            browser_id=browser_id,
            browser_name=browser_name,
            isolated=isolated
        )
        
        app.export_dotdesktop_file()
        
        if self.parent_window and hasattr(self.parent_window, 'load_user_webapps'):
            self.parent_window.load_user_webapps()
            
        self.close()


class AppmeWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Appme")
        self.set_default_size(550, 600)
        self.set_icon_name("io.github.rohankp1.Appme") 

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(vbox)

        self.header = Adw.HeaderBar()
        vbox.append(self.header)

        title_widget = Adw.WindowTitle(title="Appme", subtitle="Run websites as if they were apps")
        self.header.set_title_widget(title_widget)

        add_btn = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Add a new Web App")
        add_btn.connect("clicked", self.on_add_clicked)
        self.header.pack_start(add_btn)
        
        self.add_primary_menu()

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        vbox.append(self.stack)

        self.status_page = Adw.StatusPage(
            icon_name="package-x-generic-symbolic",
            title="No Web Apps",
            description="Create your first web app to get started."
        )
        self.stack.add_named(self.status_page, "empty")

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        
        clamp = Adw.Clamp(maximum_size=800)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.connect("row-activated", self.on_row_activated)
        
        clamp.set_child(self.listbox)
        scrolled_window.set_child(clamp)
        self.stack.add_named(scrolled_window, "list")

        self.load_user_webapps()

    def add_primary_menu(self):
        menu = Gio.Menu.new()
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", lambda a, p: show_about_dialog(self))
        self.add_action(about_action) 
        menu.append("About Appme", "win.about")
        
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")
        self.menu_button.set_tooltip_text("Menu")
        self.menu_button.set_menu_model(menu)
        
        self.header.pack_end(self.menu_button)

    def load_user_webapps(self):
        while child := self.listbox.get_first_child():
            self.listbox.remove(child)

        webapps = DesktopEntry.get_user_webapps()

        if not webapps:
            self.stack.set_visible_child_name("empty")
            return

        self.stack.set_visible_child_name("list")

        for app_data in webapps:
            row = Adw.ActionRow(title=app_data['name'])
            safe_url = GLib.markup_escape_text(app_data.get('url', ''))
            row.set_subtitle(safe_url)
            row.webapp_data = app_data 
            row.set_activatable(True) 
            
            icon = Gtk.Image.new_from_icon_name(app_data['icon'])
            icon.set_icon_size(Gtk.IconSize.LARGE)
            row.add_prefix(icon)
            
            arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
            row.add_suffix(arrow)
            
            self.listbox.append(row)

    def on_add_clicked(self, button):
        add_dialog = AddWebAppWindow(parent=self)
        add_dialog.present()

    def on_row_activated(self, listbox, row):
        if hasattr(row, 'webapp_data'):
            edit_dialog = AddWebAppWindow(parent=self, edit_data=row.webapp_data)
            edit_dialog.present()


class AppmeApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id='io.github.rohankp1.Appme',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = AppmeWindow(application=self)
        win.present()

if __name__ == '__main__':
    app = AppmeApplication()
    sys.exit(app.run(sys.argv))