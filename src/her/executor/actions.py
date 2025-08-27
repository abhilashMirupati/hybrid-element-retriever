# PLACE THIS FILE AT: src/her/executor/actions.py

from playwright.sync_api import sync_playwright

class ActionExecutor:
    def __init__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True)
        self.page = self.browser.new_page()

    def goto(self, url):
        self.page.goto(url)

    def click(self, selector):
        self.page.click(selector)

    def fill(self, selector, text):
        self.page.fill(selector, text)

    def close(self):
        self.browser.close()
        self.pw.stop()
