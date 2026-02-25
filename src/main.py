from typing import List, Dict, Any
from pathlib import Path

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
                word
                for w in lines
                if (word := w.strip().lower()).isalpha()
                and word.isascii()
                and len(word) == 5
            ]
    except FileNotFoundError as e:
        raise FileNotFoundError("No word / dictionary file was found.") from e
    except PermissionError as e:
        raise PermissionError("Access to dictionary file was denied.") from e
    return words


def get_input() -> str:
    """
    Prompt the user for a 5-letter guess word.

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


def get_colours(
    overall_green: List[str] = None,
    overall_yellow: List[str] = None,
    overall_grey: List[str] = None,
) -> tuple[list[str], list[str], list[str], str]:
    """
    Collect feedback information for a guess and accumulate it across turns.

    Args:
        overall_green (List[str] | None): Accumulated green letters so far.
        overall_yellow (List[str] | None): Accumulated yellow letters so far.
        overall_grey (List[str] | None): Accumulated grey letters so far.

    Returns:
        tuple[list[str], list[str], list[str], str]:
            (overall_green, overall_yellow, overall_grey, choice) where:
            - overall_green: all green letters seen so far
            - overall_yellow: all yellow letters seen so far
            - overall_grey: all grey letters seen so far
            - choice: the user's guessed word for this turn
    """
    if overall_green is None:
        overall_green = []
    if overall_yellow is None:
        overall_yellow = []
    if overall_grey is None:
        overall_grey = []

    choice = get_input()
    greens = get_feedback_letters("greens", choice)
    yellows = get_feedback_letters("yellow", choice)
    greys = list(choice)

    for letter in greens + yellows:
        if letter in greys:
            greys.remove(letter)

    overall_green.extend(greens)
    overall_yellow.extend(yellows)
    overall_grey.extend(greys)
    return overall_green, overall_yellow, overall_grey, choice


def get_feedback_letters(colour_name: str, choice: str) -> List[str]:
    """
    Ask the user which letters in their guess were a given colour.

    Args:
        colour_name (str): The colour name ("green", "yellow", or "grey").
        choice (str): The user's chosen word.

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


def compile_colours(
    green: List[str], grey: List[str], yellow: List[str], choice: str
) -> tuple[dict[Any, Any], dict[Any, Any], list[Any]]:
    """
    Convert per-turn colour feedback into structures used for filtering valid words.

    Args:
        green (List[str]): Letters marked green in the guess.
        grey (List[str]): Letters marked grey in the guess.
        yellow (List[str]): Letters marked yellow in the guess.
        choice (str): The user's guessed word.

    Returns:
        tuple[dict[int, str], dict[str, list[int]], list[str]]:
            (green_letters, yellow_letters, grey_letters) where:
            - green_letters maps index -> correct letter
            - yellow_letters maps letter -> list of indices where that letter is NOT allowed
            - grey_letters is a list of letters not in the answer (excluding known green/yellow)
    """
    green_letters = {}
    yellow_letters = {}
    grey_letters = []

    for pos, char in enumerate(choice):
        if char in green:
            green_letters[pos] = char
        if char in yellow:
            yellow_letters.setdefault(char, []).append(pos)
        if char in grey and char not in green and char not in yellow:
            grey_letters.append(char)

    return green_letters, yellow_letters, grey_letters


def get_frequency_score(valid_words_list: List[str]) -> List[str]:
    """
    Score candidate words by letter frequency across the candidate list and return the top 5.

    Each word's score is computed as the sum of frequencies of its unique letters.

    Args:
        valid_words_list (List[str]): Candidate words to score.

    Returns:
        List[str]: Up to 5 highest-scoring words (best first).
    """
    alphabet = {}
    for word in valid_words_list:
        for letter in word:
            if letter not in alphabet:
                alphabet[letter] = 1
            else:
                alphabet[letter] += 1

    # sort alphabet by frequency descending
    sorted_alphabet = {
        k: v
        for k, v in sorted(
            alphabet.items(), key=lambda item: item[1], reverse=True
        )
    }

    scores = []
    for word in valid_words_list:
        word_score = sum(sorted_alphabet[letter] for letter in set(word))
        scores.append((word_score, word))

    # getting the 5 highest scoring words
    best_words = [word for score, word in sorted(scores, reverse=True)[:5]]
    return best_words


def find_words(
    green: Dict[int, str],
    yellow: Dict[str, list],
    grey: List[str],
    valid_words_list: List[str],
) -> tuple[list[Any], list[str]]:
    """
    Filter the word list down to words consistent with known green/yellow/grey constraints.

    Args:
        green (Dict[int, str]): Known green letters by position (index -> letter).
        yellow (Dict[str, list[int]]): Known yellow letters (letter -> list of forbidden positions).
        grey (List[str]): Letters that must not appear in the word.
        valid_words_list (List[str]): Words to filter.

    Returns:
        tuple[List[str], List[str]]: (valid, best_words) where:
            - valid is the filtered list of possible answers
            - best_words is up to 5 recommended guesses from valid
    """
    valid = []
    for word in valid_words_list:
        if any(letter in word for letter in grey):
            continue
        if any(word[pos] != letter for pos, letter in green.items()):
            continue

        bad_yellow = False
        for letter, positions in yellow.items():
            if letter not in word:
                bad_yellow = True
                break
            if any(word[pos] == letter for pos in positions):
                bad_yellow = True
                break

        if bad_yellow:
            continue

        valid.append(word)

    best_words = get_frequency_score(valid)
    return valid, best_words


def continue_program(valid_words: List[str]) -> None:
    """
    Loop to continue receiving feedback and printing recommended next guesses.

    Args:
        valid_words (List[str]): Current list of candidate words to continue filtering.

    Raises:
        ValueError: Too many invalid attempts.
    """
    MAX_ATTEMPTS = 5
    for _ in range(MAX_ATTEMPTS):
        word = input("\nAre you finished? ").strip().lower()
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
            exit(0)
        else:
            overall_green, overall_yellow, overall_grey = [], [], []
            overall_green, overall_yellow, overall_grey, choice = get_colours(
                overall_green, overall_yellow, overall_grey
            )
            green_letters, yellow_letters, grey_letters = compile_colours(
                overall_green, overall_grey, overall_yellow, choice
            )
            valid_words, best_words = find_words(
                green_letters, yellow_letters, grey_letters, valid_words
            )
            print("Pick one:")
            for word in best_words:
                print(word, end=" ")
    raise ValueError("Too many invalid attempts.")


def main():
    overall_green = []
    overall_yellow = []
    overall_grey = []
    valid_words = get_words()
    overall_green, overall_yellow, overall_grey, choice = get_colours(
        overall_green, overall_yellow, overall_grey
    )
    green_letters, yellow_letters, grey_letters = compile_colours(
        overall_green, overall_grey, overall_yellow, choice
    )
    valid_words, best_words = find_words(
        green_letters, yellow_letters, grey_letters, valid_words
    )
    print("Pick one:")
    for word in best_words:
        print(word, end=" ")
    continue_program(valid_words)


if __name__ == "__main__":
    main()
