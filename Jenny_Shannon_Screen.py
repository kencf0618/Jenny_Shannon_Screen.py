import math
import sys
import time
import os
from collections import Counter, deque

sys.set_int_max_str_digits(0)

# Theoretical maximum entropy for decimal digits (log2(10))
MAX_ENTROPY = math.log2(10)  # ≈ 3.321928094887362
ENTROPY_THRESHOLD = 3.129

def get_terminal_size():
    """Get terminal dimensions in characters"""
    try:
        import shutil
        cols, rows = shutil.get_terminal_size()
        return cols, rows
    except:
        return 80, 24  # Default fallback

def shannon_entropy(s):
    """Calculate Shannon entropy of a string (bits per symbol)"""
    freq = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())

def get_sequence_value(seed, iterations):
    """Generate sequence value after N iterations"""
    current = seed
    for _ in range(iterations):
        current = str(int(current, 16))
    return current

def xor_with_key(text, key):
    """XOR operation for encryption/decryption"""
    key_bytes = key.encode()
    text_bytes = text.encode()
    return bytes(t ^ key_bytes[i % len(key_bytes)] for i, t in enumerate(text_bytes))

def encrypt(plaintext, seed, iterations):
    """Encrypt plaintext using sequence as key"""
    key = get_sequence_value(seed, iterations)
    return xor_with_key(plaintext, key).hex()

def decrypt(ciphertext, seed, iterations):
    """Decrypt ciphertext using sequence as key"""
    key = get_sequence_value(seed, iterations)
    return xor_with_key(bytes.fromhex(ciphertext), key).decode()

def calculate_screen_real_estate(num_str, cols=None, rows=None):
    """
    Calculate the screen real estate for a single number.
    Returns detailed metrics about how much terminal space it occupies.
    """
    if cols is None or rows is None:
        cols, rows = get_terminal_size()
    
    digits = len(num_str)
    
    # Characters per screen
    chars_per_line = cols
    lines_per_screen = rows
    chars_per_screen = chars_per_line * lines_per_screen
    
    if digits == 0:
        return {
            'digits': 0,
            'chars_per_line': chars_per_line,
            'lines_per_screen': lines_per_screen,
            'chars_per_screen': chars_per_screen,
            'total_lines': 0,
            'total_screens': 0.0,
            'full_screens': 0,
            'remainder_chars': 0,
            'remainder_percent': 0,
            'screen_percent': 0,
            'line_percent': 0,
            'chars': 0
        }
    
    # Calculate real estate
    total_lines = math.ceil(digits / chars_per_line)
    total_screens = digits / chars_per_screen
    full_screens = digits // chars_per_screen
    remainder_chars = digits % chars_per_screen
    remainder_percent = (remainder_chars / chars_per_screen) * 100 if remainder_chars > 0 else 0
    
    # What percentage of one screen does this number fill?
    screen_percent = (digits / chars_per_screen) * 100 if digits < chars_per_screen else 100
    
    # What percentage of lines does this use?
    line_percent = (total_lines / lines_per_screen) * 100 if total_lines < lines_per_screen else 100
    
    return {
        'digits': digits,
        'chars_per_line': chars_per_line,
        'lines_per_screen': lines_per_screen,
        'chars_per_screen': chars_per_screen,
        'total_lines': total_lines,
        'total_screens': total_screens,
        'full_screens': full_screens,
        'remainder_chars': remainder_chars,
        'remainder_percent': remainder_percent,
        'screen_percent': screen_percent,
        'line_percent': line_percent,
        'chars': digits
    }

def format_screen_estate(estate):
    """Format screen real estate information for display"""
    parts = []
    
    digits = estate['digits']
    total_lines = estate['total_lines']
    total_screens = estate['total_screens']
    full_screens = estate['full_screens']
    remainder = estate['remainder_chars']
    remainder_pct = estate['remainder_percent']
    chars_per_screen = estate['chars_per_screen']
    lines_per_screen = estate['lines_per_screen']
    
    if total_screens < 1:
        pct = estate['screen_percent']
        parts.append(f"{pct:.1f}% of 1 screen")
        parts.append(f"({total_lines} lines, {digits:,} chars)")
    elif total_screens < 2:
        pct = (total_screens - 1) * 100
        parts.append(f"1 full screen + {pct:.1f}% of next")
        parts.append(f"({total_lines} lines, {digits:,} chars)")
    else:
        if remainder == 0:
            parts.append(f"{full_screens} full screens")
        else:
            parts.append(f"{full_screens} full screens + {remainder:,} chars ({remainder_pct:.1f}% of screen {full_screens + 1})")
        parts.append(f"({total_lines:,} total lines, {digits:,} chars)")
    
    # Add detail about lines vs screens
    lines_info = f"Lines: {total_lines:,} ({total_lines / lines_per_screen:.1f} screens worth)"
    
    return " | ".join(parts), lines_info

def format_time(seconds):
    """Format time in human-readable format"""
    if seconds < 0.001:
        return f"{seconds*1000000:.0f} µs"
    elif seconds < 0.1:
        return f"{seconds*1000:.1f} ms"
    elif seconds < 1:
        return f"{seconds*1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"

def run_sequence(seed, entropy_threshold=ENTROPY_THRESHOLD):
    """
    Run sequence with full number display.
    Each number has its screen real estate calculated individually.
    Information displayed at the end of each number.
    """
    current = seed
    seen = {}
    iteration = 0
    entropy_stable = False
    stable_count = 0
    STABLE_REQUIRED = 3
    
    # Snail tracking
    snail_count = 0
    SNAIL_THRESHOLD = 3
    show_snail = True
    
    # Speed tracking
    times = deque(maxlen=10)
    last_entropy = None
    total_time = 0.0
    
    # Get terminal size
    cols, rows = get_terminal_size()
    chars_per_screen = cols * rows
    
    print("\033[2J\033[H")  # Clear screen
    print("=" * 80)
    print("JENNY'S NUMBER - SCREEN REAL ESTATE EDITION")
    print("=" * 80)
    print(f"Seed: {seed}")
    print(f"Terminal: {cols} columns × {rows} rows = {chars_per_screen:,} chars/screen")
    print("Each number's screen real estate is calculated individually")
    print("Press Ctrl+C to stop\n")
    print("-" * 80)
    print()
    
    try:
        while True:
            # Start timing
            iter_start_time = time.perf_counter()
            
            # Generate next value
            current = str(int(current, 16))
            digit_count = len(current)
            
            # Calculate screen real estate for THIS number
            estate = calculate_screen_real_estate(current, cols, rows)
            screen_summary, lines_info = format_screen_estate(estate)
            
            # End timing
            iter_end_time = time.perf_counter()
            iter_time = iter_end_time - iter_start_time
            total_time += iter_time
            
            # Track performance
            times.append(iter_time)
            avg_time = sum(times) / len(times) if times else iter_time
            
            # Determine speed
            is_snail = False
            if avg_time > 0 and iter_time > 0:
                speed_ratio = avg_time / iter_time
                if speed_ratio < 0.7 and digit_count > 100000:
                    is_snail = True
            
            # Snail counter logic
            if is_snail:
                snail_count += 1
            else:
                snail_count = 0
            
            if snail_count >= SNAIL_THRESHOLD:
                show_snail = False
            elif snail_count == 0:
                show_snail = True
            
            # Calculate entropy only if not stable
            if not entropy_stable:
                entropy = shannon_entropy(current)
                last_entropy = entropy
                
                if entropy >= entropy_threshold:
                    stable_count += 1
                    if stable_count >= STABLE_REQUIRED:
                        entropy_stable = True
            else:
                entropy = None
            
            # DISPLAY THE NUMBER IN FULL (this will scroll off screen)
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration}")
            print(f"{'-'*80}")
            
            # DISPLAY THE FULL NUMBER FIRST
            print(current)
            print(f"{'-'*80}")
            
            # NOW DISPLAY THE INFORMATION AT THE END
            print(f"END OF ITERATION {iteration}")
            print(f"{'-'*40}")
            print(f"DIGITS:          {digit_count:,}")
            print(f"SCREEN REAL ESTATE: {screen_summary}")
            print(f"                 {lines_info}")
            print(f"TIME:            {format_time(iter_time)}")
            print(f"TOTAL TIME:      {format_time(total_time)}")
            
            # Show speed
            if show_snail and is_snail:
                print(f"SPEED:           🐌 SNAIL")
            elif show_snail and not is_snail and digit_count > 1000:
                print(f"SPEED:           ⚡ FAST")
            elif not show_snail:
                print(f"SPEED:           SLOW (steady state)")
            
            # Show entropy if still calculating
            if not entropy_stable and entropy is not None:
                print(f"ENTROPY:         H={entropy:.4f} bits/digit")
            elif entropy_stable:
                print(f"ENTROPY:         STABLE (H={MAX_ENTROPY:.4f})")
            
            # Show average time
            if len(times) > 1:
                print(f"AVG TIME:        {format_time(avg_time)}")
            
            print(f"{'='*80}\n")
            
            # Cycle detection
            if current in seen:
                print(f"\n⚠ CYCLE DETECTED: iteration {iteration} repeats iteration {seen[current]}")
                break
            seen[current] = iteration
            iteration += 1
            
            # Show memory info periodically
            if iteration % 5 == 0 and digit_count > 1000000:
                try:
                    import psutil
                    process = psutil.Process()
                    mem_mb = process.memory_info().rss / (1024 * 1024)
                    mem_percent = process.memory_percent()
                    print(f"\n--- MEMORY: {mem_mb:.1f} MB ({mem_percent:.1f}%) | ELAPSED: {format_time(total_time)} ---\n")
                except:
                    print(f"\n--- ELAPSED: {format_time(total_time)} ---\n")
            
            # Dynamic sleep
            if digit_count < 1000:
                time.sleep(1.5)
            elif digit_count < 10000:
                time.sleep(0.8)
            elif digit_count < 100000:
                time.sleep(0.3)
            else:
                time.sleep(0.05)
            
            # Clear screen occasionally to prevent terminal bloat
            if estate['total_screens'] > 10 and iteration % 3 == 0:
                print("\033[2J\033[H")  # Clear screen
                print(f"\n--- SCREEN CLEARED at iteration {iteration} ---\n")
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print("⏹ SEQUENCE HALTED")
        print(f"{'-'*80}")
        print(f"Stopped at iteration:  {iteration}")
        print(f"Final digit count:     {len(current):,}")
        print(f"Final screen estate:   {screen_summary}")
        print(f"Elapsed time:          {format_time(total_time)}")
        print(f"Last iteration time:   {format_time(iter_time)}")
        if last_entropy:
            print(f"Final entropy:         {last_entropy:.4f} bits/digit")
        print(f"Stable entropy:        {'YES' if entropy_stable else 'NO'}")
        print(f"Snail status:          {'REMOVED' if not show_snail else 'ACTIVE'}")
        print("=" * 80)
        
    except MemoryError:
        print(f"\n\n{'='*80}")
        print("💥 MEMORY EXHAUSTED")
        print(f"{'-'*80}")
        print(f"At iteration:          {iteration}")
        print(f"Digit count:           {len(current):,}")
        print(f"Screen estate:         {screen_summary}")
        print(f"Elapsed time:          {format_time(total_time)}")
        print(f"Last iteration time:   {format_time(iter_time)}")
        print("This is the true terminal limit!")
        print("=" * 80)

def main():
    """Main program"""
    print("\033[2J\033[H")  # Clear screen
    cols, rows = get_terminal_size()
    print("=" * 80)
    print("JENNY'S NUMBER - SCREEN REAL ESTATE EDITION")
    print("=" * 80)
    print(f"Terminal: {cols} columns × {rows} rows")
    print(f"Characters per screen: {cols * rows:,}")
    print("\nFeatures:")
    print("  • Numbers displayed in FULL (they WILL scroll off screen)")
    print("  • Screen real estate calculated for EACH number individually")
    print("  • Information displayed at the END of each number")
    print("  • No density bars")
    print("  • Snail icon removed after 3 consecutive slow iterations")
    print("  • H= removed after entropy stabilization\n")
    
    mode = input("Mode — (r)un sequence ").strip().lower()
    seed = input("Seed (hex): ").strip()
    
    if mode == "r":
        run_sequence(seed)
    elif mode == "e":
        iterations = int(input("Iterations: "))
        plaintext = input("Message: ")
        start = time.time()
        ciphertext = encrypt(plaintext, seed, iterations)
        elapsed = time.time() - start
        print(f"\nCiphertext: {ciphertext}")
        print(f"Encryption time: {elapsed:.2f}s")
    elif mode == "d":
        iterations = int(input("Iterations: "))
        ciphertext = input("Ciphertext (hex): ")
        start = time.time()
        plaintext = decrypt(ciphertext, seed, iterations)
        elapsed = time.time() - start
        print(f"\nPlaintext: {plaintext}")
        print(f"Decryption time: {elapsed:.2f}s")
    else:
        print("Invalid mode. Use 'r', 'e', or 'd'.")

if __name__ == "__main__":
    main()
