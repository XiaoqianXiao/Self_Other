import itertools
# %%
import math
import random
from datetime import datetime
from pytz import timezone
import pandas as pd
import os
from itertools import permutations
from psychopy import visual, event, core, data, logging


# %%
def run_run(setting, df_trial, max_duration,
            results_dir, resultFile_name,
            thisExp,
            trialClock, win,
            SCANNER_KEYS, LOCAL_KEYS, QUIT_KEYS, SUBJECT_KEYS,
            text_condition, text_adjective, fix):
    """
    Runs the trial loop, logs responses and timings, and computes UPPERCASE accuracy.
    Stores run-level stats in thisExp.extraInfo: 'uppercase_total', 'uppercase_correct'.
    """
    # --- Counters for UPPERCASE accuracy over the run ---
    uppercase_total = 0
    uppercase_correct = 0

    trialClock.reset()
    for index, row in df_trial.iterrows():
        trial = row.to_dict()
        thisExp.addData('trial_no', trial['trial_no'])
        thisExp.addData('onset_time', trial['onset_time'])
        thisExp.addData('words', trial['words'])
        thisExp.addData('condition_name', trial['condition_name'])
        thisExp.addData('valence', trial['valence'])
        thisExp.addData('judgement', trial['judgement'])

        # ---- Prepare stimuli for this trial ----
        text_condition.text = trial['condition_name']
        text_adjective.text = trial['words_present']
        onset_time = trial['onset_time']

        # Wait for the specified onset time
        while trialClock.getTime() < onset_time:
            pass

        # Draw and flip to screen
        fix.setAutoDraw(True)
        text_condition.draw()
        text_adjective.draw()
        win.flip()

        accurate_onsetTime = trialClock.getTime()
        thisExp.addData('accurate_onsetTime', accurate_onsetTime)

        # ---- Collect response ----
        if setting == 'SCANNER':
            keys = event.waitKeys(keyList=SCANNER_KEYS,
                                  timeStamped=trialClock,
                                  maxWait=max_duration)
        elif setting == 'PRACTICE':
            keys = event.waitKeys(keyList=LOCAL_KEYS,
                                  timeStamped=trialClock,
                                  maxWait=max_duration)
        else:
            keys = event.waitKeys(timeStamped=trialClock, maxWait=max_duration)

        if keys:
            response, reaction_time = keys[0]
            rt = reaction_time - accurate_onsetTime
        else:
            response = None
            reaction_time = None
            rt = None

        # ---- Early quit ----
        if response in QUIT_KEYS:
            resultFile_name = "tmp_" + resultFile_name
            resultFile_path = os.path.join(results_dir, resultFile_name)
            thisExp.saveAsWideText(resultFile_path)
            core.quit()

        # ---- Log raw response/timing ----
        thisExp.addData('reaction_time', reaction_time)
        thisExp.addData('rt', rt)
        thisExp.addData('responses', response)

        # Map raw key → semantic answer ('yes'/'no') when applicable
        answer = None  # initialize to avoid UnboundLocalError
        if response in SUBJECT_KEYS.keys():
            answer = SUBJECT_KEYS[response]  # translate from key to meaning
        thisExp.addData('answer', answer)    # always log (even if None)

        # --------- Accuracy scoring for UPPERCASE condition ----------
        # Question: "Is the word in UPPERCASE?"
        expected_answer = None
        is_correct = None

        if trial['condition_name'] == 'UPPERCASE':
            # Ground truth from the trial's 'judgement' column
            if trial['judgement'] == 'UPPER':
                expected_answer = 'yes'
            elif trial['judgement'] == 'LOWER':
                expected_answer = 'no'

            # Only score when participant provided a yes/no answer
            if expected_answer is not None and answer in ('yes', 'no'):
                is_correct = int(answer == expected_answer)
                uppercase_total += 1
                uppercase_correct += is_correct
            # If you want to count misses as incorrect, uncomment below:
            elif expected_answer is not None:
                uppercase_total += 1
                is_correct = 0

        # Save per-trial scoring fields (None for non-UPPERCASE trials)
        thisExp.addData('expected_answer', expected_answer)
        thisExp.addData('is_correct', is_correct)

        # End of trial - move to next line in data output
        fix.setAutoDraw(True)
        win.flip()
        thisExp.nextEntry()

    # Store run-level stats for post-run feedback
    thisExp.extraInfo['uppercase_total'] = uppercase_total
    thisExp.extraInfo['uppercase_correct'] = uppercase_correct


# %%
def show_instruction(setting, INSTRUCTIONS, text_intro, win,
                     SCANNER_TRIGGER_KEY, LOCAL_START_KEY, QUIT_KEYS):
    """Waits for the subject to continue; then waits for the next scanner trigger if in scanner."""
    text_intro.text = INSTRUCTIONS[setting]
    text_intro.draw()
    win.flip()
    if setting == 'PRACTICE':  # only show instruction if there is a text to show
        key = event.waitKeys(keyList=LOCAL_START_KEY + QUIT_KEYS)[0]  # just pick first response, no timestamp
        if key in QUIT_KEYS:
            core.quit()
    # Wait for scanner to start -
    elif setting == 'SCANNER':
        key = event.waitKeys(keyList=SCANNER_TRIGGER_KEY + QUIT_KEYS)[0]  # synchronize with scanner
        if key in QUIT_KEYS:
            core.quit()
    core.wait(0.5)


def run_goodbye(win, fix, thisExp, feedback_duration_sec=0.0):
    """
    Optional on-screen goodbye/feedback in the main full-screen window.
    Default feedback_duration_sec=0.0 means no feedback here (use post-run window instead).
    """
    # Ensure fixation isn't auto-drawing over feedback
    fix.setAutoDraw(False)

    # Brief fixation flash (to preserve timing feel)
    fix.draw()
    win.flip()
    core.wait(0.2)

    if feedback_duration_sec <= 0.0:
        return

    # ---- Build feedback from stored stats ----
    uppercase_total = thisExp.extraInfo.get('uppercase_total', 0)
    uppercase_correct = thisExp.extraInfo.get('uppercase_correct', 0)

    if uppercase_total > 0:
        acc_pct = 100.0 * uppercase_correct / float(uppercase_total)
        feedback_lines = [
            'Question: "Is the word in UPPERCASE?"',
            f'UPPERCASE accuracy: {acc_pct:.1f}%  ({uppercase_correct}/{uppercase_total})'
        ]
    else:
        feedback_lines = [
            'Question: "Is the word in UPPERCASE?"',
            'No UPPERCASE trials in this run.'
        ]

    feedback_text = "\n\n".join(feedback_lines)

    # Show feedback (white text is default; background is black)
    feedback_stim = visual.TextStim(
        win,
        text=feedback_text,
        height=0.9,
        pos=(0, 0),
        wrapWidth=20  # prevents long lines from clipping off-screen (units='deg')
    )
    feedback_stim.draw()
    win.flip()
    core.wait(feedback_duration_sec)


def show_postrun_feedback(thisExp, wait_for_key=True, duration_sec=5.0):
    """
    Show UPPERCASE accuracy in a small window AFTER the main experiment window has closed.
    If wait_for_key == True, waits for any key; otherwise holds for duration_sec seconds.
    """
    # Build feedback text from saved stats
    uppercase_total = thisExp.extraInfo.get('uppercase_total', 0)
    uppercase_correct = thisExp.extraInfo.get('uppercase_correct', 0)

    if uppercase_total > 0:
        acc_pct = 100.0 * uppercase_correct / float(uppercase_total)
        feedback_text = (
            f'UPPERCASE accuracy: {acc_pct:.1f}%  ({uppercase_correct}/{uppercase_total})\n\n'
            + ('Press any key to exit.' if wait_for_key else f'Holding for {duration_sec:.0f}s...')
        )
    else:
        feedback_text = (
            'No UPPERCASE trials in this run.\n\n'
            + ('Press any key to exit.' if wait_for_key else f'Holding for {duration_sec:.0f}s...')
        )

    # Open a new, non-fullscreen window (pixels)
    win_fb = visual.Window(size=[920, 640], units='pix', fullscr=False, color=(-1, -1, -1))

    # Optional background panel for contrast
    panel = visual.Rect(win_fb, width=880, height=520, fillColor=[-0.5, -0.5, -0.5],
                        lineColor=None, opacity=0.9)
    panel.draw()

    # Feedback text (wrapped so it fits nicely)
    text = visual.TextStim(win_fb, text=feedback_text, height=28, wrapWidth=820,
                           pos=(0, 0), color=[1, 1, 1], bold=True)
    text.draw()
    win_fb.flip()

    if wait_for_key:
        event.waitKeys()   # wait for any key
    else:
        core.wait(duration_sec)

    win_fb.close()


def list_permutations(lst):
    return list(permutations(lst))
