import os

from splinter import Browser

def get_browser(width, heigth):
    browser = Browser('phantomjs')
    browser.driver.set_window_size(width, heigth)
    return browser

def create_screenshot(browser, path):
    base_url = 'http://localhost:8888/'
    browser.visit(os.path.join(base_url, path))
    filename = os.path.join('screenshot', 'screenshot{}.png'.format(path.replace('/', '-')))
    browser.driver.save_screenshot(filename)

if __name__ == '__main__':
    browser_window_size = {'OSX': (1280, 800)}
    browser = get_browser(*browser_window_size['OSX'])
    create_screenshot(browser, '')

    # TODO: screenshots of logged-in pages
