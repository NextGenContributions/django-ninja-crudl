"""Mixins for soft-delete handling."""

# pyright: reportUnusedParameter=false
import logging
from functools import reduce
from operator import attrgetter, or_
from typing import Generic, cast

from django.db import router, transaction
from django.db.models import Model, QuerySet, signals, sql
from django.db.models.deletion import Collector

from django_ninja_crudl.types import RequestDetails, TDjangoModel

logger = logging.getLogger(__name__)


class SoftDeleteMixin(Generic[TDjangoModel]):  # noqa: UP046
    """Mixin for soft-delete handling."""

    def soft_delete(
        self,
        qs: QuerySet[Model],
        request_details: RequestDetails[TDjangoModel],
        using_db: str,
    ) -> None:
        """Define how to soft-delete the given queryset of (related) objects.

        This must be implemented in CRUDL controller subclass if soft-delete is enabled.

        Args:
            qs: The queryset of (related) objects to soft-delete.
            request_details: The details of the request.
            using_db: The database alias to use.
        """
        msg = "soft_delete method must be implemented in subclass."
        raise NotImplementedError(msg)

    def soft_delete_obj(
        self,
        obj: TDjangoModel,
        request_details: RequestDetails[TDjangoModel],
    ) -> None:
        """Soft-delete an object.

        This implementation borrows heavily from Collector.delete() to replicate
        the same behavior as obj.delete(), but performing soft-deletion instead.
        """
        # Collect objects to be soft-deleted in cascade
        collector = self._collect_for_deletion(model=type(obj), obj=obj)
        logger.debug("Collected objects: %s", collector.data)

        # Sort instance collections
        for model, instances in collector.data.items():
            collector.data[model] = sorted(instances, key=attrgetter("pk"))

        # If possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        collector.sort()

        # - Avoid nested savepoint overhead: These code is called within an existing
        # transaction, 'savepoint=False' prevents creating a nested savepoint, which
        # would add overhead without benefit for this use case.
        # - All-or-nothing guarantee: Even though these code are nested within an outer
        # transaction, this atomic statement explicitly convey the intent of atomicity
        # for the entire deletion operation.
        with transaction.atomic(using=collector.using, savepoint=False):
            # Send pre_delete signals for collected instances
            self._send_pre_delete_signals(collector)

            # Handle objects that can be deleted without fetching into memory
            self._handle_fast_deletes(collector, request_details)

            # Update fields (SET, SET_DEFAULT, SET_NULL)
            self._handle_field_updates(collector)

            # Delete collected instances and send post_delete signals
            self._handle_collected_instances_and_post_delete_signals(
                collector, request_details
            )

    def _collect_for_deletion(
        self,
        *,
        model: type[TDjangoModel],
        obj: TDjangoModel,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> Collector:
        """Collect objects to be deleted in cascade.

        This method uses the same logic as obj.delete() to collect related objects.
        """
        using = using or router.db_for_write(model, instance=obj)
        collector = Collector(using=using, origin=obj)
        collector.collect([obj], keep_parents=keep_parents)  # type: ignore[reportArgumentType]
        return collector

    def _send_pre_delete_signals(self, collector: Collector) -> None:
        """Send pre_delete signals for collected instances."""
        for model, i in collector.instances_with_model():
            if not model._meta.auto_created:  # noqa: SLF001
                signals.pre_delete.send(  # pyright: ignore[reportUnknownMemberType]
                    sender=model,
                    instance=i,
                    using=collector.using,
                    origin=collector.origin,
                )

    def _handle_fast_deletes(
        self,
        collector: Collector,
        request_details: RequestDetails[TDjangoModel],
    ) -> None:
        """Handle deletion of objects that don't need to be fetched into memory."""
        qs: QuerySet[TDjangoModel]
        for qs in collector.fast_deletes:  # type: ignore[reportAssignmentType]
            self.soft_delete(
                qs=qs, request_details=request_details, using_db=collector.using
            )

    def _handle_field_updates(self, collector: Collector) -> None:
        """Handle field updates for related objects during deletion.

        This is for cases where 'on_delete' is set to SET, SET_DEFAULT, SET_NULL.
        This implementation is almost verbatim copy from Collector.delete().
        """
        for (field, value), instances_list in collector.field_updates.items():  # pyright: ignore[reportUnknownMemberType, reportAny, reportUnknownVariableType]
            updates: list[QuerySet[Model, object]] = []
            objs: list[Model] = []
            for instances in instances_list:
                if (
                    isinstance(instances, QuerySet) and instances._result_cache is None  # noqa: SLF001
                ):
                    updates.append(instances)  # ty:ignore[invalid-argument-type]
                else:
                    objs.extend(
                        instances  # ty:ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]
                    )
            if updates:
                combined_updates = reduce(or_, updates)  # pyright: ignore[reportAny]
                combined_updates.update(**{field.name: value})  # pyright: ignore[reportAny]
            if objs:
                model = objs[0].__class__
                query = sql.UpdateQuery(model)
                query.update_batch(
                    list({obj.pk for obj in objs}),  # pyright: ignore[reportAny]
                    {field.name: value},
                    collector.using,
                )

    def _handle_collected_instances_and_post_delete_signals(
        self,
        collector: Collector,
        request_details: RequestDetails[TDjangoModel],
    ) -> None:
        """Handle soft-deletion of collected instances and send post_delete signals."""
        # Reverse instance collections
        for instances in collector.data.values():
            instances = cast("list[Model]", instances)  # 'list' due to prior sorting
            instances.reverse()

        # Delete instances
        for model, instances in collector.data.items():
            pk_list = [obj.pk for obj in instances]  # pyright: ignore [reportAny]
            qs = model._default_manager.filter(pk__in=pk_list)  # noqa: SLF001
            self.soft_delete(
                qs=qs, request_details=request_details, using_db=collector.using
            )
            if not model._meta.auto_created:  # noqa: SLF001
                for i in instances:
                    signals.post_delete.send(  # pyright: ignore[reportUnknownMemberType]
                        sender=model,
                        instance=i,
                        using=collector.using,
                        origin=collector.origin,
                    )
