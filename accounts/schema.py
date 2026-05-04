import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
from .models import PasswordResetOTP
import threading
import base64
import uuid
import os
from django.core.files.base import ContentFile
import re

User = get_user_model()

def send_email_async(subject, message, from_email, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        print("Email sending failed:", e)


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'name', 'team_name', 'email', 'profile_picture')

    is_admin = graphene.Boolean()
    profile_picture_url = graphene.String()

    def resolve_is_admin(self, info):
        return self.is_staff

    def resolve_profile_picture_url(self, info):
        if self.profile_picture:
            request = info.context
            base = getattr(settings, 'MEDIA_URL', '/media/')
            # Build absolute URL using the request host
            try:
                return request.build_absolute_uri(self.profile_picture.url)
            except Exception:
                return f"{base}{self.profile_picture}"
        return None


class SignupMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        password = graphene.String(required=True)
        team_name = graphene.String(required=True)
        email = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, name, password, team_name, email):
        if User.objects.filter(name=name).exists():
            return SignupMutation(success=False, message='Username already taken.', user=None)


        def validate_email(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                raise Exception("Enter a valid email address!")

        user = User.objects.create_user(
            name=name,
            email=email,
            password=password,
            team_name=team_name
        )

        return SignupMutation(success=True, message='Account created successfully.', user=user)

class LoginMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, name, password):
        try:
            user = User.objects.get(name=name)
        except User.DoesNotExist:
            return LoginMutation(success=False, message='User not found.', token=None, user=None)

        if not user.check_password(password):
            return LoginMutation(success=False, message='Invalid password.', token=None, user=None)

        import graphql_jwt.shortcuts as jwt_shortcuts
        token = jwt_shortcuts.get_token(user)
        return LoginMutation(success=True, message='Login successful.', token=token, user=user)


class UpdateProfilePicture(graphene.Mutation):
    """Accept a base64-encoded image and save it as the user's profile picture."""
    class Arguments:
        image_base64 = graphene.String(required=True)
        file_name = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, image_base64, file_name=None):
        user = info.context.user
        if user.is_anonymous:
            return UpdateProfilePicture(success=False, message='Not authenticated.', user=None)

        try:
            # Strip data URI prefix if present (data:image/jpeg;base64,...)
            if ',' in image_base64:
                image_base64 = image_base64.split(',', 1)[1]

            image_data = base64.b64decode(image_base64)
            ext = 'jpg'
            if file_name:
                _, ext = os.path.splitext(file_name)
                ext = ext.lstrip('.') or 'jpg'

            unique_name = f"{uuid.uuid4().hex}.{ext}"
            user.profile_picture.save(unique_name, ContentFile(image_data), save=True)
            return UpdateProfilePicture(success=True, message='Profile picture updated.', user=user)
        except Exception as e:
            return UpdateProfilePicture(success=False, message=str(e), user=None)


class SendPasswordOTP(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        print("Entered email:", email)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return SendPasswordOTP(
                success=True,
                message="If the email exists, OTP has been sent"
            )

        # delete old OTPs
        PasswordResetOTP.objects.filter(user=user).delete()

        otp = str(random.randint(100000, 999999))

        print("OTP:", otp)  # ✅ DEBUG

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp
        )

        threading.Thread(
            target=send_email_async,
            args=(
                "Password Reset OTP",
                f"Your OTP is {otp}. Valid for 5 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            ),
            daemon=True,
        ).start()

        return SendPasswordOTP(
            success=True,
            message="OTP sent to your email"
        )

class ResetPasswordWithOTP(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        otp = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, otp, password):
        try:
            user = User.objects.get(email=email)
            reset_otp = PasswordResetOTP.objects.get(user=user, otp=otp)
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return ResetPasswordWithOTP(
                success=False,
                message="Invalid OTP"
            )

        if reset_otp.expired():
            reset_otp.delete()
            return ResetPasswordWithOTP(
                success=False,
                message="OTP expired"
            )

        user.set_password(password)
        user.save()

        reset_otp.delete()

        return ResetPasswordWithOTP(
            success=True,
            message="Password reset successful"
        )


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not authenticated')
        return user


class Mutation(graphene.ObjectType):
    signup = SignupMutation.Field()
    login = LoginMutation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    send_password_otp = SendPasswordOTP.Field()
    reset_password_with_otp = ResetPasswordWithOTP.Field()
    update_profile_picture = UpdateProfilePicture.Field()