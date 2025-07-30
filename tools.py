
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


#%%
def run_run(setting, df_trial, max_duration,
            results_dir, resultFile_name,
            thisExp,
            trialClock, win,
            SCANNER_KEYS, LOCAL_KEYS, QUIT_KEYS, SUBJECT_KEYS,
            text_condition, text_adjective, fix):
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

        # Prepare
        text_condition.text = trial['condition_name']
        text_adjective.text = trial['words_present']
        onset_time = trial['onset_time']

        # Wait for the specified onset time
        while trialClock.getTime() < onset_time:
            pass

        fix.setAutoDraw(True)
        text_condition.draw()
        text_adjective.draw()
        win.flip()
        accurate_onsetTime = trialClock.getTime()
        thisExp.addData('accurate_onsetTime', accurate_onsetTime)

        # Collect response
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

        # Early quit
        if response in QUIT_KEYS:
            resultFile_name = "tmp_" + resultFile_name
            resultFile_path = os.path.join(results_dir, resultFile_name)
            thisExp.saveAsWideText(resultFile_path)
            core.quit()

        # Log raw response/timing
        thisExp.addData('reaction_time', reaction_time)
        thisExp.addData('rt', rt)
        thisExp.addData('responses', response)

        # Map raw key → semantic answer ('yes'/'no') when applicable
        answer = None  # <<< initialize to avoid UnboundLocalError
        if response in SUBJECT_KEYS.keys():
            answer = SUBJECT_KEYS[response]  # translate from key to meaning
        thisExp.addData('answer', answer)    # always log, even if None

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
            # elif expected_answer is not None:
            #     uppercase_total += 1
            #     is_correct = 0

        # Save per-trial scoring fields (None for non-UPPERCASE trials)
        thisExp.addData('expected_answer', expected_answer)
        thisExp.addData('is_correct', is_correct)

        # end of trial - move to next line in data output
        fix.setAutoDraw(True)
        win.flip()
        thisExp.nextEntry()

    # Store run-level stats for goodbye feedback
    thisExp.extraInfo['uppercase_total'] = uppercase_total
    thisExp.extraInfo['uppercase_correct'] = uppercase_correct


#%%
def show_instruction(setting, INSTRUCTIONS, text_intro, win,
                     SCANNER_TRIGGER_KEY, LOCAL_START_KEY, QUIT_KEYS):
    """Waits for the subject to continue; then waits for the next scanner
    trigger if this is in the scanner."""
    text_intro.text = INSTRUCTIONS[setting]
    text_intro.draw()
    win.flip()
    if setting == 'PRACTICE':  # only show instruction if there is a text to show
        key = event.waitKeys(keyList=LOCAL_START_KEY + QUIT_KEYS)[
            0]  # just pick first response, no timestamp
        if key in QUIT_KEYS:
            core.quit()
    # Wait for scanner to start -
    elif setting == 'SCANNER':
        key = event.waitKeys(keyList=SCANNER_TRIGGER_KEY + QUIT_KEYS)[0]  # synchronize with scanner
        if key in QUIT_KEYS:
            core.quit()
    core.wait(0.5)


def run_goodbye(win, fix, thisExp, feedback_duration_sec=5.0):
    # Ensure fixation isn't auto-drawing over feedback
    fix.setAutoDraw(False)

    # Brief fixation flash (to preserve your prior timing feel)
    fix.draw()
    win.flip()
    core.wait(0.2)

    # ---- Build feedback from stored stats ----
    uppercase_total = thisExp.extraInfo.get('uppercase_total', 0)
    uppercase_correct = thisExp.extraInfo.get('uppercase_correct', 0)

    if uppercase_total > 0:
        acc_pct = 100.0 * uppercase_correct / float(uppercase_total)
        feedback_lines = [
            f'UPPERCASE Accuracy: {acc_pct:.1f}%  ({uppercase_correct}/{uppercase_total})'
        ]
    else:
        feedback_lines = [
            'No UPPERCASE trials in this run.'
        ]

    feedback_text = "\n\n".join(feedback_lines)

    # Show feedback (white text is default; background is black)
    feedback_stim = visual.TextStim(
        win,
        text=feedback_text,
        height=0.7,
        pos=(0, 0),
        wrapWidth=20  # helps prevent long lines from clipping off-screen
    )
    feedback_stim.draw()
    win.flip()
    core.wait(feedback_duration_sec)



def list_permutations(lst):
    return list(permutations(lst))
