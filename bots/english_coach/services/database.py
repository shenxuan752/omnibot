from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
        supabase = None
else:
    print("Warning: Supabase credentials not found. Database disabled.")
    supabase = None

async def save_flashcard(word_data: dict, user_id: int):
    """Save flashcard to Supabase, avoiding duplicates."""
    if not supabase: return {'status': 'error', 'message': 'Database disabled'}
    # Check if word already exists for this user
    existing = supabase.table('flashcards').select('id').eq('user_id', str(user_id)).eq('word', word_data['word']).execute()
    
    if existing.data:
        return {'status': 'skipped', 'message': 'Word already exists'}
    
    data = {
        **word_data,
        'user_id': str(user_id)
    }
    # Remove IPA if present as column doesn't exist
    # if 'ipa' in data:
    #     del data['ipa']
    result = supabase.table('flashcards').insert(data).execute()
    return result.data

async def get_flashcards(user_id: int, limit: int = 20, mode: str = 'recent'):
    """Get user's flashcards. Mode: 'recent' or 'review'."""
    if not supabase: return []
    
    if mode == 'review':
        # Get due cards (next_review_at <= now)
        # Note: Supabase/PostgREST filter for 'lte' (less than or equal)
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        # Try to get due cards first
        try:
            result = supabase.table('flashcards') \
                .select('*') \
                .eq('user_id', str(user_id)) \
                .lte('next_review_at', now) \
                .order('next_review_at', desc=False) \
                .limit(limit) \
                .execute()
            
            # If no due cards, fall back to oldest reviewed cards or just random?
            # For now, if result is empty, maybe fetch some new ones?
            # Let's stick to strict SRS: if nothing due, nothing to review.
            # But user wants "20 random words" if they want to review.
            # Let's fallback to random if empty? 
            # Actually, let's just return what we find. The bot can handle empty list.
            return result.data
        except Exception as e:
            print(f"Error fetching review cards (maybe columns missing): {e}")
            # Fallback to recent if columns missing
            return await get_flashcards(user_id, limit, 'recent')
            
    else:
        # Recent cards
        result = supabase.table('flashcards').select('*').eq('user_id', str(user_id)).order('created_at', desc=True).limit(limit).execute()
        return result.data

async def update_flashcard_progress(card_id: int, success: bool):
    """Update SRS progress for a card."""
    if not supabase: return False
    
    try:
        # Get current level
        current = supabase.table('flashcards').select('review_level').eq('id', card_id).execute()
        if not current.data: return False
        
        level = current.data[0].get('review_level', 0)
        
        from datetime import datetime, timedelta
        
        if success:
            new_level = level + 1
            # Simple interval: 1d, 3d, 7d, 14d, 30d...
            days = [0, 1, 3, 7, 14, 30, 60]
            interval = days[min(new_level, len(days)-1)]
            next_review = (datetime.utcnow() + timedelta(days=interval)).isoformat()
        else:
            new_level = 0 # Reset on fail
            next_review = datetime.utcnow().isoformat() # Review again immediately/soon
            
        supabase.table('flashcards').update({
            'review_level': new_level,
            'next_review_at': next_review
        }).eq('id', card_id).execute()
        return True
    except Exception as e:
        print(f"Error updating flashcard: {e}")
        return False

async def save_journal(entry_data: dict, user_id: int):
    """Save journal entry."""
    if not supabase: return None
    data = {
        **entry_data,
        'user_id': str(user_id)
    }
    result = supabase.table('journal_entries').insert(data).execute()
    return result.data


async def get_random_journal(user_id: int):
    """Get a random journal entry for the user."""
    if not supabase: return None
    result = supabase.table('journal_entries').select('*').eq('user_id', str(user_id)).execute()
    if result.data and len(result.data) > 0:
        import random
        return random.choice(result.data)
    return None

async def save_mission_completion(mission_data: dict, user_id: int):
    """Save completed mission."""
    if not supabase: return None
    data = {
        **mission_data,
        'user_id': str(user_id)
    }
    result = supabase.table('missions').insert(data).execute()
    return result.data

async def save_user(user_id: int):
    """Save user to track active users for schedule restoration."""
    if not supabase: return False
    try:
        # Check if user exists
        existing = supabase.table('english_coach_users').select('user_id').eq('user_id', str(user_id)).execute()
        if not existing.data:
            data = {'user_id': str(user_id)}
            supabase.table('english_coach_users').insert(data).execute()
            print(f"✅ Saved new user: {user_id}")
            return True
    except Exception as e:
        print(f"⚠️ Error saving user (table may not exist): {e}")
    return False

async def get_all_users():
    """Get all active users to restore schedules."""
    if not supabase: return []
    try:
        result = supabase.table('english_coach_users').select('user_id').execute()
        return [int(user['user_id']) for user in result.data] if result.data else []
    except Exception as e:
        print(f"⚠️ Error getting users (table may not exist): {e}")
        # Return empty list if table doesn't exist - bot will still work for new users
        return []
