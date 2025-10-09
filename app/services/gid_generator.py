"""
Global ID (G_ID) Generator Service
Handles the generation of unique G_ID following the format: (A)(N)(YY)(A)(A)(N)(N)
"""

from datetime import datetime
from typing import Optional, List
import logging
from sqlalchemy.orm import Session

try:
    from app.models.models import GIDSequence
except ImportError:
    # Fallback for different import contexts
    try:
        from ..models.models import GIDSequence
    except ImportError:
        from models.models import GIDSequence

logger = logging.getLogger(__name__)


class GIDGenerator:
    """
    Generates Global IDs with the format G{N}{YY}{A}{A}{N}{N}
    Where:
    - G: Always 'G'
    - N: Single digit (0-9)
    - YY: Two-digit year
    - A: Alphabetic characters (A-Z)
    - N: Two-digit number (00-99)
    
    OPTIMIZED for batch processing with minimal database transactions
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._sequence_cache = None
    
    def generate_next_gid(self) -> str:
        """
        Generate the next G_ID following the incremental logic:
        1. Increment NN from 00 to 99
        2. After 99, reset NN to 00 and increment AA (AA -> AB -> ... -> AZ -> BA -> ... -> ZZ)
        3. After ZZ99, increment YY by 1 and reset AA to AA, NN to 00
        4. After 99ZZ99, increment N by 1 and reset YY to current year, AA to AA, NN to 00
        
        If all tables are empty, automatically reset sequence to G25AA00
        """
        try:
            # Check if database is empty and reset sequence if needed
            self._check_and_reset_if_empty()
            
            # Get current sequence
            sequence = self.db.query(GIDSequence).first()
            
            if not sequence:
                # Initialize sequence if not exists (starting from G25AA00)
                current_year = 25  # Start from year 25 (2025)
                sequence = GIDSequence(
                    current_year=current_year,
                    current_digit=0,
                    current_alpha_1='A',
                    current_alpha_2='A',
                    current_number=0
                )
                self.db.add(sequence)
                self.db.commit()
            
            # Generate current G_ID
            gid = self._format_gid(
                sequence.current_digit,  # type: ignore
                sequence.current_year,   # type: ignore
                sequence.current_alpha_1,  # type: ignore
                sequence.current_alpha_2,  # type: ignore
                sequence.current_number  # type: ignore
            )
            
            # Increment sequence for next time
            self._increment_sequence(sequence)
            
            return gid
            
        except Exception as e:
            logger.error(f"Error generating G_ID: {str(e)}")
            self.db.rollback()
            raise
    
    def generate_batch_gids(self, count: int) -> list[str]:
        """
        Generate multiple G_IDs efficiently in batch (OPTIMIZED for speed)
        Reduces database transactions from N to 1 for N G_IDs
        
        If all tables are empty, automatically reset sequence to G25AA00
        """
        try:
            if count <= 0:
                return []
                
            logger.info(f"🚀 Generating {count} G_IDs in batch mode...")
            start_time = datetime.now()
            
            # Check if database is empty and reset sequence if needed
            self._check_and_reset_if_empty()
            
            # Get or initialize sequence once
            sequence = self.db.query(GIDSequence).first()
            if not sequence:
                current_year = 25  # Start from year 25 (2025)
                sequence = GIDSequence(
                    current_year=current_year,
                    current_digit=0,
                    current_alpha_1='A',
                    current_alpha_2='A',
                    current_number=0
                )
                self.db.add(sequence)
                self.db.flush()
            
            # Cache current sequence state (convert to Python types)
            current_digit = int(sequence.current_digit)  # type: ignore
            current_year = int(sequence.current_year)  # type: ignore
            current_alpha_1 = str(sequence.current_alpha_1)  # type: ignore
            current_alpha_2 = str(sequence.current_alpha_2)  # type: ignore
            current_number = int(sequence.current_number)  # type: ignore
            
            # Generate G_IDs in memory without database hits
            gids = []
            for i in range(count):
                # Generate current G_ID
                gid = self._format_gid(current_digit, current_year, current_alpha_1, current_alpha_2, current_number)
                gids.append(gid)
                
                # Increment sequence in memory
                current_number += 1
                if current_number > 99:
                    current_number = 0
                    # Increment alpha
                    if current_alpha_2 == 'Z':
                        if current_alpha_1 == 'Z':
                            current_alpha_1 = 'A'
                            current_alpha_2 = 'A'
                            # Increment year
                            current_year = (current_year + 1) % 100
                            if current_year == 0:
                                current_digit = (current_digit + 1) % 10
                                current_year = int(str(datetime.now().year)[-2:])
                        else:
                            current_alpha_1 = chr(ord(current_alpha_1) + 1)
                            current_alpha_2 = 'A'
                    else:
                        current_alpha_2 = chr(ord(current_alpha_2) + 1)
            
            # Update sequence in database once at the end
            setattr(sequence, 'current_digit', current_digit)
            setattr(sequence, 'current_year', current_year)
            setattr(sequence, 'current_alpha_1', current_alpha_1)
            setattr(sequence, 'current_alpha_2', current_alpha_2)
            setattr(sequence, 'current_number', current_number)
            
            # Single commit for all changes
            self.db.commit()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            if duration > 0:
                logger.info(f"✅ Generated {count} G_IDs in {duration:.3f} seconds ({count/duration:.0f} G_IDs/sec)")
            else:
                logger.info(f"✅ Generated {count} G_IDs in {duration:.3f} seconds (instant)")
            
            return gids
            
        except Exception as e:
            logger.error(f"Error generating batch G_IDs: {str(e)}")
            self.db.rollback()
            raise
    
    def _get_cached_sequence(self) -> GIDSequence:
        """Get sequence with caching to reduce database hits"""
        if self._sequence_cache is None:
            self._sequence_cache = self.db.query(GIDSequence).first()
            if not self._sequence_cache:
                current_year = int(str(datetime.now().year)[-2:])
                self._sequence_cache = GIDSequence(
                    current_year=current_year,
                    current_digit=0,
                    current_alpha_1='A',
                    current_alpha_2='A',
                    current_number=0
                )
                self.db.add(self._sequence_cache)
                self.db.commit()
        return self._sequence_cache
    
    def _format_gid(self, digit: int, year: int, alpha1: str, alpha2: str, number: int) -> str:
        """Format the G_ID string"""
        return f"G{digit}{year:02d}{alpha1}{alpha2}{number:02d}"
    
    def _check_and_reset_if_empty(self) -> None:
        """
        Check if all data tables are empty and reset sequence to G25AA00 if so
        This ensures that when database is cleared, G_ID generation starts fresh
        """
        try:
            try:
                from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai
            except ImportError:
                # Fallback for different import contexts
                try:
                    from ..models.models import GlobalID, GlobalIDNonDatabase, Pegawai
                except ImportError:
                    from models.models import GlobalID, GlobalIDNonDatabase, Pegawai
            
            # Check if all data tables are empty
            global_id_count = self.db.query(GlobalID).count()
            global_id_non_db_count = self.db.query(GlobalIDNonDatabase).count()
            pegawai_count = self.db.query(Pegawai).count()
            
            # If all tables are empty, reset sequence to start from G25AA00
            if global_id_count == 0 and global_id_non_db_count == 0 and pegawai_count == 0:
                logger.info("🔄 All data tables are empty. Resetting G_ID sequence to G25AA00...")
                
                sequence = self.db.query(GIDSequence).first()
                if sequence:
                    # Reset existing sequence
                    sequence.current_year = 25  # type: ignore
                    sequence.current_digit = 0  # type: ignore
                    sequence.current_alpha_1 = 'A'  # type: ignore
                    sequence.current_alpha_2 = 'A'  # type: ignore
                    sequence.current_number = 0  # type: ignore
                    self.db.commit()
                    logger.info("✅ G_ID sequence reset to G025AA00")
                # If no sequence exists, it will be created with default values in generate methods
                
        except Exception as e:
            logger.warning(f"Could not check/reset empty database: {str(e)}")
            # Don't fail G_ID generation if this check fails
            pass
    
    def _increment_sequence(self, sequence: GIDSequence) -> None:
        """Increment the sequence following the specified logic"""
        try:
            # Step 1: Try to increment the number (00-99)
            if sequence.current_number < 99:  # type: ignore
                sequence.current_number += 1  # type: ignore
            else:
                # Step 2: Number reached 99, reset to 00 and increment alpha
                sequence.current_number = 0  # type: ignore
                
                # Try to increment alpha combination
                if not self._increment_alpha(sequence):
                    # Step 3: Alpha reached ZZ, increment year
                    sequence.current_alpha_1 = 'A'  # type: ignore
                    sequence.current_alpha_2 = 'A'  # type: ignore
                    
                    if sequence.current_year < 99:  # type: ignore
                        sequence.current_year += 1  # type: ignore
                    else:
                        # Step 4: Year reached 99, increment digit
                        sequence.current_year = int(str(datetime.now().year)[-2:])  # type: ignore
                        
                        if sequence.current_digit < 9:  # type: ignore
                            sequence.current_digit += 1  # type: ignore
                        else:
                            # Theoretical limit reached (G999ZZ99)
                            raise ValueError("G_ID sequence limit reached: G999ZZ99")
            
            self.db.commit()
            logger.info(f"Sequence updated: {sequence.current_digit}{sequence.current_year:02d}{sequence.current_alpha_1}{sequence.current_alpha_2}{sequence.current_number:02d}")
            
        except Exception as e:
            logger.error(f"Error incrementing sequence: {str(e)}")
            self.db.rollback()
            raise
    
    def _increment_alpha(self, sequence: GIDSequence) -> bool:
        """
        Increment alphabetic combination (AA -> AB -> ... -> AZ -> BA -> ... -> ZZ)
        Returns True if increment was successful, False if limit reached (ZZ)
        """
        # Convert letters to numbers (A=0, B=1, ..., Z=25)
        alpha1_num = ord(sequence.current_alpha_1) - ord('A')  # type: ignore
        alpha2_num = ord(sequence.current_alpha_2) - ord('A')  # type: ignore
        
        # Increment alpha2 first
        if alpha2_num < 25:  # Less than Z
            sequence.current_alpha_2 = chr(ord(sequence.current_alpha_2) + 1)  # type: ignore
            return True
        else:
            # alpha2 is Z, reset to A and increment alpha1
            sequence.current_alpha_2 = 'A'  # type: ignore
            
            if alpha1_num < 25:  # Less than Z
                sequence.current_alpha_1 = chr(ord(sequence.current_alpha_1) + 1)  # type: ignore
                return True
            else:
                # Both are Z, limit reached
                return False
    
    def get_current_sequence_info(self) -> Optional[dict]:
        """Get current sequence information for monitoring"""
        try:
            sequence = self.db.query(GIDSequence).first()
            if sequence:
                return {
                    'current_digit': sequence.current_digit,
                    'current_year': sequence.current_year,
                    'current_alpha_1': sequence.current_alpha_1,
                    'current_alpha_2': sequence.current_alpha_2,
                    'current_number': sequence.current_number,
                    'next_gid_preview': self._format_gid(
                        sequence.current_digit,  # type: ignore
                        sequence.current_year,   # type: ignore
                        sequence.current_alpha_1,  # type: ignore
                        sequence.current_alpha_2,  # type: ignore
                        sequence.current_number  # type: ignore
                    ),
                    'updated_at': sequence.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"Error getting sequence info: {str(e)}")
            return None
    
    def reset_sequence(self, year: Optional[int] = None, digit: int = 0) -> bool:
        """
        Reset sequence to specified values (for testing/maintenance)
        Default year is 25 (for G25AA00 starting pattern)
        WARNING: Use with caution in production
        """
        try:
            if year is None:
                year = 25  # Default to year 25 for G25AA00 pattern
            
            sequence = self.db.query(GIDSequence).first()
            if sequence:
                sequence.current_year = year  # type: ignore
                sequence.current_digit = digit  # type: ignore
                sequence.current_alpha_1 = 'A'  # type: ignore
                sequence.current_alpha_2 = 'A'  # type: ignore
                sequence.current_number = 0  # type: ignore
            else:
                sequence = GIDSequence(
                    current_year=year,
                    current_digit=digit,
                    current_alpha_1='A',
                    current_alpha_2='A',
                    current_number=0
                )
                self.db.add(sequence)
            
            self.db.commit()
            logger.info(f"Sequence reset to: G{digit}{year:02d}AA00")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting sequence: {str(e)}")
            self.db.rollback()
            return False
    
    def validate_gid_format(self, gid: str) -> bool:
        """Validate if a G_ID follows the correct format"""
        if not gid or len(gid) != 8:
            return False
        
        try:
            # Check format: G{N}{YY}{A}{A}{N}{N}
            if gid[0] != 'G':
                return False
            
            # Check digit
            if not gid[1].isdigit():
                return False
            
            # Check year (2 digits)
            if not gid[2:4].isdigit():
                return False
            
            # Check alphabetic characters
            if not gid[4].isalpha() or not gid[5].isalpha():
                return False
            
            if not gid[4].isupper() or not gid[5].isupper():
                return False
            
            # Check final numbers (2 digits)
            if not gid[6:8].isdigit():
                return False
            
            return True
            
        except Exception:
            return False