from typing import Any

class BaseFormatter():
    def format(self, value:Any):
        return value
    
class DateTimeFormatterFromMiliseconds(BaseFormatter):
    def format(self, value: Any):
        """Format seconds as dd:hh:mm:ss (days not zero-padded)."""
        if value is None:
            return None
        try:
            seconds = int(value)
        except (TypeError, ValueError):
            return None
        if seconds < 0:
            seconds = 0

        seconds = seconds//100
        days, rem = divmod(seconds, 24 * 3600)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        return f"{days}:{hours:02d}:{minutes:02d}:{secs:02d}"