from base64 import urlsafe_b64decode, urlsafe_b64encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import DjangoUnicodeDecodeError, force_str, force_bytes
from django.shortcuts import redirect
from django.core.mail import EmailMessage

from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView

from user.serializers import (
    ChangePasswordSerializer,
    FriendSerializer,
    ProfileAlbumSerializer,
    SignupSerializer,
    CustomTokenObtainPairSerializer,
    UserDelSerializer,
    ProfileSerializer,
    PasswordResetSerializer,
    SetNewPasswordSerializer,
    EmailThread,
    UserUpdateSerializer,
)

from my_settings import (
    KAKAO_REST_API_KEY,
    
)

from .models import Friend, ProfileAlbum, User, Profile

import requests


# ================================ 회원가입, 회원정보 시작 ================================
class UserView(APIView):
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        if self.request.method == "PATCH" or self.request.method == "DELETE":
            return [IsAuthenticated(),]
        else:
            return super(UserView, self).get_permissions()
    
    # 개인정보 보기
    def get(self, request):
        user = get_object_or_404(User, id = request.user.id)
        serializer = SignupSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # 회원가입
    def post(self,request):
        serializer = SignupSerializer(data=request.data)
        
        
        if serializer.is_valid():
           serializer.save()
           return Response({"message" : "회원가입 완료!"} , status=status.HTTP_201_CREATED)
       
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 회원정보수정
    def patch (self, request):
        user = get_object_or_404(User, id=request.user.id)
        serializer = UserUpdateSerializer(user, data=request.data, context={"request": request}, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "수정완료!"}, status=status.HTTP_200_OK)
        
        else:
            return Response( {"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    # 회원 탈퇴 (비활성화, 비밀번호 받아서)
    def delete(self, request):
        user = get_object_or_404(User, id=request.user.id)
        datas = request.data.copy()  # request.data → request.data.copy() 변경
        # request.data는 Django의 QueryDict 객체로서 변경이 불가능하여 복사하여 수정한 후 전달하는 방법을 이용!
        datas["is_active"] = False
        serializer = UserDelSerializer(user, data=datas)
        if user.check_password(request.data.get("password")):
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "계정 비활성화 완료"}, status=status.HTTP_204_NO_CONTENT)
            
        else:
            return Response({"message": f"패스워드가 다릅니다"}, status=status.HTTP_400_BAD_REQUEST)

# ================================ 회원가입, 회원정보 끝 ================================


# ================================ 로그인 ================================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    
# ================================ 비밀번호 변경 ================================
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = get_object_or_404(User, id=request.user.id)
        serializer = ChangePasswordSerializer(user, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "비밀번호 변경이 완료되었습니다! 다시 로그인해주세요."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# ================================ 프로필 시작 ================================

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    # 요청 유저의 정보를 가져올 때 사용할 get_object 인스턴스 정의
    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)
    
    # 프로필 보기
    def get(self, request, user_id):
        profile = get_object_or_404(Profile, user = user_id)
        user = get_object_or_404(User, id=user_id)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # 프로필 수정
    def patch(self, request, user_id):
        user = self.get_object(user_id) # 요청 유저의 정보 가져오기
        
        if user == request.user:
            profile = get_object_or_404(Profile, id = user_id)
            serializer = ProfileSerializer(profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "프로필 수정이 완료되었습니다."}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({"message": "권한이 없습니다!"}, status=status.HTTP_403_FORBIDDEN)
        
        
class ProfileAlbumView(APIView):
    permission_classes = [IsAuthenticated]
    # 요청 유저의 정보를 가져올 때 사용할 get_object 인스턴스 정의
    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)
    
    # 사진첩 보기
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        album_img = get_object_or_404(ProfileAlbum, user = user_id)
        serializer = ProfileAlbumSerializer(album_img)
        return Response(serializer.data, status=status.HTTP_200_OK)     
    
    # # 사진 올리기
    # def post(self, request, user_id):
    #     user = get_object_or_404(User, id = request.user.id)
    #     album_img = get_object_or_404(ProfileAlbum, user = user_id)
    #     serializer = ProfileAlbumSerializer(album_img)
    #     if serializer.is_valid():
    #        serializer.save()
    #        return Response({"message" : "등록 완료!"} , status=status.HTTP_201_CREATED)
       
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)      
        
        
# ================================ 프로필 끝 ================================



# ================================ 비밀번호 재설정 시작 ================================

# 이메일 보내기
class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "비밀번호 재설정 이메일"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 재설정 토큰 확인
class PasswordTokenCheckView(APIView):
    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_b64decode(uidb64))
            user = get_object_or_404(User, id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"message": "링크가 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED
                )

            return Response(
                {"uidb64": uidb64, "token": token}, status=status.HTTP_200_OK
            )

        except DjangoUnicodeDecodeError as identifier:
            return Response(
                {"message": "링크가 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )

# 비밀번호 재설정
class SetNewPasswordView(APIView):
    def put(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "비밀번호 재설정 완료"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ================================ 비밀번호 재설정 끝 ================================

    

# ================================ 친구맺기 시작 ================================

# 친구신청
class FriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from_user = request.user
        to_user = get_object_or_404(User, id=user_id)
        serializer = FriendSerializer(data={'from_user': from_user, 'to_user': to_user})
        serializer.is_valid(raise_exception=True)
        friend_request = serializer.save()

        return Response({"message": "친구 신청을 보냈습니다."}, status=status.HTTP_201_CREATED)

# 친구신청 수락
class FriendAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_request_id):
        friend_request = get_object_or_404(Friend, id=friend_request_id)
        if friend_request.to_user != request.user:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        if friend_request.status != 'pending':
            return Response({"message": "이미 처리된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request.status = 'accepted'
        friend_request.save()

        from_user = friend_request.from_user
        to_user = friend_request.to_user
        from_user.friends.add(to_user)
       
        return Response({"message": "친구 신청을 수락했습니다."}, status=status.HTTP_200_OK)

# 친구신청 거절
class FriendRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_request_id):
        friend_request = get_object_or_404(Friend, id=friend_request_id)
        if friend_request.to_user != request.user:
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        if friend_request.status != 'pending':
            return Response({"message": "이미 처리된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request.status = 'rejected'
        friend_request.save()

        return Response({"message": "친구 신청을 거절했습니다."}, status=status.HTTP_200_OK)
    

# ================================ 친구맺기 끝 ================================



# ================================ 소셜 로그인 시작 ================================

# 카카오로그인
class KakaoLoginView(APIView):

    def get(self, request):
        return Response(KAKAO_REST_API_KEY, status=status.HTTP_200_OK)

    def post(self, request):
        auth_code = request.data.get("code")
        kakao_token_api = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_REST_API_KEY,
            "redirect_uri": "http://127.0.0.1:5500/index.html",
            "code": auth_code,
        }
        kakao_token = requests.post(
            kakao_token_api,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
        )
        access_token = kakao_token.json().get("access_token")
        user_data = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )
        user_data = user_data.json()
        data = {
            "avatar": user_data.get("properties").get("profile_image"),
            "email": user_data.get("kakao_account").get("email"),
            "nickname": user_data.get("properties").get("nickname"),
            "gender": user_data.get("properties").get("gender"),
            "login_type": "kakao",
        }
        return SocialLogin(**data)

# # 구글로그인
# class GoogleLoginView(APIView):

#     def get(self, request):
#         return Response(GOOGLE_API_KEY, status=status.HTTP_200_OK)

#     def post(self, request):
#         access_token = request.data["access_token"]
#         user_data = requests.get(
#             "https://www.googleapis.com/oauth2/v2/userinfo",
#             headers={"Authorization": f"Bearer {access_token}"},
#         )
#         user_data = user_data.json()
#         data = {
#             "avatar": user_data.get("picture"),
#             "email": user_data.get("email"),
#             "nickname": user_data.get("name"),
#             "login_type": "google",
#         }
#         return SocialLogin(**data)

# # 네이버로그인
# class NaverLoginView(APIView):

#     def get(self, request):
#         return Response(NAVER_API_KEY, status=status.HTTP_200_OK)

#     def post(self, request):
#         code = request.data.get("naver_code")
#         state = request.data.get("state")
#         access_token = requests.post(
#             f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&code={code}&client_id={NAVER_API_KEY}&client_secret={NAVER_SECRET_KEY}&state={state}",
#             headers={"Accept": "application/json"},
#         )
#         access_token = access_token.json().get("access_token")
#         user_data = requests.get(
#             "https://openapi.naver.com/v1/nid/me",
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Accept": "application/json",
#             },
#         )
#         user_data = user_data.json().get("response")
#         data = {
#             "avatar": user_data.get("profile_image"),
#             "email": user_data.get("email"),
#             "nickname": user_data.get("nickname"),
#             "login_type": "naver",
#         }
#         return SocialLogin(**data)


# def SocialLogin(**kwargs):
#     # 각각 소셜 로그인에서 email, nickname, login_type등을 받아옴!!
#     data = {k: v for k, v in kwargs.items() if v is not None}
#     # none인 값들은 빼줌
#     email = data.get("email")
#     login_type = data.get("login_type")
#     # 그 중 email이 없으면 회원가입이 불가능하므로
#     # 프론트에서 메시지를 띄워주고, 다시 로그인 페이지로 이동시키기
#     if not email:
#         return Response(
#             {"error": "해당 계정에 email정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
#         )
#     try:
#         user = User.objects.get(email=email)
#         # 로그인 타입까지 같으면, 토큰 발행해서 프론트로 보내주기
#         if login_type == user.login_type:
#             refresh = RefreshToken.for_user(user)
#             access_token = CustomTokenObtainPairSerializer.get_token(user)
#             return Response(
#                 {"refresh": str(refresh), "access": str(access_token.access_token)},
#                 status=status.HTTP_200_OK,
#             )
#         # 유저의 다른 소셜계정으로 로그인한 유저라면, 해당 로그인 타입을 보내줌.
#         # (프론트에서 "{login_type}으로 로그인한 계정이 있습니다!" alert 띄워주기)
#         else:
#             return Response(
#                 {"error": f"{user.login_type}으로 이미 가입된 계정이 있습니다!"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#     # 유저가 존재하지 않는다면 회원가입시키기
#     except User.DoesNotExist:
#         new_user = User.objects.create(**data)
#         # pw는 사용불가로 지정
#         new_user.set_unusable_password()
#         new_user.save()
#         # 이후 토큰 발급해서 프론트로
#         refresh = RefreshToken.for_user(new_user)
#         access_token = CustomTokenObtainPairSerializer.get_token(new_user)
#         return Response(
#             {"refresh": str(refresh), "access": str(access_token.access_token)},
#             status=status.HTTP_200_OK,
#         )
        
        
        
# ================================ 소셜 로그인 끝 ================================
