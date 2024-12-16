from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth
from home.models import CustomUser
import traceback
from firebase_admin._auth_utils import InvalidIdTokenError
from rest_framework.views import APIView
from .models import Video
import os
import subprocess
@api_view(['POST'])
def authorizeUser(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return Response({
            'error':'Authprozation header Missing'
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        #  Check if the user exists in your app's DB or perform any other checks as needed
        user , created  = CustomUser.objects.get_or_create(username= uid )
        if created:
            user.email = decoded_token.get('email', '')
            if user.email in ['admin@example.com']:
                user.role = 'admin'
            user.save()
        return Response(
            {
                'success':'true',
                'message':'User Authorized',
                'user_created':created,
                'role':user.role
            },
            status=status.HTTP_200_OK
        )
    except IndexError:
        return Response({
            'error':'Invalid Token Format'
        } , 
        status=status.HTTP_400_BAD_REQUEST
        )
    except InvalidIdTokenError as e:
        error_trace = traceback.format_exc()
        print("Invalid ID token error:", error_trace)
        return Response(
            {'error': 'Token verification failed due to clock skew. Please try again.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        error_trace = traceback.format_exc()  # Captures the full traceback as a string
        print(error_trace)  # Optionally print to console for debugging
        return Response(
            {
                'error': str(e),
                'details': error_trace  # Include the full traceback in the response if needed
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
class VideoUploadView(APIView):
    def get(self, request, movie_id):
        try:
            video = Video.objects.get(movie_id=movie_id)
            return Response({
                'success':'true',
                'result':{
                "movie_id": video.movie_id,
                "qualities": video.qualities
            }
            }, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({
                "error": "Video Not Found",
                'details':"Video DOes not Exist "
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            error_trace = traceback.format_exc()  # Captures the full traceback as a string
            print(error_trace)  # Optionally print to console for debugging
            return Response(
                {
                    'error': str(e),
                    'details': error_trace  # Include the full traceback in the response if needed
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def post(self, request, *args, **kwargs):
        movie_id = request.data.get("movie_id")
        file = request.FILES.get("file")

        if not movie_id or not file:
            return Response({"error": "Movie Id and file are required"}, status=status.HTTP_400_BAD_REQUEST)

        if Video.objects.filter(movie_id=movie_id).exists():
            return Response({"error": "Video with this Movie Id already Exists"}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = "media/videos/original"
        os.makedirs(upload_dir, exist_ok=True)
        original_path = os.path.join(upload_dir, file.name)

        # Save the uploaded file
        with open(original_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        # Call transcoding function
        transcoded_paths = self.transcode_video(original_path, file.name)

        video = Video.objects.create(
            movie_id=movie_id,
            qualities=transcoded_paths
        )
        return Response({
            "message": "Video Uploaded and Transcoded Successfully",
            "movie_id": movie_id,
            "qualities": transcoded_paths
        }, status=status.HTTP_201_CREATED)
    def transcode_video(self, original_path, file_name):
        transcoded_dir = "media/videos/transcoded"
        os.makedirs(transcoded_dir, exist_ok=True)
        # File paths for transcoded videos
        qualities = {
            "1080p": os.path.join(transcoded_dir, f"{file_name}_1080p.mp4"),
            "720p": os.path.join(transcoded_dir, f"{file_name}_720p.mp4"),
            "480p": os.path.join(transcoded_dir, f"{file_name}_480p.mp4")
        }
        ffmpeg_path = r"C:/FFmpeg/bin/ffmpeg.exe"
        ffmpeg_cmds = [
            [ffmpeg_path, "-i", original_path, "-vf", "scale=if(gte(iw\,2)*2\,iw\,iw/2*2):if(gte(ih\,2)*2\,ih\,ih/2*2)", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", qualities['1080p']],
            [ffmpeg_path, "-i", original_path, "-vf", "scale=if(gte(iw\,2)*2\,iw\,iw/2*2):if(gte(ih\,2)*2\,ih\,ih/2*2)", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", qualities['720p']],
            [ffmpeg_path, "-i", original_path, "-vf", "scale=if(gte(iw\,2)*2\,iw\,iw/2*2):if(gte(ih\,2)*2\,ih\,ih/2*2)", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", qualities['480p']],
        ]
        # Run the FFmpeg commands
        for cmd in ffmpeg_cmds:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred during transcoding: {e}")
                raise e  # Re-raise the exception to let the view handle it
        return qualities