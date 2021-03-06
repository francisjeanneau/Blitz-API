import pytz

from datetime import datetime

from django.contrib.auth import get_user_model, password_validation
from django.conf import settings
from django.utils import timezone
from django.http import Http404, HttpResponse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from rest_framework import status, viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import (
    TemporaryToken, ActionToken, Domain, Organization, AcademicLevel,
    AcademicField,
)
from .resources import (AcademicFieldResource, AcademicLevelResource,
                        OrganizationResource, UserResource)
from .services import ExportPagination
from . import serializers, permissions, services

User = get_user_model()

LOCAL_TIMEZONE = pytz.timezone(settings.TIME_ZONE)


class UserViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given user.

    list:
    Return a list of all the existing users.

    create:
    Create a new user instance.

    update:
    Update fields of a user instance.

    delete:
    Sets the user inactive.
    """
    queryset = User.objects.all()
    filter_fields = {
        'email': '__all__',
        'phone': '__all__',
        'other_phone': '__all__',
        'academic_field': '__all__',
        'university': '__all__',
        'academic_level': '__all__',
        'membership': '__all__',
        'last_login': '__all__',
        'first_name': '__all__',
        'last_name': '__all__',
        'is_active': '__all__',
        'date_joined': '__all__',
        'birthdate': '__all__',
        'gender': '__all__',
        'membership_end': '__all__',
        'tickets': '__all__',
        'groups': '__all__',
        'user_permissions': '__all__'
    }
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)

    @action(detail=False, permission_classes=[IsAdminUser])
    def export(self, request):
        # Use custom paginator (by page, min/max 1000 objects/page)
        self.pagination_class = ExportPagination
        # Order queryset by ascending id, thus by descending age too
        queryset = self.get_queryset().order_by('pk')
        # Paginate queryset using custom paginator
        page = self.paginate_queryset(queryset)
        # Build dataset using paginated queryset
        dataset = UserResource().export(page)
        # Build response object
        response = self.get_paginated_response(dataset.xls)
        # Add filename to response
        response['Content-Disposition'] = ''.join([
            'attachment; filename="User-',
            LOCAL_TIMEZONE.localize(datetime.now()).strftime("%Y%m%d-%H%M%S"),
            '".xls'
        ])
        return response

    def get_serializer_class(self):
        if (self.action == 'update') | (self.action == 'partial_update'):
            return serializers.UserUpdateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        if self.kwargs.get("pk", "") == "me":
            self.kwargs['pk'] = user.id
        return queryset

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = []
        elif self.action == 'list':
            permission_classes = [IsAdminUser, ]
        else:
            permission_classes = [
                IsAuthenticated,
                permissions.IsOwner
            ]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        """ Hides non-existent objects by denying permission """
        if request.user.is_staff:
            return super().retrieve(request, *args, **kwargs)
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            raise PermissionDenied

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.is_active = False
            instance.save()
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        """ Hides non-existent objects by denying permission """
        if request.user.is_staff:
            return super().update(request, *args, **kwargs)
        try:
            return super().update(request, *args, **kwargs)
        except Http404:
            raise PermissionDenied

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(email=request.data["email"])
        if response.status_code == status.HTTP_201_CREATED:
            if settings.LOCAL_SETTINGS['AUTO_ACTIVATE_USER'] is True:
                user.is_active = True
                user.save()

            if settings.LOCAL_SETTINGS['EMAIL_SERVICE'] is True:
                MAIL_SERVICE = settings.ANYMAIL
                FRONTEND_SETTINGS = settings.LOCAL_SETTINGS[
                    'FRONTEND_INTEGRATION'
                ]

                # Get the token of the saved user and send it with an email
                activate_token = ActionToken.objects.get(
                    user=user,
                    type='account_activation',
                ).key

                # Setup the url for the activation button in the email
                activation_url = FRONTEND_SETTINGS['ACTIVATION_URL'].replace(
                    "{{token}}",
                    activate_token
                )

                response_send_mail = services.send_mail(
                    [user],
                    {
                        "activation_url": activation_url,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "CONFIRM_SIGN_UP",
                )

                if response_send_mail:
                    content = {
                        'detail': _("The account was created but no email was "
                                    "sent. If your account is not "
                                    "activated, contact the administration."),
                    }
                    return Response(content, status=status.HTTP_201_CREATED)

        return response


class UsersActivation(APIView):
    """
    Activate email from an activation token or email change token
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        """
        Activate email if the provided Token is valid.
        """
        activation_token = request.data.get('activation_token')

        new_account_token = ActionToken.objects.filter(
            key=activation_token,
            type='account_activation',
        )
        change_email_token = ActionToken.objects.filter(
            key=activation_token,
            type='email_change',
        )

        # There is no reference to this token or multiple identical token
        # exists.
        if ((not new_account_token and not change_email_token)
                or (new_account_token.count() > 1
                    and change_email_token.count() > 1)):
            error = '"{0}" is not a valid activation_token.'. \
                format(activation_token)

            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )

        # There is only one reference, we will set the user active
        if len(new_account_token) == 1:
            # We activate the user
            user = new_account_token[0].user
            user.is_active = True
            user.save()

            # We delete the token used
            new_account_token[0].delete()

            # Authenticate the user automatically
            token, _created = TemporaryToken.objects.get_or_create(
                user=user
            )
            CONFIG = settings.REST_FRAMEWORK_TEMPORARY_TOKENS
            token.expires = timezone.now() + timezone.timedelta(
                minutes=CONFIG['MINUTES']
            )
            token.save()

            # We return the user
            serializer = serializers.UserSerializer(
                user,
                context={'request': request},
            )

            return_data = dict()
            return_data['user'] = serializer.data
            return_data['token'] = token.key

            return Response(return_data)

        # There is only one reference, we will change user's informations
        # The ActionToken's data field can include 'email' and 'university_id'
        # fields.
        # NOTE: This assumes that data validation was done before creating the
        # activation token and submitting it here.
        if len(change_email_token) == 1:
            # We activate the user
            user = change_email_token[0].user
            new_email = change_email_token[0].data.get('email', None)
            new_university_id = change_email_token[0].data.get(
                'university_id', None
            )
            # If no email is provided in the ActionToken's data field, this is
            # considered to be a bug.
            if not new_email:
                error = '"{0}" is not a valid activation_token.'. \
                    format(activation_token)

                return Response(
                    {'detail': error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Update user info
            user.email = new_email
            if new_university_id:
                user.university = Organization.objects.get(
                    pk=new_university_id
                )
            else:
                user.university = None
            user.save()

            # We delete the token used
            change_email_token[0].delete()

            # Authenticate the user automatically
            token, _created = TemporaryToken.objects.get_or_create(
                user=user
            )
            CONFIG = settings.REST_FRAMEWORK_TEMPORARY_TOKENS
            token.expires = timezone.now() + timezone.timedelta(
                minutes=CONFIG['MINUTES']
            )
            token.save()

            # We return the user
            serializer = serializers.UserSerializer(
                user,
                context={'request': request},
            )

            return_data = dict()
            return_data['user'] = serializer.data
            return_data['token'] = token.key

            return Response(return_data)


class ResetPassword(APIView):
    """
    post:
    Create a new token allowing user to change his password.
    """
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        if settings.LOCAL_SETTINGS['EMAIL_SERVICE'] is not True:
            # Without email this functionality is not provided
            return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

        # Valid params
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # remove old tokens to change password
        tokens = ActionToken.objects.filter(
            type='password_change',
            user=user,
        )

        for token in tokens:
            token.expire()

        # create the new token
        token = ActionToken.objects.create(
            type='password_change',
            user=user,
        )

        # Send the new token by e-mail to the user
        MAIL_SERVICE = settings.ANYMAIL
        FRONTEND_SETTINGS = settings.LOCAL_SETTINGS['FRONTEND_INTEGRATION']

        button_url = FRONTEND_SETTINGS['FORGOT_PASSWORD_URL'].replace(
            "{{token}}",
            str(token)
        )

        response_send_mail = services.send_mail(
            [user],
            {"forgot_password_url": button_url},
            "FORGOT_PASSWORD",
        )

        if response_send_mail:
            content = {
                'detail': _("Your token has been created but no email "
                            "has been sent. Please contact the "
                            "administration."),
            }
            return Response(content, status=status.HTTP_201_CREATED)

        else:
            return Response(status=status.HTTP_201_CREATED)


class ChangePassword(APIView):
    """
    post:
    Get a token and a new password and change the password of
    the token's owner.
    """
    authentication_classes = ()
    permission_classes = ()
    serializer_class = serializers.UserSerializer

    def post(self, request):
        # Valid params
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = request.data.get('token')
        new_password = request.data.get('new_password')

        tokens = ActionToken.objects.filter(
            key=token,
            type='password_change',
            expired=False,
        )

        # There is only one reference, we will change the user password
        if len(tokens) == 1:
            user = tokens[0].user
            try:
                password_validation.validate_password(password=new_password)
            except ValidationError as err:
                content = {
                    'detail': err,
                }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            # We expire the token used
            tokens[0].expire()

            # We return the user
            serializer = serializers.UserSerializer(
                user,
                context={'request': request}
            )

            return Response(serializer.data)

        # There is no reference to this token or multiple identical token
        # token exists
        else:
            error = '{0} is not a valid token.'.format(token)

            return Response(
                {'detail': error},
                status=status.HTTP_400_BAD_REQUEST
            )


class DomainViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given domain.

    list:
    Return a list of all the existing domains.

    create:
    Create a new domain instance.
    """
    serializer_class = serializers.DomainSerializer
    queryset = Domain.objects.all()
    permission_classes = (permissions.IsAdminOrReadOnly,)
    ordering = ('name',)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given organization.

    list:
    Return a list of all the existing organizations.

    create:
    Create a new organization instance.
    """
    serializer_class = serializers.OrganizationSerializer
    queryset = Organization.objects.all()
    permission_classes = (permissions.IsAdminOrReadOnly,)
    ordering = ('name',)

    @action(detail=False, permission_classes=[IsAdminUser])
    def export(self, request):
        # Use custom paginator (by page, min/max 1000 objects/page)
        self.pagination_class = ExportPagination
        # Order queryset by ascending id, thus by descending age too
        queryset = self.get_queryset().order_by('pk')
        # Paginate queryset using custom paginator
        page = self.paginate_queryset(queryset)
        # Build dataset using paginated queryset
        dataset = OrganizationResource().export(page)
        # Build response object
        response = self.get_paginated_response(dataset.xls)
        # Add filename to response
        response['Content-Disposition'] = ''.join([
            'attachment; filename="Organization-',
            LOCAL_TIMEZONE.localize(datetime.now()).strftime("%Y%m%d-%H%M%S"),
            '".xls'
        ])
        return response


class ObtainTemporaryAuthToken(ObtainAuthToken):
    """
    Enables email/password exchange for expiring token.
    """
    model = TemporaryToken

    def post(self, request):
        """
        Respond to POSTed email/password with token.
        """
        CONFIG = settings.REST_FRAMEWORK_TEMPORARY_TOKENS
        serializer = serializers.CustomAuthTokenSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = None

        token, _created = TemporaryToken.objects.get_or_create(
            user=user
        )

        if token.expired:
            # If the token is expired, generate a new one.
            token.delete()
            expires = timezone.now() + timezone.timedelta(
                minutes=CONFIG['MINUTES']
            )

            token = TemporaryToken.objects.create(
                user=user, expires=expires)

        data = {'token': token.key}
        return Response(data)


class TemporaryTokenDestroy(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    """
    destroy:
    Delete a TemporaryToken object. Used to logout.
    """
    queryset = TemporaryToken.objects.none()

    def get_queryset(self):
        key = self.kwargs.get('pk')
        tokens = TemporaryToken.objects.filter(
            key=key,
            user=self.request.user,
        )
        return tokens


class AcademicLevelViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given academic level.

    list:
    Return a list of all the existing academic levels.

    create:
    Create a new academic level instance.
    """
    serializer_class = serializers.AcademicLevelSerializer
    queryset = AcademicLevel.objects.all()
    permission_classes = (permissions.IsAdminOrReadOnly,)
    ordering = ('name',)

    @action(detail=False, permission_classes=[IsAdminUser])
    def export(self, request):
        # Use custom paginator (by page, min/max 1000 objects/page)
        self.pagination_class = ExportPagination
        # Order queryset by ascending id, thus by descending age too
        queryset = self.get_queryset().order_by('pk')
        # Paginate queryset using custom paginator
        page = self.paginate_queryset(queryset)
        # Build dataset using paginated queryset
        dataset = AcademicLevelResource().export(page)
        # Build response object
        response = self.get_paginated_response(dataset.xls)
        # Add filename to response
        response['Content-Disposition'] = ''.join([
            'attachment; filename="AcademicLevel-',
            LOCAL_TIMEZONE.localize(datetime.now()).strftime("%Y%m%d-%H%M%S"),
            '".xls'
        ])
        return response


class AcademicFieldViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given academic field.

    list:
    Return a list of all the existing academic fields.

    create:
    Create a new academic field instance.
    """
    serializer_class = serializers.AcademicFieldSerializer
    queryset = AcademicField.objects.all()
    permission_classes = (permissions.IsAdminOrReadOnly,)
    ordering = ('name',)

    @action(detail=False, permission_classes=[IsAdminUser])
    def export(self, request):
        # Use custom paginator (by page, min/max 1000 objects/page)
        self.pagination_class = ExportPagination
        # Order queryset by ascending id, thus by descending age too
        queryset = self.get_queryset().order_by('pk')
        # Paginate queryset using custom paginator
        page = self.paginate_queryset(queryset)
        # Build dataset using paginated queryset
        dataset = AcademicFieldResource().export(page)
        # Build response object
        response = self.get_paginated_response(dataset.xls)
        # Add filename to response
        response['Content-Disposition'] = ''.join([
            'attachment; filename="AcademicField-',
            LOCAL_TIMEZONE.localize(datetime.now()).strftime("%Y%m%d-%H%M%S"),
            '".xls'
        ])
        return response
