"""
Background scheduler service for Bruno AI.

This service handles:
- Nightly expiration checks
- Automated notifications
- Background maintenance tasks
"""

import asyncio
import logging
from datetime import datetime, time
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_async_session
from ..models.user import Household
from .expiration_service import ExpirationService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing background scheduled tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler service started")
            
            # Schedule nightly expiration checks at 6 AM daily
            self.scheduler.add_job(
                self.nightly_expiration_check,
                trigger=CronTrigger(hour=6, minute=0),
                id="nightly_expiration_check",
                name="Nightly Expiration Check",
                replace_existing=True
            )
            
            # Schedule weekly cleanup at 2 AM on Sundays
            self.scheduler.add_job(
                self.weekly_cleanup,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
                id="weekly_cleanup",
                name="Weekly Cleanup",
                replace_existing=True
            )
            
            logger.info("Scheduled tasks registered")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler service stopped")
    
    async def nightly_expiration_check(self):
        """
        Nightly job to check for items expiring within 3 days and send notifications.
        """
        logger.info("Starting nightly expiration check")
        
        try:
            # Get database session
            async for db in get_async_session():
                # Get all households
                result = await db.execute(select(Household))
                households = result.scalars().all()
                
                logger.info(f"Checking expiration for {len(households)} households")
                
                for household in households:
                    await self._process_household_expiration_check(db, household)
                
                logger.info("Nightly expiration check completed successfully")
                
        except Exception as e:
            logger.error(f"Error during nightly expiration check: {e}")
            raise
    
    async def _process_household_expiration_check(self, db: AsyncSession, household: Household):
        """
        Process expiration check for a single household.
        
        Args:
            db: Database session
            household: Household to process
        """
        try:
            # Get expiring items for this household
            expiring_items = await ExpirationService.get_expiring_items(
                db=db,
                household_id=household.id,
                days_ahead=3
            )
            
            # Get expired items
            expired_items = await ExpirationService.get_expired_items(
                db=db,
                household_id=household.id
            )
            
            # Only send notifications if there are items to report
            if expiring_items or expired_items:
                await self._send_household_expiration_notifications(
                    household=household,
                    expiring_items=expiring_items,
                    expired_items=expired_items
                )
                
                logger.info(
                    f"Processed household {household.id}: "
                    f"{len(expiring_items)} expiring, {len(expired_items)} expired"
                )
            
        except Exception as e:
            logger.error(f"Error processing household {household.id}: {e}")
    
    async def _send_household_expiration_notifications(
        self,
        household: Household,
        expiring_items: List,
        expired_items: List
    ):
        """
        Send expiration notifications to household members.
        
        Args:
            household: Household to notify
            expiring_items: Items expiring within 3 days
            expired_items: Items that have already expired
        """
        try:
            # Prepare notification data
            notification_data = {
                "household_id": household.id,
                "household_name": household.name,
                "expiring_count": len(expiring_items),
                "expired_count": len(expired_items),
                "expiring_items": [
                    {
                        "name": item.name,
                        "expiration_date": item.expiration_date.isoformat(),
                        "days_left": (item.expiration_date - datetime.now().date()).days
                    }
                    for item in expiring_items
                ],
                "expired_items": [
                    {
                        "name": item.name,
                        "expiration_date": item.expiration_date.isoformat(),
                        "days_expired": (datetime.now().date() - item.expiration_date).days
                    }
                    for item in expired_items
                ]
            }
            
            # Send notifications via NotificationService
            await NotificationService.send_expiration_notifications(
                household=household,
                notification_data=notification_data
            )
            
        except Exception as e:
            logger.error(f"Error sending notifications for household {household.id}: {e}")
    
    async def weekly_cleanup(self):
        """
        Weekly cleanup job to remove very old expired items and clean up data.
        """
        logger.info("Starting weekly cleanup")
        
        try:
            async for db in get_async_session():
                # This could include:
                # - Archiving very old expired items (30+ days expired)
                # - Cleaning up old notification logs
                # - Updating statistics
                
                # For now, just log the cleanup
                logger.info("Weekly cleanup completed - no cleanup actions implemented yet")
                
        except Exception as e:
            logger.error(f"Error during weekly cleanup: {e}")
            
    async def trigger_immediate_expiration_check(self, household_id: int = None):
        """
        Trigger an immediate expiration check for testing or manual triggers.
        
        Args:
            household_id: Optional specific household ID to check
        """
        logger.info(f"Triggering immediate expiration check for household: {household_id}")
        
        try:
            async for db in get_async_session():
                if household_id:
                    # Check specific household
                    result = await db.execute(
                        select(Household).where(Household.id == household_id)
                    )
                    household = result.scalar_one_or_none()
                    if household:
                        await self._process_household_expiration_check(db, household)
                        logger.info(f"Completed immediate check for household {household_id}")
                    else:
                        logger.warning(f"Household {household_id} not found")
                else:
                    # Check all households
                    await self.nightly_expiration_check()
                    
        except Exception as e:
            logger.error(f"Error during immediate expiration check: {e}")
            raise


# Global scheduler instance
scheduler_service = SchedulerService()
