from typing import List, Dict
from pathlib import Path
from collections import Counter

WORD_FILE = Path(__file__).with_name("words.txt")


def get_words() -> List[str]:
    """
    This function looks at words.txt, a text file containing many words, and collects any
    5-letter English words that contain only letters (no numbers/punctuation).

    Returns:
        List[str]: A list of valid 5-letter words.

    Raises:
        FileNotFoundError: No word/dictionary file was found.
        PermissionError: Program was denied permission to access and read a dictionary file.
    """
    try:
        with open(WORD_FILE, "r") as w:
            lines = w.readlines()
            words = [
                word for w in lines
                if (word := w.strip().lower()).isalpha() and word.isascii() and len(word) == 5]
    except FileNotFoundError as e:
        raise FileNotFoundError("No word / dictionary file was found.") from e
    except PermissionError as e:
        raise PermissionError("Access to dictionary file was denied.") from e
    return words


def get_input() -> str:
    """
    Prompt the user for a 5-letter guess word.

    Performs basic validation (length, ASCII, and alphabetic-only). The user is given a limited
    number of attempts before the function fails.

    Returns:
        str: The validated 5-letter word entered by the user.

    Raises:
        ValueError: Too many invalid attempts.
    """
    MAX_ATTEMPTS = 5
    for _ in range(MAX_ATTEMPTS):
        word = input("Word: ").strip().lower()
        if not word:
            print("Empty input. Try again.")
            continue
        if len(word) != 5:
            print("Word must be 5 letters.")
            continue
        if not word.isascii():
            print("Only standard English letters allowed.")
            continue
        if not word.isalpha():
            print("No numbers or punctuation.")
            continue
        return word
    raise ValueError("Too many invalid attempts.")


def get_feedback_letters(colour_name: str, choice: str) -> List[str]:
    """
    Ask the user which letters in their guess were a given colour.

    The user types the letters that received a specific Wordle feedback colour. The special
    value "none" indicates no letters of that colour.

    Args:
        colour_name (str): The colour name ("green", "yellow", or "grey").
        choice (str): The user's chosen word (used to validate that entered letters appear in it).

    Returns:
        List[str]: The letters (as single-character strings) of the given colour type.
    """
    while True:
        letters = (
            input(
                f"What letters were {colour_name}? Enter none if no letters of that type were found: "
            )
            .strip()
            .lower()
        )
        if letters == "none":
            return []
        elif any(char not in choice for char in list(letters)):
            print(f"A letter was not found in {choice}. Try again.")
        else:
            break
    return list(letters)


def get_turn_feedback(choice: str):
    """
    Collect per-turn feedback for a guess and classify letters as green, yellow, or grey.

    This prompts the user for green and yellow letters first, then derives grey letters as the
    remaining letters from the guess after removing the reported green/yellow occurrences.

    Args:
        choice (str): The guessed 5-letter word for the current turn.

    Returns:
        tuple[list[str], list[str], list[str]]: (greens, yellows, greys) as lists of single-character strings.
    """
    greens = get_feedback_letters("green", choice)
    yellows = get_feedback_letters("yellow", choice)
    greys = list(choice)
    for letter in greens + yellows:
        if letter in greys:
            greys.remove(letter)
    return greens, yellows, greys


def compile_turn(choice, greens, yellows, greys):
    """
    Convert a single turn's feedback into constraint structures used for filtering candidate words.

    Produces:
    - green_pos: exact known letters by position
    - yellow_pos: letters that must appear, but not at specific positions
    - min_counts: minimum occurrences required for each letter (from green + yellow evidence)
    - exact_counts: exact occurrences for letters that were also marked grey in this guess
      (i.e., no additional occurrences beyond the non-grey count)

    Args:
        choice (str): The guessed word.
        greens (list[str]): Letters confirmed correct and in the correct position.
        yellows (list[str]): Letters confirmed present but in the wrong position.
        greys (list[str]): Letters not present beyond the confirmed non-grey occurrences.

    Returns:
        tuple[dict[int, str], dict[str, list[int]], Counter, dict[str, int]]:
            (green_pos, yellow_pos, min_counts, exact_counts)
    """
    green_pos = {}
    yellow_pos = {}
    min_counts = Counter()
    exact_counts = {}

    for i, char in enumerate(choice):
        if char in greens:
            green_pos[i] = char
            min_counts[char] += 1
        elif char in yellows:
            yellow_pos.setdefault(char, []).append(i)
            min_counts[char] += 1

    for letter in set(choice):
        total_in_guess = choice.count(letter)
        non_grey = min_counts[letter]
        if letter in greys:
            exact_counts[letter] = non_grey

    return green_pos, yellow_pos, min_counts, exact_counts


def word_pass_criteria(word, green, yellow, min_counts, exact_counts):
    """
    Check whether a candidate word satisfies all accumulated Wordle constraints.

    Constraints enforced:
    - Green positions must match exactly.
    - Yellow letters must exist in the word, but not in any disallowed positions.
    - Each letter must appear at least min_counts[letter] times.
    - For letters with exact_counts, the word must contain exactly that many occurrences.

    Args:
        word (str): Candidate word to validate.
        green (dict[int, str]): Mapping of index -> required letter (green constraints).
        yellow (dict[str, list[int]]): Mapping of letter -> positions it cannot occupy (yellow constraints).
        min_counts (Counter): Minimum required occurrences for letters.
        exact_counts (dict[str, int]): Exact required occurrences for letters (typically due to grey feedback).

    Returns:
        bool: True if the word passes all criteria; otherwise False.
    """
    wc = Counter(word)

    if any(word[pos] != letter for pos, letter in green.items()):
        return False

    for letter, positions in yellow.items():
        if letter not in word:
            return False
        if any(word[pos] == letter for pos in positions):
            return False

    for letter, count in min_counts.items():
        if wc[letter] < count:
            return False

    for letter, count in exact_counts.items():
        if wc[letter] != count:
            return False

    return True


def get_frequency_score(valid_words_list: List[str]) -> List[str]:
    """
    Rank candidate words by letter-frequency coverage and return a small set of top suggestions.

    Scoring strategy:
    - Build a frequency table over the candidate list counting how many words contain each letter.
    - Score each word by summing frequencies of its *unique* letters (encourages diverse letters).
    - Return the top 5 scoring words.

    Args:
        valid_words_list (List[str]): Current candidate solutions.

    Returns:
        List[str]: Up to 5 suggested words ordered from highest to lowest score.
    """
    alphabet = {}
    for word in valid_words_list:
        for letter in set(word):
            alphabet[letter] = alphabet.get(letter, 0) + 1

    scores = []
    for word in valid_words_list:
        score = sum(alphabet[letter] for letter in set(word))
        scores.append((score, word))

    best_words = [word for score, word in sorted(scores, reverse=True)[:5]]
    return best_words


def find_words(green, yellow, min_counts, exact_counts, valid_words_list):
    """
    Filter the current candidate list using constraints, then compute top suggestions.

    Args:
        green (dict[int, str]): Green position constraints.
        yellow (dict[str, list[int]]): Yellow letter constraints (must appear, not in these positions).
        min_counts (Counter): Minimum required occurrences for each letter.
        exact_counts (dict[str, int]): Exact required occurrences for some letters.
        valid_words_list (list[str]): Words to filter (typically the remaining candidates).

    Returns:
        tuple[list[str], list[str]]: (valid, best_words) where:
            - valid is the filtered candidate list
            - best_words is a short list of high-value guesses (from get_frequency_score)
    """
    valid = []
    for word in valid_words_list:
        if word_pass_criteria(word, green, yellow, min_counts, exact_counts):
            valid.append(word)
    best_words = get_frequency_score(valid)
    return valid, best_words


def continue_program() -> bool:
    """
    Ask the user whether the Wordle has been solved and the program should stop.

    Accepts yes (y/yes) or no (n/no) with basic input validation and a limited number of attempts.

    Returns:
        bool: True if the user indicates they are finished; False otherwise.

    Raises:
        ValueError: Too many invalid attempts.
    """
    MAX_ATTEMPTS = 5
    for _ in range(MAX_ATTEMPTS):
        word = input("\nAre you finished? (y/n) ").strip().lower()
        if not word:
            print("Empty input. Try again.")
            continue
        if not word.isascii():
            print("Only standard English letters allowed.")
            continue
        if not word.isalpha():
            print("No numbers or punctuation.")
            continue
        if word in ["y", "yes"]:
            print("You successfully have solved Wordle.")
            return True
        if word in ["n", "no"]:
            return False
        print("Please enter y/yes or n/no.")
    raise ValueError("Too many invalid attempts.")


def main():
    """
    Run the interactive Wordle solver loop.

    Loads the dictionary, repeatedly collects the user's guess + feedback, accumulates constraints
    across turns, filters remaining candidates, and prints a few high-value suggestions each round.
    """
    valid_words = get_words()
    cumulative_green = {}
    cumulative_yellow = {}
    cumulative_min = Counter()
    cumulative_exact = {}

    while True:
        choice = get_input()
        greens, yellows, greys = get_turn_feedback(choice)
        g_pos, y_pos, min_counts, exact_counts = compile_turn(choice, greens, yellows, greys)

        cumulative_green.update(g_pos)

        for letter, positions in y_pos.items():
            cumulative_yellow.setdefault(letter, [])
            cumulative_yellow[letter].extend(positions)

        for letter, count in min_counts.items():
            cumulative_min[letter] = max(cumulative_min[letter], count)

        for letter, count in exact_counts.items():
            cumulative_exact[letter] = count

        valid_words, best_words = find_words(
            cumulative_green,
            cumulative_yellow,
            cumulative_min,
            cumulative_exact,
            valid_words
        )

        print("Pick one:")
        for word in best_words:
            print(word, end=" ")
        print()

        if continue_program():
            return


if __name__ == "__main__":
    main()