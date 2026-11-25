from django.db import models


class ActivityLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=30)      # PIN, DEPOSIT, WITHDRAWAL, LOCK...
    account = models.CharField(max_length=30, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%b %d %H:%M:%S} {self.action} {'OK' if self.success else 'FAILED'}"