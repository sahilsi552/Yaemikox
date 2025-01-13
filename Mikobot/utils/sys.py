import time
import psutil

# Define the bot's boot time
_boot_ = time.time()

def get_readable_time(seconds: int) -> str:
    """Convert seconds to a more readable time format (days, hours, minutes)."""
    count = 0
    time_list = []
    time_suffix_list = ["s", "m", "h", "d"]

    while count < 4:
        remainder, result = divmod(seconds, 60) if count < 2 else divmod(seconds, 24)
        if result or count > 1:
            time_list.append(f"{int(result)}{time_suffix_list[count]}")
        seconds = remainder
        count += 1

    return ", ".join(reversed(time_list))

# Usage example
async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    UP = f"{get_readable_time(bot_uptime)}"
    CPU = f"{psutil.cpu_percent(interval=0.5)}%"
    RAM = f"{psutil.virtual_memory().percent}%"
    DISK = f"{psutil.disk_usage('/').percent}%"
    return UP, CPU, RAM, DISK
