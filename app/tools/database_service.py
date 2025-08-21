import boto3
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
from botocore.exceptions import ClientError
import bcrypt
import secrets

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, region_name='us-east-1'):
        """Initialize DynamoDB connection"""
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.users_table = self.dynamodb.Table('MemoirAI-Users')
        self.journal_table = self.dynamodb.Table('MemoirAI-JournalEntries')
        
    # ==================================================================================
    # USER OPERATIONS
    # ==================================================================================
    
    def create_user(self, email: str, preferences: Dict = None) -> str:
        """Create a new user and return user_id"""
        try:
            user_id = f"user_{str(uuid.uuid4())[:8]}"
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            user_item = {
                'user_id': user_id,
                'email': email,
                'created_at': timestamp,
                'last_login': timestamp,
                'preferences': preferences or {
                    'default_tone': 'heartwarming',
                    'privacy_settings': 'private',
                    'notification_enabled': True
                },
                'subscription_status': 'free',
                'total_entries': 0
            }
            
            self.users_table.put_item(Item=user_item)
            logger.info(f"Created user: {user_id}")
            return user_id
            
        except ClientError as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email using GSI"""
        try:
            response = self.users_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET last_login = :timestamp',
                ExpressionAttributeValues={':timestamp': timestamp}
            )
        except ClientError as e:
            logger.error(f"Error updating last login for {user_id}: {e}")
    
    def create_user_with_password(self, email: str, password: str, preferences: Dict = None) -> str:
        """Create a new user with hashed password"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            user_id = f"user_{str(uuid.uuid4())[:8]}"
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user_item = {
                'user_id': user_id,
                'email': email,
                'password_hash': password_hash,
                'created_at': timestamp,
                'last_login': timestamp,
                'preferences': preferences or {
                    'default_tone': 'heartwarming',
                    'privacy_settings': 'private',
                    'notification_enabled': True
                },
                'subscription_status': 'free',
                'total_entries': 0,
                'is_active': True
            }
            
            self.users_table.put_item(Item=user_item)
            logger.info(f"Created user with password: {user_id}")
            return user_id
            
        except ClientError as e:
            logger.error(f"Error creating user with password: {e}")
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        try:
            user = self.get_user_by_email(email)
            if not user:
                return None
            
            # Check if account is active
            if not user.get('is_active', True):
                return None
            
            # Verify password
            stored_hash = user.get('password_hash', '')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # Update last login
                self.update_user_last_login(user['user_id'])
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET password_hash = :hash, updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':hash': password_hash,
                    ':timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating password: {e}")
            return False

    # ==================================================================================
    # JOURNAL ENTRY OPERATIONS
    # ==================================================================================
    
    def save_journal_entry(self, user_id: str, title: str, story_content: str, 
                      user_context: str = "", tone: str = "heartwarming",
                      images: List[Dict] = None, sentiment_analysis: Dict = None) -> str:
        """Save a complete journal entry with URL-friendly ID"""
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            entry_uuid = str(uuid.uuid4())[:8]
            
            # NEW: URL-friendly entry ID format
            # Instead of: ENTRY#2025-08-20T23:24:55.123456Z#abc12345
            # Use: ENTRY_2025-08-20T23-24-55-123456Z_abc12345
            timestamp_clean = timestamp.replace(':', '-').replace('.', '-')
            entry_id = f"ENTRY_{timestamp_clean}_{entry_uuid}"
            
            logger.info(f"Creating entry with URL-friendly ID: {entry_id}")
            
            # Calculate word count
            word_count = len(story_content.split())
            estimated_read_time = f"{max(1, word_count // 200)} min"
            
            entry_item = {
                'user_id': user_id,
                'entry_id': entry_id,
                'created_at': timestamp,
                'updated_at': timestamp,
                'title': title,
                'story_content': story_content,
                'user_context': user_context,
                'tone': tone,
                'images': images or [],
                'sentiment_analysis': sentiment_analysis or {},
                'primary_mood': sentiment_analysis.get('primary_mood', 'neutral') if sentiment_analysis else 'neutral',
                'word_count': word_count,
                'estimated_read_time': estimated_read_time,
                'is_favorite': False,
                'privacy_level': 'private',
                'tags': []
            }
            
            # Save the entry
            self.journal_table.put_item(Item=entry_item)
            
            # Update user's total entry count
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='ADD total_entries :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            logger.info(f"Saved journal entry: {entry_id} for user: {user_id}")
            return entry_id

        except ClientError as e:
            logger.error(f"Error saving journal entry: {e}")
            raise

    
    def get_user_entries(self, user_id: str, limit: int = 20, newest_first: bool = True) -> List[Dict]:
        """Get user's journal entries (newest first by default)"""
        try:
            response = self.journal_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=not newest_first,  # False = descending (newest first)
                Limit=limit
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting entries for user {user_id}: {e}")
            return []
    
    def get_entry_by_id(self, user_id: str, entry_id: str) -> Optional[Dict]:
        """Get specific journal entry with better error handling"""
        try:
            logger.info(f"Getting entry {entry_id} for user {user_id}")
            
            response = self.journal_table.get_item(
                Key={'user_id': user_id, 'entry_id': entry_id}
            )
            
            entry = response.get('Item')
            if entry:
                logger.info(f"Found entry {entry_id}")
                return entry
            else:
                logger.warning(f"Entry {entry_id} not found for user {user_id}")
                return None
                
        except ClientError as e:
            logger.error(f"Error getting entry {entry_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting entry {entry_id}: {e}")
            return None

    
    def get_entries_by_date_range(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get entries within a date range using DateIndex"""
        try:
            response = self.journal_table.query(
                IndexName='DateIndex',
                KeyConditionExpression='user_id = :user_id AND created_at BETWEEN :start_date AND :end_date',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':start_date': start_date,
                    ':end_date': end_date
                }
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting entries by date range: {e}")
            return []
    
    def get_favorite_entries(self, user_id: str, limit: int = 20, newest_first: bool = True) -> List[Dict]:
        """
        Get user's favorite journal entries only
        Uses a filter expression to get only entries where is_favorite = true
        """
        try:
            logger.info(f"Getting favorite entries for user {user_id}, limit: {limit}")
            
            # Query all entries for the user, then filter for favorites
            response = self.journal_table.query(
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='is_favorite = :is_favorite',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':is_favorite': True
                },
                ScanIndexForward=not newest_first,  # False = descending (newest first)
                Limit=limit * 2  # Get more since we're filtering, then limit later
            )
            
            entries = response.get('Items', [])
            
            # Sort by created_at if needed (since FilterExpression can affect order)
            if newest_first:
                entries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            else:
                entries.sort(key=lambda x: x.get('created_at', ''))
            
            # Apply final limit
            favorite_entries = entries[:limit]
            
            logger.info(f"Found {len(favorite_entries)} favorite entries for user {user_id}")
            return favorite_entries
            
        except ClientError as e:
            logger.error(f"Error getting favorite entries for user {user_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting favorite entries: {e}")
            return []

    def get_entries_by_mood(self, user_id: str, mood: str, limit: int = 20) -> List[Dict]:
        """
        Get entries filtered by specific mood
        Bonus function - might be useful for iOS app too!
        """
        try:
            logger.info(f"Getting entries with mood '{mood}' for user {user_id}")
            
            # Use the existing MoodIndex if it exists, otherwise filter
            try:
                # Try using the MoodIndex first (more efficient)
                response = self.journal_table.query(
                    IndexName='MoodIndex',
                    KeyConditionExpression='user_id = :user_id AND primary_mood = :mood',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':mood': mood
                    },
                    Limit=limit,
                    ScanIndexForward=False  # Newest first
                )
                entries = response.get('Items', [])
                
            except ClientError:
                # Fallback: Query all entries and filter by mood
                logger.info("MoodIndex not available, using filter expression")
                response = self.journal_table.query(
                    KeyConditionExpression='user_id = :user_id',
                    FilterExpression='primary_mood = :mood',
                    ExpressionAttributeValues={
                        ':user_id': user_id,
                        ':mood': mood
                    },
                    Limit=limit * 2,
                    ScanIndexForward=False
                )
                entries = response.get('Items', [])[:limit]
            
            logger.info(f"Found {len(entries)} entries with mood '{mood}' for user {user_id}")
            return entries
            
        except ClientError as e:
            logger.error(f"Error getting entries by mood {mood}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting entries by mood: {e}")
            return []

    
    def update_entry_favorite(self, user_id: str, entry_id: str, is_favorite: bool) -> bool:
        """
        Mark/unmark entry as favorite with proper validation
        Returns True if updated, False if entry not found
        """
        try:
            logger.info(f"Updating favorite status for entry {entry_id} to {is_favorite}")
            
            # First check if entry exists
            existing_entry = self.get_entry_by_id(user_id, entry_id)
            if not existing_entry:
                logger.warning(f"Cannot update favorite - entry {entry_id} not found for user {user_id}")
                return False
            
            # Update the favorite status
            self.journal_table.update_item(
                Key={'user_id': user_id, 'entry_id': entry_id},
                UpdateExpression='SET is_favorite = :fav, updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':fav': is_favorite,
                    ':timestamp': datetime.utcnow().isoformat() + 'Z'
                },
                # Ensure entry still exists when we update
                ConditionExpression='attribute_exists(entry_id)'
            )
            
            logger.info(f"Successfully updated favorite status for entry {entry_id}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Entry {entry_id} no longer exists")
                return False
            else:
                logger.error(f"Error updating favorite status: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error updating favorite status: {e}")
            raise

    
    def delete_entry(self, user_id: str, entry_id: str) -> bool:
        """
        Delete a journal entry with proper validation
        Returns True if deleted, False if not found
        """
        try:
            logger.info(f"Attempting to delete entry {entry_id} for user {user_id}")
            
            # First, check if the entry exists
            existing_entry = self.get_entry_by_id(user_id, entry_id)
            if not existing_entry:
                logger.warning(f"Cannot delete - entry {entry_id} not found for user {user_id}")
                return False
            
            # Entry exists, now delete it
            self.journal_table.delete_item(
                Key={'user_id': user_id, 'entry_id': entry_id},
                # Add condition to ensure we only delete if it still exists
                ConditionExpression='attribute_exists(entry_id)'
            )
            
            logger.info(f"Successfully deleted entry {entry_id} from journal table")
            
            # Only decrement counter if deletion was successful
            try:
                self.users_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression='ADD total_entries :dec',
                    ConditionExpression='total_entries > :zero',
                    ExpressionAttributeValues={
                        ':dec': -1,
                        ':zero': 0
                    }
                )
                logger.info(f"Decremented entry count for user {user_id}")
            except ClientError as count_error:
                # If count update fails, log but don't fail the whole operation
                logger.warning(f"Could not update entry count for user {user_id}: {count_error}")
            
            logger.info(f"Successfully deleted entry {entry_id} for user {user_id}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Entry {entry_id} was already deleted or doesn't exist")
                return False
            else:
                logger.error(f"DynamoDB error deleting entry {entry_id}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error deleting entry {entry_id}: {e}")
            raise
    
    # ==================================================================================
    # ANALYTICS & INSIGHTS
    # ==================================================================================
    
    def get_mood_distribution(self, user_id: str, days: int = 30) -> Dict[str, int]:
        """Get mood distribution over the last N days"""
        try:
            # Calculate date range
            from datetime import timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            start_str = start_date.isoformat() + 'Z'
            end_str = end_date.isoformat() + 'Z'
            
            entries = self.get_entries_by_date_range(user_id, start_str, end_str)
            
            mood_counts = {}
            for entry in entries:
                mood = entry.get('primary_mood', 'neutral')
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            
            return mood_counts
        except Exception as e:
            logger.error(f"Error calculating mood distribution: {e}")
            return {}
    
    def get_user_stats(self, user_id: str) -> Dict:

        """Get comprehensive user statistics"""
        try:
            user = self.get_user(user_id)
            if not user:
                return {}
            
            # Get recent entries for analysis
            recent_entries = self.get_user_entries(user_id, limit=100)
            
            if not recent_entries:
                return {
                    'total_entries': user.get('total_entries', 0),
                    'mood_distribution': {},
                    'avg_word_count': 0,
                    'writing_streak': 0
                }
            
            # Calculate stats
            total_words = sum(entry.get('word_count', 0) for entry in recent_entries)
            avg_word_count = total_words // len(recent_entries) if recent_entries else 0
            
            mood_dist = {}
            for entry in recent_entries:
                mood = entry.get('primary_mood', 'neutral')
                mood_dist[mood] = mood_dist.get(mood, 0) + 1
            
            return {
                'total_entries': user.get('total_entries', 0),
                'mood_distribution': mood_dist,
                'avg_word_count': avg_word_count,
                'recent_entries_count': len(recent_entries),
                'most_common_mood': max(mood_dist.items(), key=lambda x: x[1])[0] if mood_dist else 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Error calculating user stats: {e}")
            return {}