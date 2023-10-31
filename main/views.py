from django.shortcuts import get_object_or_404

import ffmpeg
import os

from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status

from main.serializers import (
    UploadTargetFilesSerializer,
    UploadSourceFilesSerializer,
    UpdateSourceFilesSerializer,
    OrderRetrieveSerializer,
    SourceFileSerializer,
    TrimFileVideoSerializer,
    GetPreviewofVideoFileSerializer,
)
from main.models import Order, SourceFile
from main.helpers import generate_zip_of_order_images
from main.services.execute_order import ExecuteOrderService
from main.services.get_preview_video import GetPreviewVideoService
from main.services.trim_video import TrimVideoService


class UploadTargetFilesView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = UploadTargetFilesSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderRetrieveSerializer(instance=order).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadSourceFilesView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        serializer = UploadSourceFilesSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            source_files = serializer.save()
            return Response(SourceFileSerializer(source_files, many=True).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateSourceFilesView(APIView):
    def patch(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        serializer = UpdateSourceFilesSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.update(instance=order, validated_data=serializer.validated_data)
            return Response(OrderRetrieveSerializer(instance=order).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrimVideoFileView(APIView):
    def post(self, request, pk):
        serializer = TrimFileVideoSerializer(data=request.data)
        if serializer.is_valid():
            source_file = get_object_or_404(SourceFile, id=pk)
            TrimVideoService(
                source_file=source_file,
                start=serializer.validated_data['start'],
                end=serializer.validated_data['end'],
            ).trim_video()

            return Response(SourceFileSerializer(source_file).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPreviewOfDeepfakedVideoFileView(APIView):
    def post(self, request, pk):
        serializer = GetPreviewofVideoFileSerializer(data=request.data)
        if serializer.is_valid():
            source_file = get_object_or_404(SourceFile, id=pk)
            service = GetPreviewVideoService(
                source_file=source_file,
                moment=serializer.validated_data['moment'],
                deepfaked=True,
            )
            service.get_preview()

            return Response(SourceFileSerializer(source_file).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetPreviewOfVideoFileView(APIView):
    def post(self, request, pk):
        serializer = GetPreviewofVideoFileSerializer(data=request.data)
        if serializer.is_valid():
            source_file = get_object_or_404(SourceFile, id=pk)
            service = GetPreviewVideoService(
                source_file=source_file,
                moment=serializer.validated_data['moment'],
                deepfaked=False,
            )
            service.get_preview()

            return Response(SourceFileSerializer(source_file).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderReadOnlyViewSet(ReadOnlyModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderRetrieveSerializer


class ExecuteOrderView(APIView):
    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        ExecuteOrderService(order).run()

        return Response(OrderRetrieveSerializer(instance=order).data, status=status.HTTP_200_OK)


class DownloadOrderResultsView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk)

        file_name = f"images-order-{order.id}.zip"

        response = Response(content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)

        return generate_zip_of_order_images(
            order=order,
            response=response
        )
