#%%
# -*- coding: utf-8 -*-
"""
Written by Jonas Kristoffer Lindeløv, lindeloev.net.
 * Control stimulus appearance using variables?
 * Set fullscreen

Modified by Xiaoqian Xiao. 20240916
"""

# Measure this on your monitor
MON_WIDTH = 70  # cm
MON_DISTANCE = 120  # cm
MON_SIZE = [1920, 1080]  # x,y pixels

# Presentation parameters
SCAN_TIME = 1.5  # number of seconds
SCAN_TIME_BUFFER = 0.5  # seconds to wait before concluding that the scanner won't send more triggers
NONRESPONSE_WINDOW = 0.0  # how many seconds to ignore responses in the beginning of a trial

FIXATION_SIZE = 0.5
TEXT_SIZE = 0.7  # height of the letters in degrees visual angle
TEXT_DISTANCE = 0.7  # vertical distance from text to fixation cross in degrees visual angle
INSTRUCTIONS = {
    'break': u'',  # displayed during breaks
    'SCANNER': u'',  # Instructions in scanner. Note that key name should match expInfo['setting']
    'PRACTICE': u"""
IN THE FOLLOWING TASK, YOU WILL BE ASKED TO RATE ONE OF THREE TYPES OF JUDGMENTS FOR DIFFERENT WORDS:

SELF: DOES THIS WORD DESCRIBE YOU?
OBAMA: DOES THIS WORD DESCRIBE FORMER U.S. PRESIDENT BARACK OBAMA?
UPPERCASE: IS THIS WORD PRINTED IN UPPERCASE LETTERS?

FOR EACH ITEM, PLEASE RESPOND WITH YES [1] OR NO [2] ON YOUR RESPONSE BOX. PLEASE KEEP YOUR EYES ON THE CENTRAL FIXATION POINT DURING THE TASK. IF THE NEXT TRIAL COMES UP AND YOU HAVE NOT YET RESPONDED TO THE PREVIOUS TRIAL, THAT'S OKAY, JUST SKIP IT AND MOVE ONTO THE NEXT ONE. 

READY?"""
}

# Keyboard keys
# for scanner
SCANNER_TRIGGER_KEY = ['t']
SCANNER_RESPONSE_KEYS = {'1': 'yes', '2': 'no'}
SCANNER_QUIT_KEYS = ['F9']
# for practice
LOCAL_START_KEY = ['space']
LOCAL_RESPONSE_KEYS = {'f': 'yes', 'j': 'no'}
LOCAL_QUIT_KEYS = ['escape']

SUBJECT_KEYS = {**SCANNER_RESPONSE_KEYS, **LOCAL_RESPONSE_KEYS}
SCANNER_KEYS = SCANNER_TRIGGER_KEY + list(SCANNER_RESPONSE_KEYS.keys()) + SCANNER_QUIT_KEYS
LOCAL_KEYS = LOCAL_START_KEY + list(LOCAL_RESPONSE_KEYS.keys()) + LOCAL_QUIT_KEYS

max_duration = 2

conditions = ['SELF', 'OBAMA', 'UPPERCASE']
ORDER_FILES = ['SelfOther-001.csv', 'SelfOther-002.csv']

JUDGEMENT_MAP = {  # mapping from sequence to judgement type (fixed for all)
    'evt1': 'SELF',
    'evt2': 'UPPERCASE',
    'evt3': 'OBAMA'
}

"""
SET THINGS UP
"""
from psychopy import visual, event, core, gui, monitors, data, logging
import itertools
#%%
import math
import random
from datetime import datetime
from pytz import timezone
import pandas as pd
import os
from tools import *

#%%
expName = 'self_other'
input_subID = 0
# expInfo box
expInfo = {'setting': ['SCANNER', 'PRACTICE'],
           'words_file': ['wordlist_run1.csv', 'wordlist_run2.csv', 'wordlist_prac.csv'],
           'subID': str(input_subID),
           'sessionID': ['baseline', 'week1', 'week2', 'week3'],
           'runID': ['1', '2', 'prac']}
dlg = gui.DlgFromDict(dictionary=expInfo, title='My Experiment')
#order=['subID', 'sessionID', 'runID', 'setting', 'words_file'])
if dlg.OK == False:
    core.quit()

#Initialize the results file
current_dir = os.getcwd()
results_dir = os.path.join(current_dir, 'results')
if not os.path.exists(results_dir):
    os.makedirs(results_dir)
sequence_file = 'sequence_run' + expInfo['runID'] + '.csv'
if not expInfo['runID'] == 'prac':
    runID = expInfo['runID'].zfill(2)
subID = expInfo['subID'].zfill(3)
sessionID = expInfo['sessionID']
experiment_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
resultFile_name = 'sub-' + subID + '_ses-' + sessionID + '_run-' + runID + '_time-' + experiment_time
thisExp = data.ExperimentHandler(
    name=expName, version='0.1',
    extraInfo=expInfo, runtimeInfo=None,
    originPath='',
    savePickle=True, saveWideText=True
)
# Set the logging level to ERROR to suppress warnings
resultFile_path = os.path.join(results_dir, resultFile_name)
logFile = logging.LogFile(resultFile_path + ".log", level=logging.EXP)
logging.console.setLevel(logging.ERROR)
#%%
# Psychopy window
my_monitor = monitors.Monitor('testMonitor', width=MON_WIDTH,
                              distance=MON_DISTANCE)  # Create monitor object from the variables above. This is needed to control size of stimuli in degrees.
#%%
my_monitor.setSizePix(MON_SIZE)
#%%
win = visual.Window(monitor=my_monitor, color=(-1, -1, -1), units='deg', fullscr=True, allowGUI=True)
# Psychopy stimuli/objects
fix = visual.TextStim(win, text='+', height=FIXATION_SIZE, font='Geneva', bold=True)
text_condition = visual.TextStim(win, pos=(0, TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
text_adjective = visual.TextStim(win, pos=(0, -TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
# Hide the cursor
win.mouseVisible = False

#%%
# prepare wordlist
# generate condition transformer
lst = list(range(1, 4))
condition_lists = list_permutations(lst)
# assign condition using the subjectID
condition_category = int(expInfo['subID']) % len(list_permutations(lst))
# for test
#condition_category = int('001') % len(list_permutations(lst))
condition_list = condition_lists[condition_category]
#load words
word_lists = pd.read_csv(expInfo['words_file'])
# for test
#word_lists = pd.read_csv('wordlist_run1.csv')
word_lists.loc[word_lists['condition_design'] == 1, 'condition'] = condition_list[0]
word_lists.loc[word_lists['condition_design'] == 2, 'condition'] = condition_list[1]
word_lists.loc[word_lists['condition_design'] == 3, 'condition'] = condition_list[2]
#%%
word_lists['condition'] = word_lists['condition'].astype(int)
word_lists['condition_name'] = word_lists['condition'].apply(lambda x: conditions[x - 1])
word_lists_shuffled = word_lists.sample(frac=1).reset_index(drop=True)
#%%
# prepare sequence
df_sequence = pd.read_csv(sequence_file)
# for test
#df_sequence = pd.read_csv('sequence_run1.csv')
df_sequence['row_number'] = df_sequence.groupby(['condition', 'valence']).cumcount()
word_lists_shuffled['row_number'] = word_lists_shuffled.groupby(['condition', 'valence']).cumcount()
df_trial = pd.merge(df_sequence, word_lists_shuffled, on=['condition', 'valence', 'row_number'], how='inner')
df_trial = df_trial.sort_values(by='trial_no', ascending=True)
#%%
#not need since judgement_types = condition_name
#df_trial['judgement_types'] = df_trial.loc[:,'condition'].replace(JUDGEMENT_MAP)
n_cases = df_trial[df_trial['condition_name'] == 'UPPERCASE'].shape[0]  # number of UPPERCASE trials
n_cases_half = int(math.ceil(n_cases / 2.0))  # half that number used to generate...
cases = ['LOWER'] * n_cases_half + ['UPPER'] * (
        n_cases - n_cases_half)  # list of cases for UPPERCASE trials, half of each.
random.shuffle(cases)
df_trial['judgement'] = df_trial['condition_name']
df_trial.loc[df_trial['condition_name'] == 'UPPERCASE', 'judgement'] = cases
#%%
df_trial['words_present'] = df_trial['words'].str.lower()
df_trial.loc[df_trial['judgement'] == 'UPPER', 'words_present'] = df_trial['words'].str.upper()
#%%
# Clock for timing
globalClock = core.Clock()
trialClock = core.Clock()

"""
EXECUTE EXPERIMENT
"""
#%%
# Run experiment with break. Start at specified start_run
# Show instructions
setting = expInfo['setting']
show_instruction(setting, INSTRUCTIONS, text_condition, win,
                 SCANNER_RESPONSE_KEYS, SCANNER_QUIT_KEYS, LOCAL_RESPONSE_KEYS, LOCAL_QUIT_KEYS)
run_run(setting, df_trial, max_duration,
        results_dir, resultFile_name,
        thisExp,
        trialClock, win,
        SCANNER_KEYS, SCANNER_QUIT_KEYS, LOCAL_KEYS, LOCAL_QUIT_KEYS, SUBJECT_KEYS,
        text_condition, text_adjective, fix)
run_goodbye(win, fix)
# Save the experiment data
thisExp.saveAsWideText(resultFile_path)
thisExp.saveAsPickle(resultFile_path)
logging.flush()
thisExp.abort()  # Ensure the data is saved
win.close()
core.quit()
# Finished, yay!
