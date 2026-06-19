import discord
from discord.ext import commands, tasks
import requests
import json
import os
from datetime import datetime, timedelta

# --- Configuration ---
TOKEN = os.getenv("DISCORD_TOKEN")
WEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
LAT = float(os.getenv("LAT")
LON = float(os.getenv("LON")
STATE_FILE = "/app/state.json"

# --- State Management ---
def get_state():
    if not os.path.exists(STATE_FILE):
        return {"covered": False, "snooze_until": None, "covered_at": None}
    with open(STATE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"covered": False, "snooze_until": None, "covered_at": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def ensure_state_file_exists():
    """Creates the state file with default values on startup if missing."""
    if not os.path.exists(STATE_FILE):
        print(f"Creating missing state file at {STATE_FILE}...")
        default_state = {"covered": False, "snooze_until": None, "covered_at": None}
        save_state(default_state)

# --- Weather Logic ---
def check_rain_forecast():
    """
    Checks the next 12 hours (4 increments of 3 hours).
    Returns (True, "Condition") if rain >= 3mm is expected, else (False, None).
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={WEATHER_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        forecasts = data['list'][:4]
        
        for entry in forecasts:
            rain_volume = entry.get('rain', {}).get('3h', 0)
            
            if rain_volume >= 3.0:
                condition = entry['weather'][0]['main']
                return True, condition
                
    except Exception as e:
        print(f"Error fetching weather: {e}")
        
    return False, None

# --- UI Button Controls ---
class WeatherControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mark Covered", style=discord.ButtonStyle.success, custom_id="btn_covered")
    async def covered_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_state()
        state["covered"] = True
        state["covered_at"] = datetime.now().isoformat()
        state["snooze_until"] = None
        save_state(state)
        await interaction.response.send_message("✅ Item marked as covered. Will automatically resume monitoring in 24 hours.", ephemeral=False)

    @discord.ui.button(label="Snooze (3h)", style=discord.ButtonStyle.primary, custom_id="btn_snooze")
    async def snooze_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_state()
        snooze_time = datetime.now() + timedelta(hours=3)
        state["snooze_until"] = snooze_time.isoformat()
        save_state(state)
        await interaction.response.send_message(f"🔕 Alerts snoozed for 3 hours (until {snooze_time.strftime('%I:%M %p')}).", ephemeral=False)

# --- Bot Setup ---
class WeatherBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(WeatherControls())

bot = WeatherBot()

# --- Background Tasks ---
@tasks.loop(minutes=30)
async def weather_check_task():
    state = get_state()
    
    # --- Auto-Uncover Logic (24 Hour Reset) ---
    if state.get("covered") and state.get("covered_at"):
        covered_time = datetime.fromisoformat(state["covered_at"])
        if datetime.now() - covered_time >= timedelta(hours=24):
            state["covered"] = False
            state["covered_at"] = None
            save_state(state)
            print("24 hours passed. Item automatically marked as uncovered.")
            
    # --- Snooze Logic ---
    is_snoozed = False
    if state.get("snooze_until"):
        snooze_time = datetime.fromisoformat(state["snooze_until"])
        if datetime.now() < snooze_time:
            is_snoozed = True
        else:
            state["snooze_until"] = None
            save_state(state)

    # --- Weather Check ---
    should_notify, condition = check_rain_forecast()

    if should_notify and not state["covered"] and not is_snoozed:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                f"⚠️ **Weather Alert!**\n"
                f"Expected condition: **{condition}** (>= 1mm/hr).\n"
                f"Please cover the item! Use the buttons below to update status.",
                view=WeatherControls()
            )

@weather_check_task.before_loop
async def before_weather_check():
    await bot.wait_until_ready()

# --- Bot Events & Commands ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    ensure_state_file_exists()
    
    if not weather_check_task.is_running():
        weather_check_task.start()
        print("Weather check task started.")

@bot.command()
async def panel(ctx):
    """Spawns the control panel buttons manually."""
    await ctx.send("🎛️ **Weather Control Panel**", view=WeatherControls())

# Keeping the text commands as fallbacks (Removed !uncovered)
@bot.command()
async def covered(ctx):
    state = get_state()
    state["covered"] = True
    state["covered_at"] = datetime.now().isoformat()
    state["snooze_until"] = None
    save_state(state)
    await ctx.send("✅ Item marked as covered. Will automatically resume monitoring in 24 hours.")

@bot.command()
async def snooze(ctx, hours: int = 3):
    state = get_state()
    snooze_time = datetime.now() + timedelta(hours=hours)
    state["snooze_until"] = snooze_time.isoformat()
    save_state(state)
    await ctx.send(f"🔕 Alerts snoozed for {hours} hours (until {snooze_time.strftime('%I:%M %p')}).")

# --- Run Bot ---
if __name__ == "__main__":
    if TOKEN and WEATHER_KEY and CHANNEL_ID != 0:
        bot.run(TOKEN)
    else:
        print("CRITICAL ERROR: Missing DISCORD_TOKEN, OPENWEATHER_API_KEY, or CHANNEL_ID in environment variables.")
