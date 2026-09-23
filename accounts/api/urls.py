from django.urls import path
from .views import (UserAccountDetailView, 
                    MobileAppForgotPasswordView, 
                    MobileAppEnterNewPasswordView, 
                    ResendRegistrationOTPCodeAPIView,
                    UserAccountUpdateDetailView, 
                    ProfileAccountUpdateDetailView,
                    CustomRegistrationAPIView,
                    CustomAccountActivationAPIView,
                    MobileAppChangePasswordView,
                    ProfilePasswordUpdateAPIView,
                    ProfileImageUpdateAPIView,
                    PreferencesUpdateAPIView,
                    PrivacyUpdateAPIView,
                    UserAccountDeleteAPIView,
                    AccountDetailAPIView,
                )

app_name = 'accounts_api'

urlpatterns = [
    path('register/', CustomRegistrationAPIView.as_view(), name='register'),
    path('activate-account/', CustomAccountActivationAPIView.as_view(), name='custom-activate-account'),
    path('resend-registration-otp-code/', ResendRegistrationOTPCodeAPIView.as_view(), name='resend-registration-otp-code'),
    path('account/<int:pk>/', UserAccountDetailView.as_view(), name='account-view'),
    path("account/detail/<int:pk>/", AccountDetailAPIView.as_view()),    
    path('account/update/<int:pk>/', UserAccountUpdateDetailView.as_view(), name='account-update-view'),
    path("account/delete/<int:pk>/", UserAccountDeleteAPIView.as_view(), name="account-delete"),
    path('forgot-password/', MobileAppForgotPasswordView.as_view(), name="forgot-password"),
    path('forgot-password/enter-new/', MobileAppEnterNewPasswordView.as_view(), name="forgot-password-enter-new"),
    path('change-password/', MobileAppChangePasswordView.as_view(), name="change-password"),

    # START HERE
    path('profile/<int:pk>/', ProfileAccountUpdateDetailView.as_view(), name='profile-update-view'),
    path("profile/change-password/",ProfilePasswordUpdateAPIView.as_view(), name="profile-change-password"),
    path("profile/image/update/", ProfileImageUpdateAPIView.as_view(), name="profile-image-update"),

    path("profile/privacy/update/<int:pk>/", PrivacyUpdateAPIView.as_view(), name="profile-preferences-update"),
    path("profile/preferences/update/<int:pk>/", PreferencesUpdateAPIView.as_view(), name="profile-preferences-update"),
    
]
