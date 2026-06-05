import re
from django.utils import timezone

class TranscriptValidationError(Exception):
    """Raised when a transcript fails validation rules."""
    pass

class TranscriptValidator:
    """Service to validate YouTube transcripts and produce diagnostics."""
    
    @staticmethod
    def validate_and_diagnose(transcript_text, source="youtube", retrieval_timestamp=None, retrieval_method="API"):
        """
        Validates the transcript text according to rules and returns a tuple:
        (validation_status, diagnostics_dict)
        
        Raises TranscriptValidationError if validation fails and validation is enforced.
        """
        if source is None:
            source = "unknown"
            
        source_lower = source.lower()
        text_length = len(transcript_text) if transcript_text else 0
        
        # Check forbidden words (case-insensitive)
        forbidden_patterns = [
            r"simulated",
            r"fallback",
            r"placeholder",
            r"mock\s+transcript",
            r"sample\s+transcript"
        ]
        
        has_forbidden = False
        if transcript_text:
            text_lower = transcript_text.lower()
            for pattern in forbidden_patterns:
                if re.search(pattern, text_lower):
                    has_forbidden = True
                    break
        
        # Validate rules
        is_valid = True
        
        if source_lower != "youtube":
            is_valid = False
            
        if text_length <= 1000:
            is_valid = False
            
        if has_forbidden:
            is_valid = False
            
        if retrieval_timestamp is None:
            is_valid = False

        status = "PASSED" if is_valid else "FAILED"
        
        # Build diagnostics
        preview = ""
        if transcript_text:
            preview = transcript_text[:300] + ("..." if text_length > 300 else "")
            
        diagnostics = {
            "transcript_source": source.upper() if source else "UNKNOWN",
            "transcript_length": text_length,
            "validation_status": status,
            "retrieval_method": retrieval_method,
            "retrieval_timestamp": retrieval_timestamp.isoformat() if retrieval_timestamp else None,
            "transcript_preview": preview
        }
        
        return status, diagnostics

    @classmethod
    def verify_for_generation(cls, transcript_text, source="youtube", retrieval_timestamp=None, retrieval_method="API"):
        """
        Validates the transcript. If validation fails, raises TranscriptValidationError.
        Otherwise, returns the diagnostics.
        """
        status, diagnostics = cls.validate_and_diagnose(
            transcript_text=transcript_text,
            source=source,
            retrieval_timestamp=retrieval_timestamp,
            retrieval_method=retrieval_method
        )
        if status != "PASSED":
            raise TranscriptValidationError(
                f"Transcript validation failed. Status: {status}. Length: {diagnostics['transcript_length']}. "
                f"Method: {diagnostics['retrieval_method']}. Contains forbidden content: {any(p in (transcript_text or '').lower() for p in ['simulated', 'fallback', 'placeholder', 'mock', 'sample'])}"
            )
        return diagnostics
