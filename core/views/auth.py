from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import json


@csrf_exempt
def register_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]
        username = email

        if User.objects.filter(email= email).exists():
            return JsonResponse({"message" : "this account already exists"},  status=400)
        
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        return JsonResponse({"message" : "create new account successfully"}, status=200)
    return JsonResponse({"message" : "Invalid method"}, status = 405)


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]

        user = authenticate(request, username= email, password=password)

        if user is not None:
            login(request, user)
            print("current user" , request.user)
            print("session key", request.session.session_key)
            return JsonResponse({"message": "login successfully"})
        return JsonResponse({"message" : "Invalid account"}, status=401)
    return JsonResponse({"message" : "Invalid method"}, status=405)


@csrf_exempt
def jwt_login(request):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON body"}, status=400)

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return JsonResponse({"message": "Email and password are required"}, status=400)

    # Keep same auth behavior as login_user: email is used as username.
    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({"message": "Invalid account"}, status=401)

    refresh = RefreshToken.for_user(user)
    return JsonResponse(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        },
        status=200,
    )


@csrf_exempt
def jwt_refresh(request):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON body"}, status=400)

    refresh_token = data.get("refresh", "").strip()
    if not refresh_token:
        return JsonResponse({"message": "Refresh token is required"}, status=400)

    try:
        refresh = RefreshToken(refresh_token)
        return JsonResponse({"access": str(refresh.access_token)}, status=200)
    except TokenError:
        return JsonResponse({"message": "Invalid or expired refresh token"}, status=401)


