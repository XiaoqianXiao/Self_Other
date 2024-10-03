
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
        # for scanner
        if setting == 'SCANNER':
            keys = event.waitKeys(keyList=SCANNER_KEYS,
                                  timeStamped=trialClock,
                                  maxWait=max_duration)
                # Record task responses
        elif setting == 'PRACTICE':
            keys = event.waitKeys(keyList=LOCAL_KEYS,
                                  timeStamped=trialClock,
                                  maxWait=max_duration)
        if keys:
            response, reaction_time = keys[0]
            rt = reaction_time - accurate_onsetTime
        else:
            response = None
            reaction_time = None
            rt = None
        # Record task responses
        if response in QUIT_KEYS:
            resultFile_name = "tmp_" + resultFile_name
            resultFile_path = os.path.join(results_dir, resultFile_name)
            thisExp.saveAsWideText(resultFile_path)
            core.quit()
        thisExp.addData('reaction_time', reaction_time)
        thisExp.addData('rt', rt)
        thisExp.addData('responses', response)
        if response in SUBJECT_KEYS.keys():
            answer = SUBJECT_KEYS[response]  # translate from key to meaning
            thisExp.addData('answer', answer)
        # end of trial - move to next line in data output
        fix.setAutoDraw(True)
        win.flip()
        thisExp.nextEntry()

#%%
def show_instruction(setting, INSTRUCTIONS, text_intro, win,
                     SCANNER_TRIGGER_KEY, LOCAL_RESPONSE_KEYS, QUIT_KEYS):
    """Waits for the subject to continue; then waits for the next scanner
    trigger if this is in the scanner."""
    text_intro.text = INSTRUCTIONS[setting]
    text_intro.draw()
    win.flip()
    if setting == 'PRACTICE':  # only show instruction if there is a text to show
        key = event.waitKeys(keyList=list(LOCAL_RESPONSE_KEYS.keys()) + QUIT_KEYS)[
            0]  # just pick first response, no timestamp
        if key in QUIT_KEYS:
            core.quit()
    # Wait for scanner to start -
    elif setting == 'SCANNER':
        key = event.waitKeys(keyList=SCANNER_TRIGGER_KEY + QUIT_KEYS)[0]  # synchronize with scanner
        start_time = core.getTime()
        if key in QUIT_KEYS:
            core.quit()
    core.wait(0.5)
    return start_time


def run_goodbye(win, fix, start_time):
    while trialClock.getTime() - start_time < 616.5:
    fix.draw()
    win.flip()
    #event.waitKeys()


def list_permutations(lst):
    return list(permutations(lst))
