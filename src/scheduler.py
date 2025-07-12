import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

class EmailSummaryScheduler:
    def __init__(self, interval_hours: int = 6):
        self.interval_hours = interval_hours
        self.running = False
        self.scheduler_thread = None
        self.job_function = None
        
    def set_job_function(self, func: Callable):
        """Set the function to be called on schedule"""
        self.job_function = func
        
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.running:
            logging.warning("Scheduler is already running")
            return
            
        if not self.job_function:
            raise ValueError("No job function set. Use set_job_function() first.")
        
        self.running = True
        
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule the job
        schedule.every(self.interval_hours).hours.do(self._safe_job_wrapper)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        next_run = datetime.now() + timedelta(hours=self.interval_hours)
        logging.info(f"Email summary scheduler started. Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run immediately on start
        self._safe_job_wrapper()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logging.info("Email summary scheduler stopped")
    
    def run_now(self):
        """Run the job immediately"""
        if self.job_function:
            logging.info("Running email summary job manually")
            self._safe_job_wrapper()
        else:
            logging.error("No job function set")
    
    def update_interval(self, hours: int):
        """Update the scheduling interval"""
        if hours < 1 or hours > 24:
            raise ValueError("Interval must be between 1 and 24 hours")
        
        self.interval_hours = hours
        
        if self.running:
            # Restart with new interval
            self.stop()
            time.sleep(1)
            self.start()
            
        logging.info(f"Scheduler interval updated to {hours} hours")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            next_run = jobs[0].next_run
            return next_run
        return None
    
    def get_status(self) -> dict:
        """Get scheduler status information"""
        next_run = self.get_next_run_time()
        
        return {
            'running': self.running,
            'interval_hours': self.interval_hours,
            'next_run': next_run.isoformat() if next_run else None,
            'jobs_count': len(schedule.get_jobs())
        }
    
    def _run_scheduler(self):
        """Main scheduler loop (runs in separate thread)"""
        logging.info("Scheduler thread started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                time.sleep(60)
        
        logging.info("Scheduler thread stopped")
    
    def _safe_job_wrapper(self):
        """Wrapper that safely executes the job function with error handling"""
        try:
            logging.info("Starting scheduled email summary job")
            start_time = datetime.now()
            
            self.job_function()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logging.info(f"Email summary job completed successfully in {duration:.1f} seconds")
            
        except Exception as e:
            logging.error(f"Email summary job failed: {e}")
            # Could send error notification here if needed


class ManualRunner:
    """Simple class for running email summaries manually without scheduling"""
    
    def __init__(self):
        self.job_function = None
    
    def set_job_function(self, func: Callable):
        """Set the function to be called"""
        self.job_function = func
    
    def run(self):
        """Run the job immediately"""
        if not self.job_function:
            raise ValueError("No job function set. Use set_job_function() first.")
        
        try:
            logging.info("Starting manual email summary")
            start_time = datetime.now()
            
            self.job_function()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logging.info(f"Manual email summary completed in {duration:.1f} seconds")
            
        except Exception as e:
            logging.error(f"Manual email summary failed: {e}")
            raise