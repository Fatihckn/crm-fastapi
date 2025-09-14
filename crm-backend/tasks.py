import threading
import time
from queue import Queue
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Note, NoteStatus
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

job_queue = Queue()


def get_db_session():
    return SessionLocal()


def rule_based_summary(raw_text: str) -> str:

    if not raw_text or not raw_text.strip():
        return ""

    words = raw_text.split()
    word_count = len(words)

    # Very short text - return as is
    if word_count <= 10:
        return raw_text.strip()

    # Short text - first 10 words with ellipsis
    elif word_count <= 50:
        return " ".join(words[:10]) + "..."

    # Medium text - first 15 words + last 5 words
    elif word_count <= 100:
        return " ".join(words[:15]) + "... " + " ".join(words[-5:])

    # Long text - first 20 words + last 10 words
    else:
        return " ".join(words[:20]) + "... " + " ".join(words[-10:])


def summarize_note_worker():

    while True:
        try:
            note_id = job_queue.get()
            db = get_db_session()
            note = None

            try:
                note = db.query(Note).filter(Note.id == note_id).first()
                if not note:
                    logger.error(f"Note {note_id} not found")
                    continue

                note.status = NoteStatus.PROCESSING
                db.commit()
                logger.info(f"Processing note {note_id}")

                time.sleep(5)

                summary = rule_based_summary(note.raw_text)
                note.summary = summary
                note.status = NoteStatus.DONE
                db.commit()

                logger.info(f"Note {note_id} summarized successfully: {summary[:50]}...")

            except Exception as e:
                logger.error(f"Error processing note {note_id}: {e}")
                if note:
                    note.status = NoteStatus.FAILED
                    db.commit()
            finally:
                db.close()
                job_queue.task_done()

        except Exception as e:
            logger.error(f"Worker thread error: {e}")
            time.sleep(1)


thread = threading.Thread(target=summarize_note_worker, daemon=True)
thread.start()


def enqueue_note_summary(note_id: int):
    try:
        job_queue.put(note_id)
        logger.info(f"Note {note_id} queued for summarization")
    except Exception as e:
        logger.error(f"Failed to queue note {note_id}: {e}")
