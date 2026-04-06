<p align="center">
  <img src="angel_gothic_FOR_GITHUB.webp" width="100%" alt="ErosLab Gothic Angel">
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=monospace&size=20&pause=2000&color=FF2244&center=true&width=600&lines=ErosLab+Bot+Ecosystem+%F0%9F%94%9E;Serverless+24%2F7+on+GitHub+Actions;AI+via+Groq+%26+Llama+3;Smart+filtering+%26+no+duplicates;Free+hosting+%E2%80%A2+Full+autonomy">
</p>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/Haillord/eroslab-bot?style=for-the-badge&color=red" alt="license">
  <img src="https://img.shields.io/github/stars/Haillord/eroslab-bot?style=for-the-badge&color=red" alt="stars">
  <img src="https://img.shields.io/github/actions/workflow/status/Haillord/eroslab-bot/bot.yml?style=for-the-badge&label=Bot%20Status" alt="workflow">
</p>

<p align="center">
  <img src="banner.svg?v=5" width="100%" alt="ErosLab Bot Ecosystem">
</p>

<p align="center">
  <a href="https://t.me/eroslabai"><strong>🔞 Основной канал</strong></a>
  •
  <a href="https://t.me/eroslabwallpaper"><strong>🤍 Обои</strong></a>
</p>

---

<!-- FEATURES -->
<table>
<tr>
<td width="50%">

**`Serverless 24/7`**
Полная автоматизация на GitHub Actions без затрат на сервер

</td>
<td width="50%">

**`Gist Database`**
Хранение состояния в скрытых Gists — никаких лишних коммитов

</td>
</tr>
<tr>
<td>

**`Smart Filtering`**
Защита от дублей по хешу, контроль качества и разрешения

</td>
<td>

**`AI Engine`**
Генерация подписей через Groq и OpenRouter (Llama 3 / Vision)

</td>
</tr>
<tr>
<td colspan="2">

**`Media Lab`**
Наложение водяных знаков и оптимизация видео через FFmpeg на лету

</td>
</tr>
</table>

---

### 🛠 Stack

`Python 3.11` · `GitHub Actions` · `Gist API` · `CivitAI` · `Rule34` · `Groq` · `OpenRouter` · `FFmpeg` · `yt-dlp`

---

### 📂 Structure
```text
▸ civitai_bot.py      // основной движок (nsfw)
▸ wallpapers_bot.py   // бот с обоями (sfw)
▸ gist_storage.py     // логика работы с БД Gist
▸ caption_gen.py      // ai-генератор описаний
▸ watermark.py        // обработка фото и видео
```

---

### 🔑 Secrets

> `Settings` → `Secrets and variables` → `Actions`

| Secret | |
|:---|:---|
| `TELEGRAM_BOT_TOKEN` | Токен основного бота |
| `GH_TOKEN` | Classic Token с правами на Gist |
| `GIST_ID` | ID вашего секретного Gist |
| `CIVITAI_API_KEY` | Доступ к API CivitAI |
| `GROQ_API_KEY` | Ключ для AI генерации подписей |

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Python-3776AB?style=for-the-badge&logo=python" alt="python">
  <img src="https://img.shields.io/badge/Powered%20by-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions" alt="actions">
  <img src="https://img.shields.io/badge/Developer-Haillord-red?style=for-the-badge&logo=telegram" alt="author">
</p>