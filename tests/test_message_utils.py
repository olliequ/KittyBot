import unittest
from commons.message_utils import split_message, DISCORD_MESSAGE_LIMIT

class TestMessageSplitting(unittest.TestCase):
    def test_short_message(self):
        """Test that short messages are not split"""
        message = "Short message"
        result = split_message(message)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], message)
    
    def test_exact_limit(self):
        """Test message exactly at the limit"""
        message = "a" * DISCORD_MESSAGE_LIMIT
        result = split_message(message)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), DISCORD_MESSAGE_LIMIT)
    
    def test_newline_splitting(self):
        """Test splitting on newlines"""
        lines = ["Line " + str(i) for i in range(100)]
        message = "\n".join(lines)
        result = split_message(message)
        
        # Verify each part is within limit
        for part in result:
            self.assertLessEqual(len(part), DISCORD_MESSAGE_LIMIT)
        
        # Verify all content is preserved
        combined = "\n".join(result)
        self.assertEqual(set(combined.split("\n")), set(lines))
    
    def test_long_line_splitting(self):
        """Test splitting a very long line without spaces"""
        message = "x" * (DISCORD_MESSAGE_LIMIT * 2)
        result = split_message(message)
        
        # Should be split into at least 2 parts
        self.assertGreater(len(result), 1)
        
        # Each part should be within limit
        for part in result:
            self.assertLessEqual(len(part), DISCORD_MESSAGE_LIMIT)
        
        # Combined content should match original
        combined = "".join(result)
        self.assertEqual(combined, message)
    
    def test_mixed_content(self):
        """Test splitting mixed content with newlines and long lines"""
        parts = [
            "Normal line",
            "a" * 1500,
            "Another normal line",
            "x" * 2500,
            "Final line"
        ]
        message = "\n".join(parts)
        result = split_message(message)
        
        # Each part should be within limit
        for part in result:
            self.assertLessEqual(len(part), DISCORD_MESSAGE_LIMIT)
        
        # All content should be preserved, but may be split differently
        combined = " ".join(result)  # Join with space to handle split lines
        for part in parts:
            # Check if the content exists, possibly split across messages
            self.assertTrue(
                part in combined or all(
                    chunk in combined 
                    for chunk in [part[i:i+DISCORD_MESSAGE_LIMIT] 
                                for i in range(0, len(part), DISCORD_MESSAGE_LIMIT)]
                ),
                f"Content not found: {part[:50]}..."
            )

if __name__ == "__main__":
    unittest.main() 