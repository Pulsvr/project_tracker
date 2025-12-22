from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    pass

email_confirmation_token = EmailConfirmationTokenGenerator()