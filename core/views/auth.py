from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

import json


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"message" : "Invalid method"}, status = 405)
    try:
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]
        username = email
        if not email or not password:
            return JsonResponse({"message" : "Email and password are required"}, status=400)

        if User.objects.filter(email= email).exists():
            return JsonResponse({"message" : "this account already exists"},  status=400)
        
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        return JsonResponse({"message" : "create new account successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"message" : "Error creating account", "error": str(e)}, status=500)
    


@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({"message" : "Invalid method"}, status=405)
    try:
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]

        if not email or not password:
            return JsonResponse({"message" : "Email and password are required"}, status=400)

        user = authenticate(request, username= email, password=password)

        if user is not None:
            login(request, user)
            print("after login session_key:", request.session.session_key)
            print("session modified:", request.session.modified)
            return JsonResponse({"message": "login successfully"}, status=200)
        return JsonResponse({"message" : "Invalid account"}, status=401)
    except Exception as e:
        return JsonResponse({"message" : "Error logging in", "error": str(e)}, status=500)
    

def logout_user(request):
    # print("logout_user hit", request.method, request.path, request.user)
    if request.method != "POST":
        return JsonResponse({"message": "Invalid method"}, status=405)
    logout(request)
    return JsonResponse({"message": "logout successfully"}, status=200)


def current_user(request):
    print('cookies', request.COOKIES)
    print('session key', request.session.session_key)

    print('debug current_user hit', request.method, request.path, request.user)
    if request.method != "GET":
        return JsonResponse({"message": "Invalid method"}, status=405)

    print('debug current_user user', request.user)
    if not request.user.is_authenticated:
        print('debug current_user not authenticated')
        return JsonResponse({"authenticated": False}, status=401)
    print('debug current_user authenticated')
    return JsonResponse(
        {
            "authenticated": True,
            "user": {
                "id": request.user.id,
                "email": request.user.email,
            },
        },
        status=200,
    )


