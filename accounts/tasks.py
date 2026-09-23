from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template

from accounts.models import Account


# @task
def send_password_activate_token_to_user(new_account_id):
    account = Account.objects.get(id=new_account_id)
    account = account
    user_email_address = account.email
    activate_account_code = account.activate_account_code
    # site_url = settings.SITE_URL

    context =  {
        'account': account,
        # 'site_url': site_url,
        'activate_account_code': activate_account_code,
    }
    print("SENDING EMAILS!!!!!!!!!!!!!!!!")
    html_tpl_path = 'emails/accounts/send_password_activate_token_to_user.html'
    email_html_template = get_template(html_tpl_path).render(context)
    email_msg = EmailMessage(
        "Activate Account",
        email_html_template, 
        [settings.DEFAULT_FROM_EMAIL,], # From Email
        [user_email_address,], # To Email
        reply_to=[settings.DEFAULT_FROM_EMAIL,]
    )
        # this is the crucial part that sends email as html content but not as a plain text
    email_msg.content_subtype = 'html'
    email_msg.send(fail_silently=False)
    return email_msg


# @task
def send_password_reset_token_to_user(account_id):
    account = Account.objects.get(id=account_id)
    account = account
    user_email_address = account.email
    user_forgot_password_code = account.forgot_password_code
    site_url = settings.SITE_URL

    context =  {
        'account': account,
        'site_url': site_url,
        'user_forgot_password_code': user_forgot_password_code,
    }

    html_tpl_path = 'emails/accounts/send_password_reset_token_to_user.html'
    email_html_template = get_template(html_tpl_path).render(context)
    email_msg = EmailMessage(
        "Forgot Password Token",
        email_html_template, 
        [settings.DEFAULT_FROM_EMAIL,], # From Email
        [user_email_address,], # To Email
        reply_to=[settings.DEFAULT_FROM_EMAIL,]
    )
        # this is the crucial part that sends email as html content but not as a plain text
    email_msg.content_subtype = 'html'
    email_msg.send(fail_silently=False)
    return email_msg


# @task
def send_password_change_token_to_user(account_id):
    account = Account.objects.get(id=account_id)
    account = account
    user_email_address = account.email
    user_forgot_password_code = account.forgot_password_code
    site_url = settings.SITE_URL

    context =  {
        'account': account,
        'site_url': site_url,
        'user_forgot_password_code': user_forgot_password_code,
    }

    html_tpl_path = 'emails/accounts/send_password_change_token_to_user.html'
    email_html_template = get_template(html_tpl_path).render(context)
    email_msg = EmailMessage(
        "Change Password Token",
        email_html_template, 
        [settings.DEFAULT_FROM_EMAIL,], # From Email
        [user_email_address,], # To Email
        reply_to=[settings.DEFAULT_FROM_EMAIL,]
    )
        # this is the crucial part that sends email as html content but not as a plain text
    email_msg.content_subtype = 'html'
    email_msg.send(fail_silently=False)
    return email_msg