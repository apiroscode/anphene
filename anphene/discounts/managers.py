from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class VoucherQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(usage_limit__isnull=True) | Q(used__lt=F("usage_limit")),
            Q(end_date__isnull=True) | Q(end_date__gte=date),
            start_date__lte=date,
        )

    def expired(self, date):
        return self.filter(
            Q(used__gte=F("usage_limit")) | Q(end_date__lt=date), start_date__lt=date
        )


class SaleQueryset(models.QuerySet):
    def active(self, date=None):
        if date is None:
            date = timezone.now()
        return self.filter(Q(end_date__isnull=True) | Q(end_date__gte=date), start_date__lte=date)

    def expired(self, date=None):
        if date is None:
            date = timezone.now()
        return self.filter(end_date__lt=date, start_date__lt=date)
