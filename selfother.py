#%%
# -*- coding: utf-8 -*-
"""
Written by Jonas Kristoffer Lindeløv, lindeloev.net.

TO DO:
 * Control stimulus appearance using variables?
 * Set fullscreen
"""

# Measure this on your monitor
MON_WIDTH = 37  # cm
MON_DISTANCE = 70  # cm
MON_SIZE = [1024, 768]  # x,y pixels

# Presentation parameters
SCAN_TIME = 2.5  # number of seconds
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
KEYS_SUBJECT = {'1': 'yes', '2': 'no'}
KEYS_EXPERIMENTER = ['space']
SCANNER_KEYS = ['=', 'equal']
QUIT_KEYS = ['escape']

conditions = ['SELF', 'OBAMA', 'UPPERCASE']
ORDER_FILES = ['SelfOther-001.csv', 'SelfOther-002.csv']

JUDGEMENT_MAP = {  # mapping from sequence to judgement type (fixed for all)
    'NULL': 'NULL',
    'evt1': 'SELF',
    'evt2': 'UPPERCASE',
    'evt3': 'OBAMA'
}

"""
SET THINGS UP
"""
from psychopy import visual, event, core, gui, monitors, data, logging
import itertools
import math
import random
from datetime import datetime
from pytz import timezone
import pandas as pd
import os

#
expName = 'self_other'
input_subID = 0
# expInfo box
expInfo = {
    'setting': ['SCANNER', 'PRACTICE'],
    'words_file': ['Lists 1-3 run 1.xlsx', 'Lists 1-3 run 2.xlsx', 'Lists 4-6 run 1.xlsx',
                   'Lists 4-6 run 2.xlsx', 'Word Lists 1-3.xlsx', 'Word Lists 4-6.xlsx',
                   'PRACTICE.xlsx']}
expInfo['subID'] = str(input_subID)
expInfo['sessionID'] = ['baseline', 'week1', 'week2', 'week3']
expInfo['runID'] = ['1','2']
expInfo['order_id'] = ['0','1','2','3','4','5']
dlg = gui.DlgFromDict(dictionary=expInfo, title='My Experiment')
                      #order=['subID', 'sessionID', 'runID', 'setting', 'order_id', 'words_file'])
if dlg.OK == False:
    core.quit()

#Initialize the results file
current_dir = os.getcwd()
results_dir = os.path.join(current_dir, 'results')
if not os.path.exists(results_dir):
    os.makedirs(results_dir)
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
logFile = logging.LogFile(resultFile_path+".log", level=logging.EXP)
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
text_judgement = visual.TextStim(win, pos=(0, TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
text_adjective = visual.TextStim(win, pos=(0, -TEXT_DISTANCE), height=TEXT_SIZE, font='Geneva', bold=True)
# Hide the cursor
win.mouseVisible = False
#%%
# Translate order_id into list of condition-event translation
word_column_order = list(itertools.permutations(range(3)))[
    int(expInfo['order_id'])]  # select a permutation of SELF, UPPERCASE, and OBAMA
# Load words
word_lists = pd.read_excel(expInfo['words_file'])
word_lists = {
    'NULL': [''] * 1000,  # make plenty of NULLs at index 0
    'SELF': list(word_lists.iloc[:, word_column_order[0]]),
    'UPPERCASE': list(word_lists.iloc[:, word_column_order[1]]),
    'OBAMA': list(word_lists.iloc[:, word_column_order[2]])
}
clock = core.Clock()

#%%
def make_trials(run_number):
    """ Returns a list of dictionaries, where each dictionary represents a trial """
    # Load sequence for this run number
    sequence_file = ORDER_FILES[run_number - 1]
    sequence = pd.read_csv(sequence_file,na_filter=False, header=None)
    fixation_onsets = sequence.iloc[:,0]
    judgement_types = sequence.iloc[:,4].replace(JUDGEMENT_MAP)  # pick the judgement type column and translate it
    durations_type = (sequence.iloc[:,2] / SCAN_TIME).astype(
        int)  # pick presentation time, convert from seconds (float) to scans (int)
    n_cases = sum(judgement_types == 'UPPERCASE')  # number of UPPERCASE trials
    n_cases_half = int(math.ceil(n_cases / 2.0))  # half that number used to generate...
    cases = ['LOWER'] * n_cases_half + ['UPPER'] * n_cases_half  # list of cases for UPPERCASE trials, half of each.
    random.shuffle(cases)  # random order
    # Loop through the list of trial order, then  fill out remaining info
    trials = []  # list of trials (dictionaries). Will be filled out below and then returned
    for trial_number, judgement_type in enumerate(judgement_types):
        case = cases.pop() if judgement_type == 'UPPERCASE' else 'UPPER'  # default to UPPER. Else pick from the list
        #case = cases[trial_number]
        adjective = word_lists[judgement_type].pop()
        trial = {
            # Trial info
            'judgement': judgement_type,
            #'word_list': judgement_index,
            'adjective': adjective.upper() if case == 'UPPER' else adjective.lower(),
            # takes a word from this list and removes it
            'case': case,
            'durations_type': durations_type[trial_number],
            'fixation_onset': fixation_onsets[trial_number],
            'trial_number': trial_number + 1,  # start at 1 instead of 0
            'run_number': run_number,

            # Placeholders for answers
            'time_start': '',
            'answer': '',
            'rt': '',
        }
        trial.update(expInfo)  # add data from expInfo (general session info)
        trials.append(trial)  # add this trial to the trial list
    return trials

#%%
def run_block(run_number):
    """ Takes a trial list and runs through it, displaying and recording appropriately """
    trials = make_trials(run_number)
    clock.reset()
    df_trials = pd.DataFrame(trials)
    for index, row in df_trials.iterrows():
        trial = row.to_dict()
        thisExp.addData('judgement', trial['judgement'])
        thisExp.addData('adjective', trial['adjective'])
        thisExp.addData('case', trial['case'])
        thisExp.addData('durations_type', trial['durations_type'])
        thisExp.addData('trial_number', trial['trial_number'])
        # Prepare
        text_judgement.text = trial['judgement'] if trial['judgement'] != 'NULL' else ''
        text_adjective.text = trial['adjective']
        current_scan = 0  # number of TRs that this trial has been ongoing
        fixation_onset = trial['fixation_onset']
        # Fixation start
        #fixation_text.draw()
        fix.setAutoDraw(True)
        win.flip()
        s_time = clock.getTime()
        thisExp.addData('fixationStart_onsetTime', clock.getTime())
        core.wait(0.2)
        fix.setAutoDraw(False)
        fix.setAutoDraw(True)
        text_judgement.draw()
        text_adjective.draw()
        win.flip()
        time_start = clock.getTime()
        thisExp.addData('onsetTime', clock.getTime())
        max_duration = SCAN_TIME * trial['durations_type']

        if expInfo['setting'] == 'SCANNER':
            response = event.waitKeys(keyList=list(KEYS_SUBJECT.keys()) + SCANNER_KEYS + QUIT_KEYS, timeStamped=clock,
                                      maxWait=max_duration + SCAN_TIME_BUFFER)
            if response is None:
                key = SCANNER_KEYS[0]
            else:
                key, reaction_time = response[0]
        elif expInfo['setting'] == 'PRACTICE':
            response = event.waitKeys(keyList=list(KEYS_SUBJECT.keys()) + QUIT_KEYS, timeStamped=clock,
                                      maxWait=max_duration)
            if response is None:
                # Timeout, pretend that the scanner sent a trigger
                key = SCANNER_KEYS[0]
            else:
                key, reaction_time = response[0]
        # Record task responses
        if key in KEYS_SUBJECT.keys():
            answer = KEYS_SUBJECT[key]  # translate from key to meaning
            rt = reaction_time - time_start
            thisExp.addData('answer', answer)
            thisExp.addData('reaction_time', reaction_time)
            thisExp.addData('rt', rt)
            # Break out of while-loop if the scanner is beginning the next trigger
        #if key in SCANNER_KEYS:
        #    current_scan += 1  # a scan trigger was recorded
        #    if current_scan >= trial['durations_type']:
        #        break
        if key in QUIT_KEYS:
            core.quit()
        fix.setAutoDraw(True)
        e_time = clock.getTime()
        win.flip()
        core.wait(max_duration - (e_time - s_time) - 0.3)
        fix.setAutoDraw(False)
        # Save trial
        # end of trial - move to next line in data output
        thisExp.nextEntry()
#%%
def show_instruction(text):
    """Waits for the subject to continue; then waits for the next scanner
    trigger if this is in the scanner."""
    if expInfo['setting'] == 'PRACTICE':  # only show instruction if there is a text to show
        text_judgement.text = text
        text_judgement.draw()
        win.flip()
        key = event.waitKeys(keyList=list(KEYS_SUBJECT.keys()) + QUIT_KEYS)[0]  # just pick first response, no timestamp
        if key in QUIT_KEYS:
            core.quit()

    # Wait for scanner to start - 
    elif expInfo['setting'] == 'SCANNER':
        win.flip()  # blank screen
        key = event.waitKeys(keyList=SCANNER_KEYS + QUIT_KEYS)[0]  # synchronize with scanner
        if key in QUIT_KEYS:
            core.quit()
"""
EXECUTE EXPERIMENT
"""
#%%
# Run experiment with break. Start at specified start_run
if int(expInfo['runID']) == 1:
    # Show instructions
    show_instruction(INSTRUCTIONS[expInfo['setting']])  # Translate from setting to instruction text
    run_block(1)
    # Save the experiment data
    thisExp.saveAsWideText(resultFile_path)
    thisExp.saveAsPickle(resultFile_path)
    logging.flush()
    thisExp.abort()  # Ensure the data is saved
    win.close()
    core.quit()
if int(expInfo['runID']) == 2:
    show_instruction(INSTRUCTIONS['break'])
    run_block(2)
    # Save the experiment data
    thisExp.saveAsWideText(resultFile_path)
    thisExp.saveAsPickle(resultFile_path)
    logging.flush()
    thisExp.abort()  # Ensure the data is saved
    win.close()
    core.quit()
# Finished, yay!