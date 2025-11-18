from django.db import transaction
from users.models import User
from .models import Defect, StatusHistory

ALLOWED_TRANSITIONS = {
    Defect.STATUS_NEW: {Defect.STATUS_IN_PROGRESS, Defect.STATUS_CANCELLED},
    Defect.STATUS_IN_PROGRESS: {Defect.STATUS_REVIEW, Defect.STATUS_CANCELLED},
    Defect.STATUS_REVIEW: {Defect.STATUS_CLOSED},
}

def can_assign_performer(user: User, performer: User):
    if performer and performer.is_observer:
        return False
    return True

@transaction.atomic
def change_status(defect: Defect, new_status: str, actor: User):
    current = defect.status
    if new_status == current:
        return defect
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError("Недопустимый переход статуса")
    if actor.is_engineer:
        if defect.performer_id != actor.id:
            raise PermissionError("Инженер может редактировать только свои дефекты")
        if not (
            (current == Defect.STATUS_NEW and new_status == Defect.STATUS_IN_PROGRESS) or
            (current == Defect.STATUS_IN_PROGRESS and new_status == Defect.STATUS_REVIEW)
        ):
            raise PermissionError("Недостаточно прав для изменения статуса")
    if new_status == Defect.STATUS_CLOSED and current != Defect.STATUS_REVIEW:
        raise ValueError("Нельзя закрыть дефект если статус не 'На проверке'")
    StatusHistory.objects.create(defect=defect, old_status=current, new_status=new_status, changed_by=actor)
    defect.status = new_status
    defect.save(update_fields=["status", "updated_at"])
    return defect