"""WLED scheduler service."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.integrations.wled import WLEDIntegration
from app.models.wled_schedule import WLEDSchedule

logger = logging.getLogger(__name__)


class WLEDSchedulerService:
    """Service for scheduling WLED automations."""

    def __init__(self):
        """Initialize scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.running = False

    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting WLED scheduler...")
        self.scheduler.start()
        self.running = True

        # Load and schedule all enabled schedules
        await self.load_schedules()

        logger.info("WLED scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return

        logger.info("Stopping WLED scheduler...")
        self.scheduler.shutdown(wait=False)
        self.running = False
        logger.info("WLED scheduler stopped")

    async def load_schedules(self):
        """Load all enabled schedules from database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WLEDSchedule).where(WLEDSchedule.enabled == True)
            )
            schedules = list(result.scalars().all())

            for schedule in schedules:
                await self.add_schedule(schedule)

            logger.info(f"Loaded {len(schedules)} WLED schedules")

    async def add_schedule(self, schedule: WLEDSchedule):
        """
        Add a schedule to the scheduler.

        Args:
            schedule: Schedule to add
        """
        try:
            # Check if schedule is active (within date range)
            now = datetime.utcnow()
            if schedule.start_date and now < schedule.start_date:
                logger.debug(f"Schedule {schedule.id} not started yet")
                return
            if schedule.end_date and now > schedule.end_date:
                logger.debug(f"Schedule {schedule.id} has ended")
                return

            # Create cron trigger
            trigger = CronTrigger.from_crontab(schedule.cron_expression)

            # Add job to scheduler
            self.scheduler.add_job(
                self._execute_schedule,
                trigger=trigger,
                args=[schedule.id],
                id=f"wled_schedule_{schedule.id}",
                replace_existing=True,
            )

            # Calculate and store next run time
            next_run = self.scheduler.get_job(f"wled_schedule_{schedule.id}").next_run_time

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(WLEDSchedule).where(WLEDSchedule.id == schedule.id)
                )
                db_schedule = result.scalar_one_or_none()
                if db_schedule:
                    db_schedule.next_run = next_run
                    await db.commit()

            logger.info(
                f"Added schedule {schedule.id} ({schedule.name}) - "
                f"next run: {next_run}"
            )

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule.id}: {e}")

    async def remove_schedule(self, schedule_id: int):
        """
        Remove a schedule from the scheduler.

        Args:
            schedule_id: Schedule ID to remove
        """
        try:
            job_id = f"wled_schedule_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed schedule {schedule_id}")
        except Exception as e:
            logger.error(f"Failed to remove schedule {schedule_id}: {e}")

    async def update_schedule(self, schedule: WLEDSchedule):
        """
        Update a schedule in the scheduler.

        Args:
            schedule: Updated schedule
        """
        await self.remove_schedule(schedule.id)
        if schedule.enabled:
            await self.add_schedule(schedule)

    async def _execute_schedule(self, schedule_id: int):
        """
        Execute a schedule.

        Args:
            schedule_id: Schedule ID to execute
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get schedule
                result = await db.execute(
                    select(WLEDSchedule).where(WLEDSchedule.id == schedule_id)
                )
                schedule = result.scalar_one_or_none()

                if not schedule:
                    logger.error(f"Schedule {schedule_id} not found")
                    return

                if not schedule.enabled:
                    logger.debug(f"Schedule {schedule_id} is disabled, skipping")
                    return

                # Check date range
                now = datetime.utcnow()
                if schedule.start_date and now < schedule.start_date:
                    logger.debug(f"Schedule {schedule_id} not started yet")
                    return
                if schedule.end_date and now > schedule.end_date:
                    logger.info(f"Schedule {schedule_id} has ended, disabling")
                    schedule.enabled = False
                    await db.commit()
                    await self.remove_schedule(schedule_id)
                    return

                logger.info(f"Executing schedule {schedule_id} ({schedule.name})")

                # Create WLED service
                wled_service = WLEDIntegration(db)

                # Build state from preset or custom state
                if schedule.preset_id:
                    state = {"ps": schedule.preset_id}
                elif schedule.state:
                    state = schedule.state
                else:
                    logger.error(f"Schedule {schedule_id} has no action defined")
                    return

                # Apply to devices or sync group
                if schedule.sync_group:
                    devices_updated = await wled_service.apply_to_all_synced(
                        schedule.sync_group, state
                    )
                    logger.info(
                        f"Applied to {devices_updated} devices in group "
                        f"'{schedule.sync_group}'"
                    )
                elif schedule.device_ids:
                    devices_updated = 0
                    for device_id in schedule.device_ids:
                        success = await wled_service.set_device_state(
                            device_id, state
                        )
                        if success:
                            devices_updated += 1

                    logger.info(
                        f"Applied to {devices_updated}/{len(schedule.device_ids)} devices"
                    )
                else:
                    logger.error(f"Schedule {schedule_id} has no target devices")
                    return

                # Update execution tracking
                schedule.last_run = now
                schedule.run_count += 1

                # Update next run time
                job = self.scheduler.get_job(f"wled_schedule_{schedule_id}")
                if job:
                    schedule.next_run = job.next_run_time

                await db.commit()

                logger.info(
                    f"Schedule {schedule_id} executed successfully "
                    f"(run #{schedule.run_count})"
                )

            except Exception as e:
                logger.exception(f"Failed to execute schedule {schedule_id}: {e}")


# Global scheduler instance
_scheduler_instance: Optional[WLEDSchedulerService] = None


def get_scheduler() -> WLEDSchedulerService:
    """Get global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WLEDSchedulerService()
    return _scheduler_instance


async def start_scheduler():
    """Start global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop global scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
