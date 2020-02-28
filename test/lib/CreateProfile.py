class CreateProfile(object):
    def __init__(self, path="."):
        self.path = path

    def create_firefox_profile(self, save_path="."):
        from selenium import webdriver

        fp = webdriver.FirefoxProfile(".")
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", save_path)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        fp.update_preferences()
        return fp.path
