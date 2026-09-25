# apps/users/exceptions.py
from rest_framework import status
from rest_framework.exceptions import APIException


class AlreadyInCouple(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "You already belong to a couple."
    default_code = "couple_exists"


class NotInCouple(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = (
        "You are not part of any couple yet. Go find your other half 😉"
    )
    default_code = "no_couple"


class InvalidInvite(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid invite code or you are already taken."
    default_code = "invalid_invite"
