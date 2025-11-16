from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Defect, Attachment, Comment
from .serializers import DefectSerializer, AttachmentSerializer, CommentSerializer
from .permissions import DefectPermission
from .services import change_status, can_assign_performer

class DefectViewSet(viewsets.ModelViewSet):
    serializer_class = DefectSerializer
    permission_classes = [IsAuthenticated, DefectPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project", "performer", "status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "deadline"]

    def get_queryset(self):
        qs = Defect.objects.select_related("project", "stage", "performer")
        user = self.request.user
        if user.is_manager:
            return qs
        if user.is_engineer:
            return qs.filter(project__members=user)
        return qs.filter(project__members=user)

    def perform_create(self, serializer):
        performer = serializer.validated_data.get("performer")
        if not can_assign_performer(self.request.user, performer):
            raise ValueError("Нельзя назначить наблюдателя исполнителем")
        serializer.save()

    def perform_update(self, serializer):
        performer = serializer.validated_data.get("performer")
        if performer is not None and not can_assign_performer(self.request.user, performer):
            raise ValueError("Нельзя назначить наблюдателя исполнителем")
        serializer.save()

    @action(detail=True, methods=["post"]) 
    def change_status(self, request, pk=None):
        defect = self.get_object()
        new_status = request.data.get("status")
        try:
            change_status(defect, new_status, request.user)
        except (ValueError, PermissionError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DefectSerializer(defect).data)

    @action(detail=True, methods=["get", "post"], parser_classes=[MultiPartParser, FormParser])
    def attachments(self, request, pk=None):
        defect = self.get_object()
        if request.method == "GET":
            return Response(AttachmentSerializer(defect.attachments.all(), many=True).data)
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "file required"}, status=400)
        a = Attachment.objects.create(defect=defect, file=file)
        return Response(AttachmentSerializer(a).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        defect = self.get_object()
        if request.method == "GET":
            return Response(CommentSerializer(defect.comments.all(), many=True).data)
        text = request.data.get("text")
        if not text:
            return Response({"detail": "text required"}, status=400)
        c = Comment.objects.create(defect=defect, author=request.user, text=text)
        return Response(CommentSerializer(c).data, status=201)