from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User, EmailVerificationToken, PasswordResetToken


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra_info", {"fields": ("phone",)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Extra_info", {"fields": ("phone",)}),
    )

    list_display = ("id", "username", "email", "phone", "email_verified", "is_active",)

admin.site.register(User, UserAdmin)


class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'created_at',)

admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)


class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'created_at',)

admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)