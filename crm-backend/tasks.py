from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Note, NoteStatus
from config import settings
import time
from transformers import pipeline
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    "crm_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


print("Loading AI model...")
summarizer = None
try:
    summarizer = pipeline(
        "summarization",
        model="sshleifer/distilbart-cnn-12-6",
        device=-1,
        dtype=torch.float32
    )
    print("AI model loaded successfully!")
    logger.info("AI model loaded successfully!")
except Exception as e:
    print(f"Error loading AI model: {e}")
    logger.error(f"Error loading AI model: {e}")
    print("Using fallback summarization (rule-based)")
    summarizer = None


@celery_app.task(bind=True, max_retries=3)
def summarize_note_task(self, note_id: int):
    db = get_db_session()
    try:
        logger.info(f"Starting summarization for note {note_id}")

        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            logger.error(f"Note {note_id} not found")
            return {"status": "error", "message": "Note not found"}

        note.status = NoteStatus.PROCESSING
        db.commit()
        logger.info(f"Note {note_id} status updated to processing")

        time.sleep(1)

        if summarizer is None:
            logger.warning("AI model not loaded, using fallback summarization")

            raw_text = note.raw_text
            words = raw_text.split()
            if len(words) <= 10:
                summary = raw_text
            elif len(words) <= 50:
                summary = " ".join(words[:10]) + "..."
            else:
                summary = " ".join(words[:20]) + "... " + " ".join(words[-10:])
        else:
            try:
                raw_text = note.raw_text

                if len(raw_text) > 1000:
                    raw_text = raw_text[:1000]
                    logger.info(f"Text truncated to 1000 characters for note {note_id}")

                logger.info(f"Generating AI summary for note {note_id}")
                max_len, min_len = get_summary_lengths(raw_text)
                summary_result = summarizer(
                    raw_text,
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False
                )
                summary = summary_result[0]['summary_text']
                logger.info(f"AI summary generated successfully for note {note_id}")

            except Exception as ai_error:
                logger.error(f"AI model error for note {note_id}: {ai_error}")

                raw_text = note.raw_text
                words = raw_text.split()
                if len(words) <= 10:
                    summary = raw_text
                elif len(words) <= 50:
                    summary = " ".join(words[:10]) + "..."
                else:
                    summary = " ".join(words[:20]) + "... " + " ".join(words[-10:])
                logger.info(f"Using fallback summarization for note {note_id}")

        note.summary = summary
        note.status = NoteStatus.DONE
        db.commit()
        logger.info(f"Note {note_id} completed successfully with summary: {summary[:100]}...")

        return {"status": "success", "summary": summary}

    except Exception as exc:
        logger.error(f"Unexpected error in summarize_note_task for note {note_id}: {exc}")

        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if note:
                note.status = NoteStatus.FAILED
                db.commit()
                logger.info(f"Note {note_id} status updated to failed")
        except Exception as db_error:
            logger.error(f"Error updating note status to failed: {db_error}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for note {note_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))

        logger.error(f"Task failed permanently for note {note_id} after {self.max_retries} retries")
        return {"status": "error", "message": str(exc)}

    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.error(f"Error closing database connection: {close_error}")


@celery_app.task
def health_check():
    return {"status": "healthy", "message": "Celery worker is running"}


def get_summary_lengths(text: str, base_max: int = 50):
    words = text.split()
    length = len(words)

    if length <= 50:
        max_len = max(length // 2, 20)
    elif length <= 200:
        max_len = min(base_max, length // 2)
    else:
        max_len = min(100, length // 2)

    min_len = max(10, max_len // 2)
    return max_len, min_len


def summarize_note_sync(raw_text: str) -> str:
    try:
        if summarizer is None:

            words = raw_text.split()
            if len(words) <= 10:
                return raw_text
            elif len(words) <= 50:
                return " ".join(words[:10]) + "..."
            else:
                return " ".join(words[:20]) + "... " + " ".join(words[-10:])
        else:

            if len(raw_text) > 1000:
                raw_text = raw_text[:1000]

            max_len, min_len = get_summary_lengths(raw_text)
            summary_result = summarizer(
                raw_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            return summary_result[0]['summary_text']
    except Exception as e:
        logger.error(f"Error in sync summarization: {e}")

        words = raw_text.split()
        if len(words) <= 10:
            return raw_text
        elif len(words) <= 50:
            return " ".join(words[:10]) + "..."
        else:
            return " ".join(words[:20]) + "... " + " ".join(words[-10:])


# Test the model loading
if __name__ == "__main__":
    print("Testing model loading...")
    if summarizer:
        test_text = """Customer called today complaining about slow response times on our website.
        They mentioned that the website takes too long to load and they are losing customers
        because of this issue. The customer is a premium client and this is affecting their
        business operations. We need to investigate the server performance and optimize the
        database queries immediately. This is an urgent matter that requires immediate attention
        from our technical team. The customer has been with us for 3 years and this is the
        first time they have complained about performance issues."""
        try:
            result = summarizer(test_text, max_length=120, min_length=40, do_sample=False)
            print(f"Test successful: {result[0]['summary_text']}")
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("Model not loaded, cannot test")
