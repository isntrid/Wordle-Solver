# Wordle Solver <img src="download.png" width="30">

A command-line argument tool that narrows down possible Wordle answers based on the feedback from each guess.

Wordle is a simple 5-letter word game, where you input words and attempt to find the answer via deduction.

## How it works

    A green letter means: this letter is in the word, at this exact position.
    A yellow letter means: this letter is in the word, but not in this position.
    A grey letter means: this letter is not in the word, at any position.

## Features

- The program automatically finds the grey letters in your word. Meaning, you only have to input the green and yellow letters. Greys are handled for you.
- Total possible word count is shown each turn.
- Filters every word for you
- Simple and easy to understand prompting.  

## Usage

- Enter in a word of your choice into Wordle, i will be using 'soare' for this example
- Enter the word and the results of it into the program. For me, only 'a' was yellow, and everything else was grey.
- The program asks you for what letters were green. If none were green, then enter 'none'.
For me, my only yellow was 'a', so i enter that. There is no need to input the grey letters.
- The program returns a list of words, of which you can pick any. I picked 'admit.'
- In 'admit', the 'a' and 'i' were green, while the 't' was yellow.
- Now, i tell the program that i am not finished and repeat the process
- For greens, i input 'ai', for yelows i input 't', and then i can pick another word.
- I then pick the word 'attic,' which happens to be the exact word. All letters are green, and then i tell the program that i am finished.
- You have solved Wordle.

## Requirements

- Python 3.8+
