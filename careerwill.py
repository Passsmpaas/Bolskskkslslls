import os
import requests
import threading
import asyncio
import time
from pyromod import listen
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message
from config import CHANNEL_ID, CHANNEL_ID2, THUMB_URL, BOT_TEXT

requests = requests.Session()

# Download thumbnail
def download_thumbnail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            thumb_path = "thumb_temp.jpg"
            with open(thumb_path, "wb") as f:
                f.write(response.content)
            return thumb_path
        return None
    except Exception:
        return None

# -------------------- Downloader Function ---------------------
async def careerdl(app, message, headers, batch_id, token, topic_ids, prog, batch_name):
    num_id = topic_ids.split('&')
    result_text = ""
    total_videos = 0
    total_notes = 0
    total_topics = len(num_id)
    current_topic = 0
    start_time = time.time()

    thumb_path = download_thumbnail(THUMB_URL)

    for id_text in num_id:
        try:
            current_topic += 1
            details_url = f"https://elearn.crwilladmin.com/api/v9/batch-detail/{batch_id}?topicId={id_text}"
            response = requests.get(details_url, headers=headers)
            data = response.json()
            classes = data["data"]["class_list"]["classes"]
            classes.reverse()

            # Get topic name
            topic_url = f"https://elearn.crwilladmin.com/api/v9/batch-topic/{batch_id}?type=class"
            topic_data = requests.get(topic_url, headers=headers).json()["data"]
            topics = topic_data["batch_topic"]
            current_topic_name = next((topic["topicName"] for topic in topics if str(topic["id"]) == id_text), "Unknown Topic")

            # Time metrics
            elapsed_time = time.time() - start_time
            avg_time_per_topic = elapsed_time / current_topic
            remaining_topics = total_topics - current_topic
            eta = avg_time_per_topic * remaining_topics
            elapsed_str = f"{int(elapsed_time//60)}m {int(elapsed_time%60)}s"
            eta_str = f"{int(eta//60)}m {int(eta%60)}s"

            progress_msg = (
                "🔄 <b>Processing Large Batch</b>\n"
                f"├─ Subject: {current_topic}/{total_topics}\n"
                f"├─ Name: <code>{current_topic_name}</code>\n"
                f"├─ Topics: {current_topic}/{total_topics}\n"
                f"├─ Links: {total_videos + total_notes}\n"
                f"├─ Time: {elapsed_str}\n"
                f"└─ ETA: {eta_str}"
            )
            await prog.edit_text(progress_msg)

            for video_data in classes:
                lesson_name = video_data['lessonName']
                lesson_ext = video_data['lessonExt']
                detail_url = f"https://elearn.crwilladmin.com/api/v9/class-detail/{video_data['id']}"
                lesson_url = requests.get(detail_url, headers=headers).json()['data']['class_detail']['lessonUrl']

                # Only CloudFront links
                if lesson_ext == 'cloudfront' or lesson_url.startswith("https://"):
                    video_link = lesson_url
                    total_videos += 1
                    result_text += f"{lesson_name}: {video_link}\n"
                else:
                    continue

            # Notes
            notes_url = f"https://elearn.crwilladmin.com/api/v9/batch-topic/{batch_id}?type=notes"
            notes_resp = requests.get(notes_url, headers=headers).json()
            if 'data' in notes_resp and 'batch_topic' in notes_resp['data']:
                for topic in notes_resp['data']['batch_topic']:
                    topic_id = topic['id']
                    notes_topic_url = f"https://elearn.crwilladmin.com/api/v9/batch-notes/{batch_id}?topicId={topic_id}"
                    notes_data = requests.get(notes_topic_url, headers=headers).json()
                    for note in reversed(notes_data.get('data', {}).get('notesDetails', [])):
                        doc_title = note.get('docTitle', '')
                        doc_url = note.get('docUrl', '').replace(' ', '%20')
                        line = f"{doc_title}: {doc_url}\n"
                        if line not in result_text:
                            result_text += line
                            total_notes += 1

        except Exception as e:
            error_msg = (
                "❌ <b>An error occurred during extraction</b>\n\n"
                f"Error details: <code>{str(e)}</code>\n\n"
                "Please try again or contact support."
            )
            await message.reply(error_msg)

    file_name = f"{batch_name.replace('/', '')}.txt"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(result_text)

    import datetime
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    caption = (
        "🎓 <b>COURSE EXTRACTED</b> 🎓\n\n"
        "📱 <b>APP:</b> CareerWill\n"
        f"📚 <b>BATCH:</b> {batch_name}\n"
        f"📅 <b>DATE:</b> {current_date} IST\n\n"
        "📊 <b>CONTENT STATS</b>\n"
        f"├─ 🎬 Videos: {total_videos}\n"
        f"├─ 📄 PDFs/Notes: {total_notes}\n"
        f"└─ 📦 Total Links: {total_videos + total_notes}\n\n"
        f"🚀 <b>Extracted by:</b> @{(await app.get_me()).username}\n\n"
        f"<code>╾───• {BOT_TEXT} •───╼</code>"
    )

    try:
        await app.send_document(
            message.chat.id,
            document=file_name,
            caption=caption,
            thumb=download_thumbnail(THUMB_URL)
        )
        await app.send_document(
            CHANNEL_ID,
            document=file_name,
            caption=caption,
            thumb=download_thumbnail(THUMB_URL)
        )
    finally:
        await prog.delete()
        os.remove(file_name)
            
