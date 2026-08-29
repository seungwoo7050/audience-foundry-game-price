from django.contrib import admin

from .models import (
    AuditEvent,
    Game,
    IngestionRun,
    PriceObservation,
    PublishedPriceProjection,
    SourceReceipt,
    Store,
    StoreProduct,
    VerificationDecision,
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("canonical_title", "slug", "publication_state", "updated_at")
    search_fields = ("canonical_title", "slug")


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("code", "display_name", "source_state", "terms_approval_decision")


@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    list_display = (
        "external_product_id",
        "store",
        "game",
        "edition_label",
        "region",
        "mapping_state",
    )
    list_filter = ("mapping_state", "region", "store")


@admin.register(VerificationDecision)
class VerificationDecisionAdmin(admin.ModelAdmin):
    list_display = ("subject_type", "subject_identity", "decision", "actor_identity", "decided_at")
    readonly_fields = ("id", "schema_version", "decided_at")

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False


class EvidenceAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(IngestionRun, EvidenceAdmin)
admin.site.register(SourceReceipt, EvidenceAdmin)
admin.site.register(PriceObservation, EvidenceAdmin)
admin.site.register(AuditEvent, EvidenceAdmin)
admin.site.register(PublishedPriceProjection, EvidenceAdmin)
