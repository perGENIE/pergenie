from splinter import Browser

from django.conf import settings

from apps.authentication.models import User


def create_user(test_user_id, test_user_password, is_active=False):
    test_user_id = 'test-user@pergenie.org'
    test_user_password = 'test-user-password'
    user = User.objects.create_user(test_user_id,
                                    test_user_password)
    user.is_active = is_active
    user.save()
    return user

def browser_login(browser, test_user_id, test_user_password):
    browser.visit(settings.LOGIN_URL)
    browser.fill('email', test_user_id)
    browser.fill('password', test_user_password)
    browser.find_by_name('submit').click()
    return browser
