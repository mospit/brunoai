#!/usr/bin/env python
"""
Emergency Schema Downgrade Script

This script provides a standalone way to downgrade from UUID-based schema
back to the original Integer-based schema without requiring Alembic.

Usage:
    python emergency_downgrade.py [--dry-run] [--backup-only] [--verify-only]

Options:
    --dry-run       Show what would be done without making changes
    --backup-only   Only create backups, don't perform downgrade
    --verify-only   Only verify current schema status
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.downgrade_schema import (
    SchemaDowngradeManager,
    perform_emergency_downgrade,
    verify_integer_schema
)


def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('emergency_downgrade.log')
        ]
    )


def main():
    """Main entry point for emergency downgrade script."""
    parser = argparse.ArgumentParser(
        description='Emergency UUID to Integer schema downgrade tool'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Only create backups, do not perform downgrade'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify current schema status'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force downgrade even if safety checks fail'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting emergency schema downgrade script...")
    
    try:
        downgrade_manager = SchemaDowngradeManager()
        
        if args.verify_only:
            logger.info("Verifying current schema status...")
            if verify_integer_schema():
                logger.info("✅ Schema is already in integer format")
                return 0
            else:
                logger.info("❌ Schema appears to be in UUID format or has issues")
                return 1
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info("Would perform the following operations:")
            logger.info("1. Validate downgrade safety")
            logger.info("2. Create UUID data backups")
            logger.info("3. Drop UUID constraints and columns")
            logger.info("4. Restore integer primary keys and foreign keys")
            logger.info("5. Verify downgrade success")
            return 0
        
        if args.backup_only:
            logger.info("BACKUP ONLY MODE - Creating UUID data backups...")
            if downgrade_manager.backup_uuid_data():
                logger.info("✅ UUID data backup completed successfully")
                return 0
            else:
                logger.error("❌ UUID data backup failed")
                return 1
        
        # Safety validation
        if not args.force:
            logger.info("Performing safety validation...")
            if not downgrade_manager.validate_downgrade_safety():
                logger.error("❌ Safety validation failed. Use --force to override.")
                return 1
            logger.info("✅ Safety validation passed")
        
        # Confirm with user unless forced
        if not args.force:
            response = input(
                "\n⚠️  WARNING: This will downgrade your schema from UUID to Integer format.\n"
                "This operation will:\n"
                "- Drop all UUID columns\n"
                "- Restore integer-based primary keys\n"
                "- May result in data loss if not properly backed up\n\n"
                "Are you sure you want to continue? (yes/no): "
            )
            if response.lower() not in ['yes', 'y']:
                logger.info("Operation cancelled by user")
                return 0
        
        # Execute the downgrade
        logger.info("Executing emergency schema downgrade...")
        success = perform_emergency_downgrade()
        
        if success:
            logger.info("✅ Emergency schema downgrade completed successfully")
            
            # Verify the result
            if verify_integer_schema():
                logger.info("✅ Schema verification passed - now in integer format")
                return 0
            else:
                logger.warning("⚠️  Downgrade completed but verification failed")
                return 1
        else:
            logger.error("❌ Emergency schema downgrade failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
