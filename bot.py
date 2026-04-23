"""
Discord Ticket System Bot
Features:
- /ticket-setup   → Ticket panel gönder
- Buton ile ticket aç
- Her ticket için private kanal
- Ticket kapat / sil / transcript
- Staff role permission sistemi
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
import asyncio
import threading
from web import app as flask_app

# ─── CONFIG ───────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
CONFIG_FILE = "config.json"

# ─── CONFIG YÖNETİMİ ──────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── BOT KURULUMU ─────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── TICKET PANEL VIEW ────────────────────────────────────
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎫 Ticket Aç",
        style=discord.ButtonStyle.primary,
        custom_id="open_ticket"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_open_ticket(interaction)


# ─── TICKET KANAL VIEW ────────────────────────────────────
class TicketChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Ticket'ı Kapat",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_close_ticket(interaction)

    @discord.ui.button(
        label="📋 Transcript Al",
        style=discord.ButtonStyle.secondary,
        custom_id="transcript_ticket"
    )
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_transcript(interaction)


# ─── KAPALIYKEN GÖRÜNEN VIEW ─────────────────────────────
class ClosedTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🗑️ Kanalı Sil",
        style=discord.ButtonStyle.danger,
        custom_id="delete_ticket"
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_delete_ticket(interaction)

    @discord.ui.button(
        label="🔓 Ticket'ı Yeniden Aç",
        style=discord.ButtonStyle.success,
        custom_id="reopen_ticket"
    )
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_reopen_ticket(interaction)


# ─── TICKET HANDLER FONKSİYONLARI ────────────────────────

async def handle_open_ticket(interaction: discord.Interaction):
    guild = interaction.guild
    user = interaction.user
    config = load_config()
    guild_cfg = config.get(str(guild.id), {})

    # Zaten açık ticket var mı?
    existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower().replace(' ', '-')}")
    if existing:
        await interaction.response.send_message(
            f"❌ Zaten açık bir ticket'ın var: {existing.mention}",
            ephemeral=True
        )
        return

    # Ticket kategorisi
    category_id = guild_cfg.get("category_id")
    category = guild.get_channel(int(category_id)) if category_id else None

    # Staff rolü
    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None

    # Kanal izinleri
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            embed_links=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True
        ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_messages=True
        )

    # Kanal oluştur
    channel = await guild.create_text_channel(
        name=f"ticket-{user.name.lower().replace(' ', '-')}",
        overwrites=overwrites,
        category=category,
        topic=f"Ticket sahibi: {user} ({user.id})"
    )

    # Ticket log
    tickets = guild_cfg.get("tickets", {})
    tickets[str(channel.id)] = {
        "owner_id": user.id,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "status": "open"
    }
    guild_cfg["tickets"] = tickets
    config[str(guild.id)] = guild_cfg
    save_config(config)

    # Ticket embed
    embed = discord.Embed(
        title="🎫 Destek Ticket'ı",
        description=(
            f"Merhaba {user.mention}! Destek ekibimiz en kısa sürede seninle ilgilenecek.\n\n"
            f"**Lütfen sorununu detaylıca açıkla.**\n\n"
            f"Ticket'ı kapatmak için aşağıdaki butonu kullanabilirsin."
        ),
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Ticket No: {channel.id}")
    embed.set_thumbnail(url=user.display_avatar.url)

    mention_text = f"{user.mention}"
    if staff_role:
        mention_text += f" | {staff_role.mention}"

    await channel.send(content=mention_text, embed=embed, view=TicketChannelView())

    # Log kanalına bildir
    log_channel_id = guild_cfg.get("log_channel_id")
    if log_channel_id:
        log_channel = guild.get_channel(int(log_channel_id))
        if log_channel:
            log_embed = discord.Embed(
                title="📂 Yeni Ticket Açıldı",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            log_embed.add_field(name="Kullanıcı", value=f"{user} ({user.id})", inline=True)
            log_embed.add_field(name="Kanal", value=channel.mention, inline=True)
            await log_channel.send(embed=log_embed)

    await interaction.response.send_message(
        f"✅ Ticket'ın açıldı: {channel.mention}",
        ephemeral=True
    )


async def handle_close_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    guild = interaction.guild
    config = load_config()
    guild_cfg = config.get(str(guild.id), {})
    tickets = guild_cfg.get("tickets", {})
    ticket_data = tickets.get(str(channel.id))

    if not ticket_data:
        await interaction.response.send_message("❌ Bu bir ticket kanalı değil!", ephemeral=True)
        return

    # Sadece ticket sahibi veya staff kapatabilir
    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None
    is_staff = staff_role and staff_role in interaction.user.roles
    is_owner = ticket_data["owner_id"] == interaction.user.id
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_staff or is_owner or is_admin):
        await interaction.response.send_message("❌ Bu ticket'ı kapatma yetkin yok!", ephemeral=True)
        return

    await interaction.response.defer()

    # Ticket sahibinin yazma iznini kaldır
    owner = guild.get_member(ticket_data["owner_id"])
    if owner:
        await channel.set_permissions(owner, view_channel=True, send_messages=False)

    # Durum güncelle
    tickets[str(channel.id)]["status"] = "closed"
    tickets[str(channel.id)]["closed_by"] = str(interaction.user.id)
    tickets[str(channel.id)]["closed_at"] = datetime.datetime.utcnow().isoformat()
    guild_cfg["tickets"] = tickets
    config[str(guild.id)] = guild_cfg
    save_config(config)

    # Kanal ismini güncelle
    await channel.edit(name=f"closed-{channel.name.replace('ticket-', '')}")

    embed = discord.Embed(
        title="🔒 Ticket Kapatıldı",
        description=f"Bu ticket **{interaction.user.mention}** tarafından kapatıldı.",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    await channel.send(embed=embed, view=ClosedTicketView())

    # Log
    log_channel_id = guild_cfg.get("log_channel_id")
    if log_channel_id:
        log_channel = guild.get_channel(int(log_channel_id))
        if log_channel:
            log_embed = discord.Embed(
                title="🔒 Ticket Kapatıldı",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            log_embed.add_field(name="Kanal", value=channel.name, inline=True)
            log_embed.add_field(name="Kapatan", value=f"{interaction.user}", inline=True)
            await log_channel.send(embed=log_embed)


async def handle_transcript(interaction: discord.Interaction):
    channel = interaction.channel
    await interaction.response.defer(ephemeral=True)

    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        timestamp = msg.created_at.strftime("%d.%m.%Y %H:%M:%S")
        content = msg.content or "[Embed/Attachment]"
        messages.append(f"[{timestamp}] {msg.author} : {content}")

    transcript_text = "\n".join(messages)
    filename = f"transcript-{channel.name}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"

    import io
    file = discord.File(io.BytesIO(transcript_text.encode("utf-8")), filename=filename)

    await interaction.followup.send(
        content=f"📋 **Transcript hazır!** `{channel.name}`",
        file=file,
        ephemeral=True
    )

    # Log kanalına da gönder
    config = load_config()
    guild_cfg = config.get(str(channel.guild.id), {})
    log_channel_id = guild_cfg.get("log_channel_id")
    if log_channel_id:
        log_channel = channel.guild.get_channel(int(log_channel_id))
        if log_channel:
            file2 = discord.File(io.BytesIO(transcript_text.encode("utf-8")), filename=filename)
            log_embed = discord.Embed(
                title="📋 Transcript Oluşturuldu",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            log_embed.add_field(name="Kanal", value=channel.name, inline=True)
            log_embed.add_field(name="İsteyen", value=str(interaction.user), inline=True)
            await log_channel.send(embed=log_embed, file=file2)


async def handle_delete_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    guild = interaction.guild
    config = load_config()
    guild_cfg = config.get(str(guild.id), {})

    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None
    is_staff = staff_role and staff_role in interaction.user.roles
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_staff or is_admin):
        await interaction.response.send_message("❌ Sadece staff kanalı silebilir!", ephemeral=True)
        return

    await interaction.response.send_message("🗑️ Kanal 5 saniye içinde siliniyor...", ephemeral=True)
    await asyncio.sleep(5)

    # Config'den kaldır
    tickets = guild_cfg.get("tickets", {})
    tickets.pop(str(channel.id), None)
    guild_cfg["tickets"] = tickets
    config[str(guild.id)] = guild_cfg
    save_config(config)

    await channel.delete(reason=f"Ticket silindi: {interaction.user}")


async def handle_reopen_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    guild = interaction.guild
    config = load_config()
    guild_cfg = config.get(str(guild.id), {})
    tickets = guild_cfg.get("tickets", {})
    ticket_data = tickets.get(str(channel.id))

    if not ticket_data:
        await interaction.response.send_message("❌ Bu bir ticket kanalı değil!", ephemeral=True)
        return

    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None
    is_staff = staff_role and staff_role in interaction.user.roles
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_staff or is_admin):
        await interaction.response.send_message("❌ Sadece staff ticket'ı yeniden açabilir!", ephemeral=True)
        return

    owner = guild.get_member(ticket_data["owner_id"])
    if owner:
        await channel.set_permissions(owner, view_channel=True, send_messages=True)

    new_name = channel.name.replace("closed-", "ticket-")
    await channel.edit(name=new_name)

    tickets[str(channel.id)]["status"] = "open"
    guild_cfg["tickets"] = tickets
    config[str(guild.id)] = guild_cfg
    save_config(config)

    embed = discord.Embed(
        title="🔓 Ticket Yeniden Açıldı",
        description=f"Bu ticket **{interaction.user.mention}** tarafından yeniden açıldı.",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    await channel.send(embed=embed, view=TicketChannelView())
    await interaction.response.send_message("✅ Ticket yeniden açıldı!", ephemeral=True)


# ─── SLASH KOMUTLARI ──────────────────────────────────────

@tree.command(name="ticket-setup", description="Ticket panelini kur (Admin)")
@app_commands.describe(
    channel="Panelin gönderileceği kanal",
    staff_role="Staff rolü",
    category="Ticket kanallarının açılacağı kategori",
    log_channel="Log kanalı"
)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    staff_role: discord.Role,
    category: discord.CategoryChannel,
    log_channel: discord.TextChannel = None
):
    config = load_config()
    guild_cfg = config.get(str(interaction.guild.id), {})
    guild_cfg["staff_role_id"] = str(staff_role.id)
    guild_cfg["category_id"] = str(category.id)
    if log_channel:
        guild_cfg["log_channel_id"] = str(log_channel.id)
    config[str(interaction.guild.id)] = guild_cfg
    save_config(config)

    embed = discord.Embed(
        title="🎫 Destek Merkezi",
        description=(
            "Sunucumuzda bir sorun mu yaşıyorsun veya yardıma mı ihtiyacın var?\n\n"
            "Aşağıdaki butona tıklayarak özel bir destek kanalı açabilirsin.\n"
            "Ekibimiz en kısa sürede seninle ilgilenecek! 💪"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Sadece gerekli olduğunda ticket aç.")
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    await channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message(
        f"✅ Ticket paneli {channel.mention} kanalına gönderildi!\n"
        f"Staff: {staff_role.mention} | Kategori: {category.name}"
        + (f" | Log: {log_channel.mention}" if log_channel else ""),
        ephemeral=True
    )


@tree.command(name="ticket-add", description="Ticket kanalına kullanıcı ekle")
@app_commands.describe(user="Eklenecek kullanıcı")
async def ticket_add(interaction: discord.Interaction, user: discord.Member):
    config = load_config()
    guild_cfg = config.get(str(interaction.guild.id), {})
    tickets = guild_cfg.get("tickets", {})

    if str(interaction.channel.id) not in tickets:
        await interaction.response.send_message("❌ Bu bir ticket kanalı değil!", ephemeral=True)
        return

    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
    is_staff = staff_role and staff_role in interaction.user.roles
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_staff or is_admin):
        await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        return

    await interaction.channel.set_permissions(user, view_channel=True, send_messages=True)
    await interaction.response.send_message(f"✅ {user.mention} bu ticket'a eklendi.")


@tree.command(name="ticket-remove", description="Ticket kanalından kullanıcı çıkar")
@app_commands.describe(user="Çıkarılacak kullanıcı")
async def ticket_remove(interaction: discord.Interaction, user: discord.Member):
    config = load_config()
    guild_cfg = config.get(str(interaction.guild.id), {})
    tickets = guild_cfg.get("tickets", {})

    if str(interaction.channel.id) not in tickets:
        await interaction.response.send_message("❌ Bu bir ticket kanalı değil!", ephemeral=True)
        return

    staff_role_id = guild_cfg.get("staff_role_id")
    staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
    is_staff = staff_role and staff_role in interaction.user.roles
    is_admin = interaction.user.guild_permissions.administrator

    if not (is_staff or is_admin):
        await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        return

    await interaction.channel.set_permissions(user, overwrite=None)
    await interaction.response.send_message(f"✅ {user.mention} bu ticket'tan çıkarıldı.")


@tree.command(name="ticket-list", description="Açık ticketları listele (Staff)")
async def ticket_list(interaction: discord.Interaction):
    config = load_config()
    guild_cfg = config.get(str(interaction.guild.id), {})
    tickets = guild_cfg.get("tickets", {})

    open_tickets = {k: v for k, v in tickets.items() if v.get("status") == "open"}

    if not open_tickets:
        await interaction.response.send_message("📭 Şu an açık ticket yok.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🎫 Açık Ticketlar ({len(open_tickets)})",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )

    for ch_id, data in list(open_tickets.items())[:10]:
        ch = interaction.guild.get_channel(int(ch_id))
        owner = interaction.guild.get_member(data["owner_id"])
        ch_name = ch.mention if ch else f"#{ch_id}"
        owner_name = str(owner) if owner else f"ID: {data['owner_id']}"
        embed.add_field(name=ch_name, value=f"Sahip: {owner_name}", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── BOT OLAYLARI ─────────────────────────────────────────

@bot.event
async def on_ready():
    # Persistent view'ları yeniden kaydet
    bot.add_view(TicketPanelView())
    bot.add_view(TicketChannelView())
    bot.add_view(ClosedTicketView())

    await tree.sync()
    print(f"✅ Bot hazır: {bot.user} ({bot.user.id})")
    print("📋 Komutlar senkronize edildi.")
    print(f"🌐 {len(bot.guilds)} sunucuda aktif")


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkin yok!", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Hata: {error}", ephemeral=True)


# ─── BAŞLAT ───────────────────────────────────────────────
def run_flask():
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  DISCORD_TOKEN ortam değişkenini ayarla!")
        print("   Örnek: DISCORD_TOKEN=token python3 bot.py")
    else:
        # Flask web sunucusunu ayrı thread'de başlat
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print(f"🌐 Web dashboard başlatıldı → http://localhost:{os.getenv('PORT', 5000)}")
        bot.run(TOKEN)
